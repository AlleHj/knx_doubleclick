import logging
import os
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries, core
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_NAME_SUFFIX,
    CONF_KNX_GROUP_ADDRESS,
    CONF_KNX_VALUE,
    CONF_DOUBLE_CLICK_WINDOW_SECONDS,
    CONF_YAML_CONTENT,
    DEFAULT_KNX_VALUE,
    DEFAULT_DOUBLE_CLICK_WINDOW_SECONDS,
    DEFAULT_NAME_SUFFIX,
    ACTIONS_DIR_BASENAME,
    ERROR_CANNOT_READ_ACTIONS_FILE,
    ERROR_CANNOT_WRITE_ACTIONS_FILE
)

_LOGGER = logging.getLogger(__name__)

def _config_flow_get_actions_file_path(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> str:
    """Hjälpfunktion för att bygga sökväg till åtgärdsfilen."""
    from homeassistant.util import slugify as util_slugify
    name_suffix = entry.data.get(CONF_NAME_SUFFIX, DEFAULT_NAME_SUFFIX)
    s_name_suffix = util_slugify(name_suffix if name_suffix else DEFAULT_NAME_SUFFIX)
    filename = f"{s_name_suffix}--{entry.entry_id}.yaml"
    return hass.config.path(ACTIONS_DIR_BASENAME, filename)

class KnxDoubleClickConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Hanterar den initiala konfigurationen."""
    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> config_entries.FlowResult:
        errors: Dict[str, str] = {}

        if user_input is not None:
            name_suffix = user_input.get(CONF_NAME_SUFFIX, "").strip()
            if not name_suffix:
                name_suffix = DEFAULT_NAME_SUFFIX

            current_entries = self._async_current_entries(include_ignore=False)
            if any(entry.data.get(CONF_NAME_SUFFIX) == name_suffix for entry in current_entries):
                errors["base"] = "name_suffix_already_configured"

            if not errors:
                data_to_save = {
                    CONF_NAME_SUFFIX: name_suffix,
                    CONF_KNX_GROUP_ADDRESS: user_input[CONF_KNX_GROUP_ADDRESS],
                    CONF_KNX_VALUE: user_input[CONF_KNX_VALUE],
                    CONF_DOUBLE_CLICK_WINDOW_SECONDS: user_input[CONF_DOUBLE_CLICK_WINDOW_SECONDS],
                }
                entry_title = f"KNX Dubbelklick: {name_suffix}"
                return self.async_create_entry(title=entry_title, data=data_to_save)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME_SUFFIX, default=DEFAULT_NAME_SUFFIX): cv.string,
                vol.Required(CONF_KNX_GROUP_ADDRESS): cv.string,
                vol.Required(CONF_KNX_VALUE, default=DEFAULT_KNX_VALUE): vol.Coerce(int),
                vol.Required(
                    CONF_DOUBLE_CLICK_WINDOW_SECONDS,
                    default=DEFAULT_DOUBLE_CLICK_WINDOW_SECONDS,
                ): vol.Coerce(float),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> "KnxDoubleClickOptionsFlowHandler":
        return KnxDoubleClickOptionsFlowHandler(config_entry)


class KnxDoubleClickOptionsFlowHandler(config_entries.OptionsFlow):
    """Hanterar ändringar av inställningar (kugghjulet)."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        pass

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> config_entries.FlowResult:
        """Visar menyn."""
        return self.async_show_menu(
            step_id="init",
            menu_options={
                "basic_options": "Grundläggande Inställningar",
                "edit_yaml_dialog": "Redigera YAML Åtgärder"
            }
        )

    async def async_step_basic_options(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> config_entries.FlowResult:
        """Redigera parametrar."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_config = {**self.config_entry.data, **self.config_entry.options}
        current_ga = current_config.get(CONF_KNX_GROUP_ADDRESS, "")
        current_val = current_config.get(CONF_KNX_VALUE, DEFAULT_KNX_VALUE)
        current_win = current_config.get(CONF_DOUBLE_CLICK_WINDOW_SECONDS, DEFAULT_DOUBLE_CLICK_WINDOW_SECONDS)

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_KNX_GROUP_ADDRESS,
                    default=current_ga
                ): cv.string,
                vol.Required(
                    CONF_KNX_VALUE,
                    default=int(current_val)
                ): vol.Coerce(int),
                vol.Required(
                    CONF_DOUBLE_CLICK_WINDOW_SECONDS,
                    default=float(current_win)
                ): vol.Coerce(float),
            }
        )

        actions_file_path = _config_flow_get_actions_file_path(self.hass, self.config_entry)
        config_entry_name = self.config_entry.title or self.config_entry.data.get(CONF_NAME_SUFFIX, "Okänd")

        placeholders = {
            "config_entry_name": config_entry_name,
            "actions_file_path": actions_file_path
        }

        return self.async_show_form(
            step_id="basic_options",
            data_schema=options_schema,
            errors=errors,
            description_placeholders=placeholders,
            last_step=True
        )

    async def async_step_edit_yaml_dialog(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> config_entries.FlowResult:
        """
        Redigerar YAML-filen direkt med en native TextSelector (YAML-mode).
        Ingen JavaScript eller frontend-komponent behövs längre.
        """
        errors = {}
        file_path = _config_flow_get_actions_file_path(self.hass, self.config_entry)

        # 1. Om användaren trycker på Spara (Submit)
        if user_input is not None:
            new_content = user_input.get(CONF_YAML_CONTENT, "")
            try:
                # Skriv till fil i executor för att inte blockera main loop
                def write_file():
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)

                await self.hass.async_add_executor_job(write_file)

                # Återvänd till create_entry med nuvarande options för att stänga flödet
                # Vi ändrar inte själva options i config entryn, bara filen på disken.
                return self.async_create_entry(title="", data=self.config_entry.options)

            except Exception as e:
                _LOGGER.error("Kunde inte spara fil %s: %s", file_path, e)
                errors["base"] = ERROR_CANNOT_WRITE_ACTIONS_FILE
                # Om det blir fel vill vi visa formuläret igen, med det innehåll användaren försökte spara
                file_content = new_content

        # 2. Om vi laddar steget första gången (eller vid fel), läs filinnehåll
        if user_input is None:
            try:
                def read_file():
                    if os.path.exists(file_path):
                        with open(file_path, "r", encoding="utf-8") as f:
                            return f.read()
                    return "" # Tom fil om den inte finns

                file_content = await self.hass.async_add_executor_job(read_file)

            except Exception as e:
                _LOGGER.error("Kunde inte läsa fil %s: %s", file_path, e)
                errors["base"] = ERROR_CANNOT_READ_ACTIONS_FILE
                file_content = "# FEL: Kunde inte läsa filen."

        # 3. Skapa schemat med native YAML editor
        schema = vol.Schema({
            vol.Required(CONF_YAML_CONTENT, default=file_content): selector.TextSelector(
                selector.TextSelectorConfig(
                    multiline=True,
                    language="yaml",
                    autocomplete="yaml"
                )
            )
        })

        config_entry_name = self.config_entry.title or \
                            self.config_entry.data.get(CONF_NAME_SUFFIX, f"Instans {self.config_entry.entry_id[:8]}")

        return self.async_show_form(
            step_id="edit_yaml_dialog",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "config_entry_name": config_entry_name,
                "file_path": file_path
            },
            last_step=True
        )