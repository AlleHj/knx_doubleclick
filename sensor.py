# Versionshistorik:
# Version: 0.3.16
# Datum: 2025-05-25
# Upphovsman: AI-Assistent
# Ändringar:
# - Inga funktionella ändringar i denna fil. config_flow.py har justerats för att
#   använda {"selector": {"code_editor": {"mode": "yaml"}}} för YAML-fältet.
#
# Version: 0.3.15
# Datum: 2025-05-25
# Upphovsman: AI-Assistent
# Ändringar:
# - Inga funktionella ändringar i denna fil. config_flow.py har justerats
#   för att korrekt använda 'suggested_value' för YAML-editorn i OptionsFlow.

"""Sensorplattform för KNX Dubbelklicksdetektor."""
import logging
import os
from typing import Any, Dict, Optional, List
import datetime

import yaml
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback, Event, Context
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.script import Script, SCRIPT_MODE_SINGLE
from homeassistant.util import slugify

import homeassistant.util.dt as dt_util

from .const import (
    DOMAIN,
    CONF_NAME_SUFFIX,
    CONF_KNX_GROUP_ADDRESS,
    CONF_KNX_VALUE,
    CONF_DOUBLE_CLICK_WINDOW_SECONDS,
    ATTR_LAST_CLICK_TIME,
    ATTR_KNX_GROUP_ADDRESS,
    ATTR_KNX_LISTEN_VALUE,
    ATTR_DOUBLE_CLICK_WINDOW,
    ATTR_ACTIONS_FILE_PATH,
    ATTR_LAST_TIME_DIFFERENCE,
    ACTIONS_DIR_BASENAME,
    DEFAULT_ACTIONS_FILE_CONTENT,
    DEFAULT_NAME_SUFFIX,
    COMPLEX_ACTION_KEYS,
)

_LOGGER = logging.getLogger(__name__)


def _generate_actions_filename_for_sensor(config_entry: ConfigEntry) -> str:
    name_suffix = config_entry.data.get(CONF_NAME_SUFFIX, DEFAULT_NAME_SUFFIX)
    s_name_suffix = slugify(name_suffix if name_suffix else DEFAULT_NAME_SUFFIX)
    return f"{s_name_suffix}--{config_entry.entry_id}.yaml"


def _get_actions_file_path_for_sensor_instance(hass: HomeAssistant, config_entry: ConfigEntry) -> str:
    filename = _generate_actions_filename_for_sensor(config_entry)
    return hass.config.path(ACTIONS_DIR_BASENAME, filename)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    # ... (samma som i v0.3.8) ...
    _LOGGER.debug("Sätter upp sensor för config entry: %s (ID: %s)", config_entry.title, config_entry.entry_id)
    
    actions_file_path = _get_actions_file_path_for_sensor_instance(hass, config_entry)
    _LOGGER.info(
        "Åtgärdsfil för '%s' kommer att hanteras i: %s.",
        config_entry.title,
        actions_file_path
    )

    if not await hass.async_add_executor_job(os.path.exists, actions_file_path):
        _LOGGER.info("Åtgärdsfil %s saknas, skapar med standardinnehåll och identifierande header.", actions_file_path)
        try:
            header_comment = (
                f"# Åtgärdsfil för KNX Dubbelklicksdetektor instans: '{config_entry.title}'\n"
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
        except Exception as e:
            _LOGGER.error("Kunde inte skapa standard åtgärdsfil %s: %s", actions_file_path, e)

    name_suffix = config_entry.data.get(CONF_NAME_SUFFIX, DEFAULT_NAME_SUFFIX)
    full_sensor_name = f"KNX Dubbelklick Lyssnare {name_suffix}"
    
    sensor = KnxDoubleClickSensor(hass, config_entry, full_sensor_name)
    async_add_entities([sensor])
    _LOGGER.info("Sensor '%s' tillagd för KNX Dubbelklicksdetektor.", full_sensor_name)


class KnxDoubleClickSensor(SensorEntity):
    """Representation av en KNX Dubbelklicksdetektor-sensor."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, name: str):
        # ... (samma som i v0.3.8) ...
        self.hass = hass
        self.config_entry = config_entry
        self._name = name
        self._attr_unique_id = f"{config_entry.entry_id}_sensor"
        self._attr_should_poll = False

        self._last_valid_knx_event_time_utc: Optional[datetime.datetime] = None
        self._native_value: Optional[datetime.datetime] = None
        self._remove_listener: Optional[callable] = None
        
        self._knx_group_address: Optional[str] = None
        self._knx_value: Optional[int] = None
        self._double_click_window_seconds: Optional[float] = None
        
        self._actions_file_path = _get_actions_file_path_for_sensor_instance(hass, config_entry)
        self._last_time_difference_seconds: Optional[float] = None

        self._update_instance_variables_from_config()

        _LOGGER.debug(
            "Sensor %s initialiserad. Lyssnar på GA: %s, Värde: %s, Fönster: %s s. Åtgärdsfil: %s",
            self._name,
            self._knx_group_address,
            self._knx_value,
            self._double_click_window_seconds,
            self._actions_file_path,
        )


    @property
    def name(self) -> str:
        return self._name

    @property
    def native_value(self) -> Optional[datetime.datetime]:
        return self._native_value

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        # ... (samma som i v0.3.8) ...
        attrs = {
            ATTR_KNX_GROUP_ADDRESS: self._knx_group_address,
            ATTR_KNX_LISTEN_VALUE: self._knx_value,
            ATTR_DOUBLE_CLICK_WINDOW: self._double_click_window_seconds,
            ATTR_ACTIONS_FILE_PATH: self._actions_file_path,
        }
        if self._native_value:
            attrs[ATTR_LAST_CLICK_TIME] = dt_util.as_local(self._native_value).isoformat()
        
        if self._last_time_difference_seconds is not None:
            attrs[ATTR_LAST_TIME_DIFFERENCE] = round(self._last_time_difference_seconds, 3)
        return attrs

    @callback
    def _update_instance_variables_from_config(self) -> None:
        # ... (samma som i v0.3.8) ...
        combined_config = {**self.config_entry.data, **self.config_entry.options}

        self._knx_group_address = combined_config.get(CONF_KNX_GROUP_ADDRESS)
        self._knx_value = combined_config.get(CONF_KNX_VALUE) 
        self._double_click_window_seconds = combined_config.get(CONF_DOUBLE_CLICK_WINDOW_SECONDS)
        
        name_suffix = self.config_entry.data.get(CONF_NAME_SUFFIX, DEFAULT_NAME_SUFFIX)
        self._name = f"KNX Dubbelklick Lyssnare {name_suffix}"

        _LOGGER.debug("Sensor %s instansvariabler uppdaterade från konfiguration.", self.name)

    async def _load_parsed_actions_from_file(self) -> Optional[List[Dict[str, Any]]]:
        # ... (samma som i v0.3.8) ...
        actions_yaml_str: Optional[str] = None
        if not await self.hass.async_add_executor_job(os.path.exists, self._actions_file_path):
            _LOGGER.warning("Åtgärdsfilen %s för %s hittades inte.", self._actions_file_path, self.name)
            return None
        try:
            def read_file_content():
                with open(self._actions_file_path, "r", encoding="utf-8") as f:
                    return f.read()
            actions_yaml_str = await self.hass.async_add_executor_job(read_file_content)
        except Exception as e:
            _LOGGER.error("Kunde inte läsa åtgärdsfil %s för %s: %s", self._actions_file_path, self.name, e)
            return None

        if not actions_yaml_str or not actions_yaml_str.strip():
            _LOGGER.info("Åtgärdsfilen %s för %s är tom.", self._actions_file_path, self.name)
            return None
        try:
            parsed_actions = yaml.safe_load(actions_yaml_str)
            _LOGGER.debug("Sensor '%s': Parsade åtgärder från fil %s: %s", self.name, self._actions_file_path, parsed_actions)
            if parsed_actions is None or (isinstance(parsed_actions, list) and not parsed_actions):
                _LOGGER.info("Inga åtgärder att utföra från fil %s (tom eller enbart kommentarer).", self._actions_file_path, self.name)
                return None
            if not isinstance(parsed_actions, list):
                _LOGGER.error("Innehållet i åtgärdsfilen %s för %s är inte en YAML-lista.", self._actions_file_path, self.name)
                return None
            return parsed_actions
        except yaml.YAMLError as e:
            _LOGGER.error("Ogiltig YAML i åtgärdsfil %s för %s: %s", self._actions_file_path, self.name, e)
        return None

    def _compile_script_from_parsed_actions(self, parsed_actions: List[Dict[str, Any]]) -> Optional[Script]:
        # ... (samma som i v0.3.8) ...
        if not parsed_actions:
            return None
        try:
            script_runner = Script(
                self.hass,
                parsed_actions,
                f"{self.name} Dubbelklick Åtgärd (från fil)",
                DOMAIN,
                script_mode=SCRIPT_MODE_SINGLE, 
                logger=_LOGGER,
            )
            _LOGGER.debug("Åtgärder kompilerade för %s. Antal åtgärder: %d", self.name, len(parsed_actions))
            return script_runner
        except Exception as e:
            _LOGGER.error("Oväntat fel vid kompilering av skript för %s från parsade åtgärder: %s", self.name, e, exc_info=True)
        return None

    async def async_added_to_hass(self) -> None:
        # ... (samma som i v0.3.8) ...
        await super().async_added_to_hass()
        
        self.async_on_remove(
            self.config_entry.add_update_listener(self._async_options_updated)
        )
        self._start_knx_listener()

    async def async_will_remove_from_hass(self) -> None:
        # ... (samma som i v0.3.8) ...
        self._stop_knx_listener()
        await super().async_will_remove_from_hass()

    @callback
    def _start_knx_listener(self) -> None:
        # ... (samma som i v0.3.8) ...
        if self._remove_listener:
            self._remove_listener()
            self._remove_listener = None

        if self._knx_group_address:
            _LOGGER.debug("Sensor %s börjar lyssna på KNX-event för GA: %s, Värde: %s", 
                          self.name, self._knx_group_address, self._knx_value)
            self._remove_listener = self.hass.bus.async_listen(
                "knx_event", self._async_handle_knx_event
            )
        else:
            _LOGGER.warning("Ingen KNX gruppadress konfigurerad för %s. Kan inte lyssna på event.", self.name)

    @callback
    def _stop_knx_listener(self) -> None:
        # ... (samma som i v0.3.8) ...
        if self._remove_listener:
            self._remove_listener()
            self._remove_listener = None
            _LOGGER.debug("KNX-lyssnare borttagen för %s.", self.name)

    @callback
    async def _async_options_updated(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        # ... (samma som i v0.3.8) ...
        _LOGGER.debug("Options uppdaterade för %s sensor, uppdaterar konfiguration och startar om lyssnare.", self.name)
        
        old_ga = self._knx_group_address
        old_val = self._knx_value

        self._update_instance_variables_from_config()
        
        if old_ga != self._knx_group_address or old_val != self._knx_value:
            _LOGGER.info("KNX lyssnarparametrar ändrade för %s. Startar om lyssnaren.", self.name)
            self._stop_knx_listener()
            self._start_knx_listener()
            
        self.async_write_ha_state()

    @callback
    async def _async_handle_knx_event(self, event: Event) -> None:
        """Hanterar ett KNX-event från eventbussen."""
        # ... (loggning och värdehantering är densamma som i v0.3.8) ...
        _LOGGER.debug(
            "Sensor '%s' mottog ett KNX-event på bussen. Event data: %s. "
            "Konfigurerad för GA: '%s', Värde: '%s'",
            self.name,
            event.data,
            self._knx_group_address,
            self._knx_value
        )

        destination_address = event.data.get("destination")
        
        value_from_event_value_field = event.data.get("value")
        actual_value_from_event = value_from_event_value_field

        if actual_value_from_event is None:
            value_from_event_data_field = event.data.get("data")
            _LOGGER.debug(
                "Sensor '%s': 'event.data.value' var None. Faller tillbaka till 'event.data.data' (%r, typ: %s).",
                self.name,
                value_from_event_data_field,
                type(value_from_event_data_field)
            )
            actual_value_from_event = value_from_event_data_field
        
        if actual_value_from_event is None:
            _LOGGER.debug(
                "Sensor '%s': Varken 'event.data.value' eller 'event.data.data' innehöll ett användbart värde. Ignorerar event.",
                self.name
            )
            return

        _LOGGER.debug(
            "Sensor '%s' jämför: Mottagen Dest: %r (ska vara %r), Faktiskt Värde från Event: %r (typ: %s) (ska vara %r typ: %s)",
            self.name,
            destination_address, self._knx_group_address,
            actual_value_from_event, type(actual_value_from_event),
            self._knx_value, type(self._knx_value)
        )
        
        comparable_value = None
        try:
            if isinstance(actual_value_from_event, list) and len(actual_value_from_event) == 1:
                comparable_value = int(actual_value_from_event[0])
            else:
                comparable_value = int(actual_value_from_event)
        except (ValueError, TypeError) as e:
            _LOGGER.debug(
                "Sensor '%s': Kunde inte konvertera mottaget värde %r (typ: %s) till heltal för jämförelse: %s. Ignorerar.",
                self.name,
                actual_value_from_event,
                type(actual_value_from_event),
                e
            )
            return

        if (
            destination_address == self._knx_group_address
            and comparable_value == self._knx_value 
        ):
            _LOGGER.info(
                "MATCH! KNX-event för '%s': GA '%s', Värde '%s' (jämfört som %s). Bearbetar dubbelklicklogik...",
                self.name,
                destination_address,
                actual_value_from_event, 
                comparable_value
            )
            current_time_utc = dt_util.utcnow()
            previous_event_time_utc = self._last_valid_knx_event_time_utc

            self._native_value = current_time_utc 
            self._last_valid_knx_event_time_utc = current_time_utc
            self._last_time_difference_seconds = None 

            if previous_event_time_utc and self._double_click_window_seconds is not None:
                time_difference_seconds = (
                    current_time_utc - previous_event_time_utc
                ).total_seconds()
                self._last_time_difference_seconds = time_difference_seconds

                _LOGGER.debug(
                    "Tidsdifferens för %s: %.3f sekunder. Fönster: %.3f sekunder.",
                    self.name,
                    time_difference_seconds,
                    self._double_click_window_seconds,
                )

                if time_difference_seconds <= self._double_click_window_seconds:
                    _LOGGER.info(
                        "Dubbelklick detekterat för %s! Tidsdifferens: %.3f s.",
                        self.name,
                        time_difference_seconds,
                    )
                    
                    parsed_actions_list = await self._load_parsed_actions_from_file()

                    if parsed_actions_list:
                        _LOGGER.debug("Agerar på %d parsade åtgärder: %s", len(parsed_actions_list), parsed_actions_list)
                        
                        # ---- Start: Logik för att köra åtgärder med korrigerad indentering ----
                        all_actions_are_simple_services = True
                        if not parsed_actions_list:
                            all_actions_are_simple_services = False
                        else:
                            for action_dict_check in parsed_actions_list:
                                if not (isinstance(action_dict_check, dict) and \
                                        "service" in action_dict_check and \
                                        not any(key in action_dict_check for key in COMPLEX_ACTION_KEYS)):
                                    all_actions_are_simple_services = False
                                    break
                        
                        actions_executed_successfully_directly = False 
                        
                        if all_actions_are_simple_services:
                            _LOGGER.info("Alla %d åtgärder är enkla serviceanrop. Försöker köra dem direkt sekventiellt.", len(parsed_actions_list))
                            actions_executed_successfully_directly = True 
                            for i, action_dict in enumerate(parsed_actions_list):
                                service_call_str = str(action_dict["service"])
                                service_data = action_dict.get("data", {}).copy()
                                target_data = action_dict.get("target", {})

                                if isinstance(target_data, dict):
                                    service_data.update(target_data)
                                elif isinstance(target_data, str) and "entity_id" not in service_data :
                                     service_data["entity_id"] = target_data
                                
                                if "entity_id" in action_dict and "entity_id" not in service_data:
                                    service_data["entity_id"] = action_dict["entity_id"]
                                
                                try:
                                    domain, service_name = service_call_str.split(".", 1)
                                    _LOGGER.info(
                                        "Utför direkt serviceanrop %d/%d för %s: Domän=%s, Tjänst=%s, Data=%s",
                                        i + 1, len(parsed_actions_list), self.name, domain, service_name, service_data
                                    )
                                    await self.hass.services.async_call(
                                        domain, service_name, service_data,
                                        blocking=True, context=Context()
                                    )
                                    _LOGGER.info("Direkt serviceanrop %d/%d för %s lyckades.", i + 1, len(parsed_actions_list), self.name)
                                except ValueError as e: # Korrekt indentering av hela try-except blocket
                                    _LOGGER.error(
                                        "Fel vid parsning av service för direktanrop %d/%d ('%s') för %s: %s. Åtgärd: %s", 
                                        i + 1, len(parsed_actions_list), service_call_str, self.name, e, action_dict, exc_info=True
                                    )
                                    actions_executed_successfully_directly = False 
                                    break 
                                except Exception as e:
                                    _LOGGER.error(
                                        "Fel vid direkt serviceanrop %d/%d för %s: %s. Åtgärd: %s", 
                                        i + 1, len(parsed_actions_list), self.name, e, action_dict, exc_info=True
                                    )
                                    actions_executed_successfully_directly = False
                                    break
                            # Slut på for-loopen
                            if actions_executed_successfully_directly and parsed_actions_list:
                                _LOGGER.info("Alla (%d) enkla serviceanrop har körts direkt för %s.", len(parsed_actions_list), self.name)
                            elif not actions_executed_successfully_directly and parsed_actions_list :
                                _LOGGER.error("Minst ett direkt serviceanrop misslyckades för %s. Inte alla åtgärder kördes.", self.name)
                        # Slut på if all_actions_are_simple_services
                        
                        # Kör Script-hjälparen om det INTE var enbart enkla anrop som alla lyckades, ELLER om listan var tom från början men ändå ska testas med Script.
                        # Mer korrekt: Kör Script om INTE (alla var enkla OCH alla lyckades direkt).
                        # Detta täcker: komplexa åtgärder, eller om direkta anrop misslyckades (för att få HA Cores felmeddelande).
                        if not (all_actions_are_simple_services and actions_executed_successfully_directly and parsed_actions_list) and parsed_actions_list:
                            if not all_actions_are_simple_services:
                                _LOGGER.info("Åtgärdslistan innehåller komplexa åtgärder, använder Script-hjälparen för %s.", self.name)
                            else: # Betyder all_simple var true, men actions_executed_successfully_directly var false
                                _LOGGER.warning("Direkta serviceanrop misslyckades för %s, försöker ändå med Script-hjälparen för att logga eventuellt HA Core-fel.", self.name)
                            
                            script_runner = self._compile_script_from_parsed_actions(parsed_actions_list)
                            if script_runner:
                                script_context = Context()
                                name_suffix = self.config_entry.data.get(CONF_NAME_SUFFIX, DEFAULT_NAME_SUFFIX)
                                template_variables = {
                                    "trigger": {
                                        "platform": "knx_doubleclick",
                                        "group_address": self._knx_group_address,
                                        "value": comparable_value,
                                        "event_time_utc": current_time_utc.isoformat(),
                                        "event_time_local": dt_util.as_local(current_time_utc).isoformat(),
                                        "time_difference_seconds": time_difference_seconds,
                                        "name_suffix": name_suffix
                                    },
                                    "config_entry_name": self.config_entry.title,
                                    "actions_file": self._actions_file_path
                                }
                                _LOGGER.debug("Kör skript via Script-hjälparen med variabler: %s", template_variables)
                                try:
                                    await script_runner.async_run(
                                        run_variables=template_variables,
                                        context=script_context
                                    )
                                except Exception as e:
                                    _LOGGER.error("Fel vid körning av Script-hjälparen för %s: %s", self.name, e, exc_info=True)
                            else:
                                 _LOGGER.warning("Kunde inte kompilera skript för %s via Script-hjälparen (parsed_actions: %s).", self.name, parsed_actions_list)
                    else: # parsed_actions_list var None eller tom
                        _LOGGER.warning(
                            "Dubbelklick detekterat för %s, men inga åtgärder är konfigurerade i filen %s eller så kunde filen/skriptet inte laddas/kompileras.",
                            self.name, self._actions_file_path
                        )
            
            self.async_write_ha_state()
        else: # Om inte GA och värde matchar
            if destination_address == self._knx_group_address:
                _LOGGER.debug(
                    "Sensor '%s': GA '%s' matchade, men värdet gjorde det inte. Jämförbart Värde från Event: %r (typ: %s), Förväntat Värde: %r (typ: %s). Ignorerar.",
                    self.name,
                    destination_address,
                    comparable_value if comparable_value is not None else actual_value_from_event,
                    type(comparable_value if comparable_value is not None else actual_value_from_event),
                    self._knx_value, type(self._knx_value)
                )