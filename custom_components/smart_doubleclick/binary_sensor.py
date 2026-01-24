# Versionshistorik:
# Version: 1.0.0
# Datum: 2026-01-15
# Upphovsman: Home Assistant Expert
# Ändringar:
# - Bytte till BinarySensorEntity.
# - Ersatte KNX-lyssnare med State-lyssnare.
# - Implementerade CONF_SOURCE_ENTITY och CONF_TRIGGER_VALUE.
# - Lade till Debug-loggning.
# - Uppdaterade namngivning för att matcha användarens val exakt.

"""Sensorplattform för Smart Double Click."""

# pylint: disable=too-many-lines
import datetime
import logging
import os
from typing import Any, Dict, List, Optional

import homeassistant.util.dt as dt_util
import yaml
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Context, Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event, async_call_later
from homeassistant.helpers.script import SCRIPT_MODE_SINGLE, Script
import homeassistant.helpers.config_validation as cv
from homeassistant.util import slugify

from .const import (
    ACTIONS_DIR_BASENAME,
    ATTR_ACTIONS_FILE_PATH,
    ATTR_DOUBLE_CLICK_WINDOW,
    ATTR_TRIGGER_VALUE,
    ATTR_SOURCE_ENTITY,
    ATTR_LAST_CLICK_TIME,
    ATTR_LAST_TIME_DIFFERENCE,
    COMPLEX_ACTION_KEYS,
    CONF_DEBUG_MODE,
    CONF_DOUBLE_CLICK_WINDOW_SECONDS,
    CONF_SOURCE_ENTITY,
    CONF_TRIGGER_VALUE,
    CONF_NAME_SUFFIX,
    DEFAULT_ACTIONS_FILE_CONTENT,
    DEFAULT_DEBUG_MODE,
    DEFAULT_NAME_SUFFIX,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _generate_actions_filename_for_sensor(config_entry: ConfigEntry) -> str:
    name_suffix = config_entry.data.get(CONF_NAME_SUFFIX, DEFAULT_NAME_SUFFIX)
    s_name_suffix = slugify(name_suffix if name_suffix else DEFAULT_NAME_SUFFIX)
    return f"{s_name_suffix}--{config_entry.entry_id}.yaml"


def _get_actions_file_path_for_sensor_instance(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> str:
    filename = _generate_actions_filename_for_sensor(config_entry)
    return hass.config.path(ACTIONS_DIR_BASENAME, filename)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Sätter upp sensorn från config entry."""
    _LOGGER.debug(
        "Sätter upp sensor för config entry: %s (ID: %s)",
        config_entry.title,
        config_entry.entry_id,
    )

    actions_file_path = _get_actions_file_path_for_sensor_instance(hass, config_entry)
    _LOGGER.info(
        "Åtgärdsfil för '%s' kommer att hanteras i: %s.",
        config_entry.title,
        actions_file_path,
    )

    if not await hass.async_add_executor_job(os.path.exists, actions_file_path):
        _LOGGER.info(
            "Åtgärdsfil %s saknas, skapar med standardinnehåll och identifierande header.",
            actions_file_path,
        )
        try:
            header_comment = (
                f"# Åtgärdsfil för Smart Double Click instans: '{config_entry.title}'\n"
                f"# Entry ID: {config_entry.entry_id}\n"
                f"# Filnamn: {_generate_actions_filename_for_sensor(config_entry)}\n"
                f"# Sökväg till denna fil: {actions_file_path}\n"
                "# ---------------------------------------------------------------------------\n\n"
            )
            full_content_for_new_file = header_comment + DEFAULT_ACTIONS_FILE_CONTENT

            def write_default_file_with_header():
                actions_dir_parent_path = hass.config.path(ACTIONS_DIR_BASENAME)
                if not os.path.exists(actions_dir_parent_path):
                    os.makedirs(actions_dir_parent_path, exist_ok=True)
                with open(actions_file_path, "w", encoding="utf-8") as f:
                    f.write(full_content_for_new_file)

            await hass.async_add_executor_job(write_default_file_with_header)
        except Exception as e:  # pylint: disable=broad-exception-caught
            _LOGGER.error(
                "Kunde inte skapa standard åtgärdsfil %s: %s", actions_file_path, e
            )

    name_suffix = config_entry.data.get(CONF_NAME_SUFFIX, DEFAULT_NAME_SUFFIX)
    # Använd exakt namn från config (inget prefix)
    full_sensor_name = name_suffix

    sensor = SmartDoubleClickBinarySensor(hass, config_entry, full_sensor_name)
    async_add_entities([sensor])
    _LOGGER.info("Sensor '%s' tillagd för Smart Double Click.", full_sensor_name)


class SmartDoubleClickBinarySensor(BinarySensorEntity):
    """Representation av en Smart Double Click-sensor."""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, name: str):
        """Initialiserar sensorn."""
        self.hass = hass
        self.config_entry = config_entry
        self._name = name
        self._attr_unique_id = f"{config_entry.entry_id}_binary_sensor"
        self._attr_should_poll = False
        self._attr_is_on = False

        self._last_trigger_time_utc: Optional[datetime.datetime] = None
        self._remove_listener: Optional[callable] = None

        self._source_entity: Optional[str] = None
        self._trigger_value: Optional[str] = None
        self._double_click_window_seconds: Optional[float] = None
        self._debug_mode: bool = DEFAULT_DEBUG_MODE

        self._actions_file_path = _get_actions_file_path_for_sensor_instance(
            hass, config_entry
        )
        self._last_time_difference_seconds: Optional[float] = None

        self._update_instance_variables_from_config()

        _LOGGER.debug(
            "Sensor %s initialiserad. Källa: %s, Triggar på: %s, Fönster: %s s. Åtgärdsfil: %s",
            self._name,
            self._source_entity,
            self._trigger_value,
            self._double_click_window_seconds,
            self._actions_file_path,
        )

    @property
    def name(self) -> str:
        """Returnerar namnet på sensorn."""
        return self._name

    @property
    def is_on(self) -> bool:
        """Returnerar om sensorn är på (momentant)."""
        return self._attr_is_on

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Returnerar extra attribut."""
        attrs = {
            ATTR_SOURCE_ENTITY: self._source_entity,
            ATTR_TRIGGER_VALUE: self._trigger_value,
            ATTR_DOUBLE_CLICK_WINDOW: self._double_click_window_seconds,
            ATTR_ACTIONS_FILE_PATH: self._actions_file_path,
            "debug_mode": self._debug_mode,
        }
        if self._last_trigger_time_utc:
            attrs[ATTR_LAST_CLICK_TIME] = dt_util.as_local(
                self._last_trigger_time_utc
            ).isoformat()

        if self._last_time_difference_seconds is not None:
            attrs[ATTR_LAST_TIME_DIFFERENCE] = round(
                self._last_time_difference_seconds, 3
            )
        return attrs

    @callback
    def _update_instance_variables_from_config(self) -> None:
        """Uppdaterar lokala variabler från config entry."""
        combined_config = {**self.config_entry.data, **self.config_entry.options}

        self._source_entity = combined_config.get(CONF_SOURCE_ENTITY)
        self._trigger_value = combined_config.get(CONF_TRIGGER_VALUE)
        self._double_click_window_seconds = combined_config.get(
            CONF_DOUBLE_CLICK_WINDOW_SECONDS
        )
        self._debug_mode = combined_config.get(CONF_DEBUG_MODE, DEFAULT_DEBUG_MODE)

        name_suffix = self.config_entry.data.get(CONF_NAME_SUFFIX, DEFAULT_NAME_SUFFIX)
        self._name = name_suffix  # Exakt namn

        _LOGGER.debug(
            "Sensor %s instansvariabler uppdaterade från konfiguration.", self.name
        )

    async def _load_parsed_actions_from_file(self) -> Optional[List[Dict[str, Any]]]:
        """Laddar och parsar åtgärder från YAML-filen."""
        # pylint: disable=broad-exception-caught
        # pylint: disable=too-many-return-statements
        actions_yaml_str: Optional[str] = None
        if not await self.hass.async_add_executor_job(
            os.path.exists, self._actions_file_path
        ):
            _LOGGER.warning(
                "Åtgärdsfilen %s för %s hittades inte.",
                self._actions_file_path,
                self.name,
            )
            return None
        try:

            def read_file_content():
                with open(self._actions_file_path, "r", encoding="utf-8") as f:
                    return f.read()

            actions_yaml_str = await self.hass.async_add_executor_job(read_file_content)
        except Exception as e:
            _LOGGER.error(
                "Kunde inte läsa åtgärdsfil %s för %s: %s",
                self._actions_file_path,
                self.name,
                e,
            )
            return None

        if not actions_yaml_str or not actions_yaml_str.strip():
            _LOGGER.info(
                "Åtgärdsfilen %s för %s är tom.", self._actions_file_path, self.name
            )
            return None
        try:
            parsed_actions = yaml.safe_load(actions_yaml_str)
            _LOGGER.debug(
                "Sensor '%s': Parsade åtgärder från fil %s: %s",
                self.name,
                self._actions_file_path,
                parsed_actions,
            )
            if parsed_actions is None or (
                isinstance(parsed_actions, list) and not parsed_actions
            ):
                _LOGGER.info(
                    "Inga åtgärder att utföra från fil %s för %s (tom eller enbart kommentarer).",
                    self._actions_file_path,
                    self.name,
                )
                return None
            if not isinstance(parsed_actions, list):
                _LOGGER.error(
                    "Innehållet i åtgärdsfilen %s för %s är inte en YAML-lista.",
                    self._actions_file_path,
                    self.name,
                )
                return None
            return parsed_actions
        except yaml.YAMLError as e:
            _LOGGER.error(
                "Ogiltig YAML i åtgärdsfil %s för %s: %s",
                self._actions_file_path,
                self.name,
                e,
            )
        return None

    def _compile_script_from_parsed_actions(
        self, parsed_actions: List[Dict[str, Any]]
    ) -> Optional[Script]:
        """Kompilerar åtgärder till ett Script-objekt."""
        if not parsed_actions:
            return None
        try:
            validated_actions = cv.SCRIPT_SCHEMA(parsed_actions)
            script_runner = Script(
                self.hass,
                validated_actions,
                f"{self.name} Dubbelklick Åtgärd (från fil)",
                DOMAIN,
                script_mode=SCRIPT_MODE_SINGLE,
                logger=_LOGGER,
            )
            _LOGGER.debug(
                "Åtgärder kompilerade för %s. Antal åtgärder: %d",
                self.name,
                len(parsed_actions),
            )
            return script_runner
        except Exception as e:  # pylint: disable=broad-exception-caught
            _LOGGER.error(
                "Oväntat fel vid kompilering av skript för %s från parsade åtgärder: %s",
                self.name,
                e,
                exc_info=True,
            )
        return None

    async def async_added_to_hass(self) -> None:
        """När entiteten läggs till i HA."""
        await super().async_added_to_hass()

        self.async_on_remove(
            self.config_entry.add_update_listener(self._async_options_updated)
        )
        self._start_listener()

    async def async_will_remove_from_hass(self) -> None:
        """När entiteten tas bort från HA."""
        self._stop_listener()
        await super().async_will_remove_from_hass()

    @callback
    def _start_listener(self) -> None:
        """Startar lyssnaren för entitetsförändringar."""
        if self._remove_listener:
            self._remove_listener()
            self._remove_listener = None

        if self._source_entity:
            _LOGGER.debug(
                "Sensor %s börjar lyssna på %s, Triggar på: %s",
                self.name,
                self._source_entity,
                self._trigger_value,
            )
            self._remove_listener = async_track_state_change_event(
                self.hass, [self._source_entity], self._async_handle_state_change
            )
        else:
            _LOGGER.warning(
                "Ingen käll-entitet konfigurerad för %s. Kan inte lyssna.", self.name
            )

    @callback
    def _stop_listener(self) -> None:
        """Stoppar lyssnaren."""
        if self._remove_listener:
            self._remove_listener()
            self._remove_listener = None
            _LOGGER.debug("Lyssnare borttagen för %s.", self.name)

    @callback
    async def _async_options_updated(
        self, hass: HomeAssistant, entry: ConfigEntry
    ) -> None:
        """Callback när inställningar uppdateras."""
        # pylint: disable=unused-argument
        _LOGGER.debug(
            "Options uppdaterade för %s sensor, uppdaterar konfiguration och startar om lyssnare.",
            self.name,
        )

        old_source = self._source_entity
        old_trigger = self._trigger_value

        self._update_instance_variables_from_config()

        if old_source != self._source_entity or old_trigger != self._trigger_value:
            _LOGGER.info(
                "Lyssnarparametrar ändrade för %s. Startar om lyssnaren.", self.name
            )
            self._stop_listener()
            self._start_listener()

        self.async_write_ha_state()

    @callback
    async def _async_handle_state_change(self, event: Event) -> None:
        """Hanterar en tillståndsförändring."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        _LOGGER.debug(
            "Sensor '%s': Tillstånd ändrat för %s: %s (önskat: %s)",
            self.name,
            self._source_entity,
            new_state.state,
            self._trigger_value,
        )

        if new_state.state == self._trigger_value:
            await self._handle_trigger(new_state.state)

    async def _handle_trigger(self, trigger_value):
        """Hanterar en trigger-händelse (t.ex. 'on')."""
        current_time_utc = dt_util.utcnow()
        previous_trigger_time_utc = self._last_trigger_time_utc

        self._last_trigger_time_utc = current_time_utc
        self._last_time_difference_seconds = None

        # Debug: Första klicket (eller senare klick om tiden runnit ut)
        if self._debug_mode and (
            previous_trigger_time_utc is None
            or (current_time_utc - previous_trigger_time_utc).total_seconds()
            > self._double_click_window_seconds
        ):
            _LOGGER.info(
                "Klick registrerat för %s. Tid: %s.",
                self.name,
                current_time_utc.isoformat(),
            )

        if previous_trigger_time_utc and self._double_click_window_seconds is not None:
            time_difference_seconds = (
                current_time_utc - previous_trigger_time_utc
            ).total_seconds()
            self._last_time_difference_seconds = time_difference_seconds

            _LOGGER.debug(
                "Tidsdifferens för %s: %.3f sekunder. Fönster: %.3f sekunder.",
                self.name,
                time_difference_seconds,
                self._double_click_window_seconds,
            )

            if time_difference_seconds <= self._double_click_window_seconds:
                if self._debug_mode:
                    _LOGGER.info(
                        "Andra klick registrerat för %s. Tid: %s. Diff: %.3f s. TRIGGER UTLOSTS!",
                        self.name,
                        current_time_utc.isoformat(),
                        time_difference_seconds,
                    )
                else:
                    _LOGGER.info(
                        "Dubbelklick detekterat för %s! Tidsdifferens: %.3f s.",
                        self.name,
                        time_difference_seconds,
                    )

                # Momentan aktivering
                self._attr_is_on = True
                self.async_write_ha_state()

                # Återställ till OFF kort därefter (t.ex. 0.1s eller nästa tick)
                # Vi använder async_call_later för att schemalägga återställningen
                @callback
                def reset_state(_):
                    self._attr_is_on = False
                    self.async_write_ha_state()

                async_call_later(self.hass, 0.2, reset_state)

                parsed_actions_list = await self._load_parsed_actions_from_file()

                if parsed_actions_list:
                    await self._execute_actions(
                        parsed_actions_list,
                        trigger_value,
                        current_time_utc,
                        time_difference_seconds,
                    )
                else:
                    _LOGGER.warning(
                        "Dubbelklick detekterat för %s, men inga åtgärder är konfigurerade i filen %s.",
                        self.name,
                        self._actions_file_path,
                    )

        self.async_write_ha_state()

    async def _execute_actions(
        self,
        parsed_actions_list,
        trigger_value,
        current_time_utc,
        time_difference_seconds,
    ):  # pylint: disable=too-many-nested-blocks
        """Exekverar åtgärderna."""
        _LOGGER.debug(
            "Agerar på %d parsade åtgärder: %s",
            len(parsed_actions_list),
            parsed_actions_list,
        )

        all_actions_are_simple_services = True
        if not parsed_actions_list:
            all_actions_are_simple_services = False
        else:
            for action_dict_check in parsed_actions_list:
                if not (
                    isinstance(action_dict_check, dict)
                    and "service" in action_dict_check
                    and not any(key in action_dict_check for key in COMPLEX_ACTION_KEYS)
                ):
                    all_actions_are_simple_services = False
                    break

        actions_executed_successfully_directly = False

        if all_actions_are_simple_services:
            _LOGGER.info(
                "Alla %d åtgärder är enkla serviceanrop. Försöker köra dem direkt sekventiellt.",
                len(parsed_actions_list),
            )
            actions_executed_successfully_directly = True
            for i, action_dict in enumerate(parsed_actions_list):
                if not await self._execute_single_service_action(
                    i, action_dict, len(parsed_actions_list)
                ):
                    actions_executed_successfully_directly = False
                    break

        if not (
            all_actions_are_simple_services and actions_executed_successfully_directly
        ):
            await self._execute_complex_actions(
                parsed_actions_list,
                all_actions_are_simple_services,
                {
                    "value": trigger_value,
                    "time": current_time_utc,
                    "diff": time_difference_seconds,
                },
            )

    async def _execute_single_service_action(self, index, action_dict, total_actions):
        """Kör ett enkelt serviceanrop."""
        # pylint: disable=broad-exception-caught
        service_call_str = str(action_dict["service"])
        service_data = action_dict.get("data", {}).copy()
        target_data = action_dict.get("target")

        final_target = None
        if target_data:
            if isinstance(target_data, dict):
                final_target = target_data
            elif isinstance(target_data, str):
                final_target = {"entity_id": target_data}

        # Hantera entity_id på toppnivå (legacy)
        if "entity_id" in action_dict:
            if final_target is None:
                final_target = {}
            if "entity_id" not in final_target:
                final_target["entity_id"] = action_dict["entity_id"]

        try:
            domain, service_name = service_call_str.split(".", 1)
            _LOGGER.info(
                "Utför direkt serviceanrop %d/%d för %s: Domän=%s, Tjänst=%s, Data=%s, Target=%s",
                index + 1,
                total_actions,
                self.name,
                domain,
                service_name,
                service_data,
                final_target,
            )
            await self.hass.services.async_call(
                domain,
                service_name,
                service_data,
                blocking=True,
                context=Context(),
                target=final_target,
            )
            return True
        except Exception as e:
            _LOGGER.error(
                "Fel vid direkt serviceanrop %d/%d för %s: %s. Åtgärd: %s",
                index + 1,
                total_actions,
                self.name,
                e,
                action_dict,
                exc_info=True,
            )
            return False

    async def _execute_complex_actions(
        self, parsed_actions_list, all_actions_are_simple_services, context_data
    ):
        """Kör komplexa åtgärder via Script-hjälparen."""
        # pylint: disable=broad-exception-caught
        if not all_actions_are_simple_services:
            _LOGGER.info(
                "Åtgärdslistan innehåller komplexa åtgärder, använder Script-hjälparen för %s.",
                self.name,
            )
        else:
            _LOGGER.warning(
                "Direkta serviceanrop misslyckades för %s, försöker ändå med Script-hjälparen.",
                self.name,
            )

        script_runner = self._compile_script_from_parsed_actions(parsed_actions_list)
        if script_runner:
            script_context = Context()
            name_suffix = self.config_entry.data.get(
                CONF_NAME_SUFFIX, DEFAULT_NAME_SUFFIX
            )
            template_variables = {
                "trigger": {
                    "platform": "smart_doubleclick",
                    "name": name_suffix,
                    "source_entity": self._source_entity,
                    "value": context_data["value"],
                    "event_time_utc": context_data["time"].isoformat(),
                    "event_time_local": dt_util.as_local(
                        context_data["time"]
                    ).isoformat(),
                    "time_difference_seconds": context_data["diff"],
                },
                "config_entry_name": self.config_entry.title,
                "actions_file": self._actions_file_path,
            }
            try:
                await script_runner.async_run(
                    run_variables=template_variables, context=script_context
                )
            except Exception as e:
                _LOGGER.error(
                    "Fel vid körning av Script-hjälparen för %s: %s",
                    self.name,
                    e,
                    exc_info=True,
                )
        else:
            _LOGGER.warning(
                "Kunde inte kompilera skript för %s via Script-hjälparen.", self.name
            )
