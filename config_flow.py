# Versionshistorik:
# Version: 0.3.16
# Datum: 2025-05-25
# Upphovsman: AI-Assistent
# Ändringar:
# - Ändrat YAML-editorfältet i OptionsFlow till att använda 
#   {"selector": {"code_editor": {"mode": "yaml", "rows": 25}}}
#   som schemadefinition, vilket är ett mer direkt sätt att anropa HA:s kodeditor.
#
# Version: 0.3.15
# Datum: 2025-05-25
# Upphovsman: AI-Assistent
# Ändringar:
# - Justerat hur YAML-editorn definieras i OptionsFlow:
#   - Använder nu en enkel 'default' i vol.Optional-schemat.
#   - Det faktiska filinnehållet skickas som 'suggested_value' via 'description'-attributet
#     till vol.Optional för att förpopulera YAML-editorn.
#   - Schematypen för YAML-editorn är nu korrekt satt till selector-dictionaryn.
#   Detta är ett nytt försök att lösa serialiseringsfel och få en fungerande YAML-editor.
# ... (resten av versionshistoriken) ...

"""Konfigurationsflöde för KNX Dubbelklicksdetektor."""
import logging
import os
from typing import Any, Dict, Optional

import voluptuous as vol
import yaml 
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
# cv.string behövs fortfarande för andra fält
from homeassistant.helpers import config_validation as cv 
from homeassistant.util import slugify
# TextSelector, TextSelectorConfig, TextSelectorType behövs inte om vi använder dictionary-syntaxen

from .const import (
    DOMAIN,
    CONF_NAME_SUFFIX,
    CONF_KNX_GROUP_ADDRESS,
    CONF_KNX_VALUE,
    CONF_DOUBLE_CLICK_WINDOW_SECONDS,
    CONF_ACTIONS_YAML_EDITOR,
    DEFAULT_KNX_VALUE,
    DEFAULT_DOUBLE_CLICK_WINDOW_SECONDS,
    DEFAULT_NAME_SUFFIX,
    ACTIONS_DIR_BASENAME,
    DEFAULT_ACTIONS_FILE_CONTENT,
    ERROR_CANNOT_READ_ACTIONS_FILE,
    ERROR_CANNOT_WRITE_ACTIONS_FILE,
    ERROR_INVALID_ACTIONS_YAML_IN_EDITOR,
)

_LOGGER = logging.getLogger(__name__)


def _generate_actions_filename(config_entry: config_entries.ConfigEntry) -> str:
    name_suffix = config_entry.data.get(CONF_NAME_SUFFIX, DEFAULT_NAME_SUFFIX)
    s_name_suffix = slugify(name_suffix if name_suffix else DEFAULT_NAME_SUFFIX)
    return f"{s_name_suffix}--{config_entry.entry_id}.yaml"


def _get_actions_file_path_for_entry(hass: HomeAssistant, config_entry: config_entries.ConfigEntry) -> str:
    filename = _generate_actions_filename(config_entry)
    return hass.config.path(ACTIONS_DIR_BASENAME, filename)


class KnxDoubleClickConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    # ... (async_step_user är densamma som i v0.3.15) ...
    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        errors: Dict[str, str] = {}
        if user_input is not None:
            name_suffix = user_input.get(CONF_NAME_SUFFIX, DEFAULT_NAME_SUFFIX)
            if not name_suffix.strip():
                name_suffix = DEFAULT_NAME_SUFFIX
            entry_title = f"KNX Dubbelklick: {name_suffix}"
            _LOGGER.info("Förbereder att skapa ny config entry: %s", entry_title)
            data_to_save = {
                CONF_NAME_SUFFIX: name_suffix,
                CONF_KNX_GROUP_ADDRESS: user_input[CONF_KNX_GROUP_ADDRESS],
                CONF_KNX_VALUE: user_input[CONF_KNX_VALUE],
                CONF_DOUBLE_CLICK_WINDOW_SECONDS: user_input[CONF_DOUBLE_CLICK_WINDOW_SECONDS],
            }
            return self.async_create_entry(title=entry_title, data=data_to_save)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME_SUFFIX, default=DEFAULT_NAME_SUFFIX): cv.string,
                vol.Required(CONF_KNX_GROUP_ADDRESS): cv.string,
                vol.Required(
                    CONF_KNX_VALUE, default=DEFAULT_KNX_VALUE
                ): vol.Coerce(int),
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
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return KnxDoubleClickOptionsFlowHandler(config_entry)


class KnxDoubleClickOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry):
        self.config_entry = config_entry

    async def _read_actions_file_content(self, actions_file_path: str) -> str:
        # ... (samma som i v0.3.15) ...
        try:
            if await self.hass.async_add_executor_job(os.path.exists, actions_file_path):
                def read_sync():
                    with open(actions_file_path, "r", encoding="utf-8") as f:
                        return f.read()
                return await self.hass.async_add_executor_job(read_sync)
            else:
                _LOGGER.warning("Åtgärdsfil %s hittades inte, skapar med standardinnehåll.", actions_file_path)
                header_comment = (
                    f"# Åtgärdsfil för KNX Dubbelklicksdetektor instans: '{self.config_entry.title}'\n"
                    f"# Entry ID: {self.config_entry.entry_id}\n"
                    f"# Filnamn: {_generate_actions_filename(self.config_entry)}\n"
                    f"# Sökväg till denna fil: {actions_file_path}\n"
                    "# ---------------------------------------------------------------------------\n\n"
                )
                content = header_comment + DEFAULT_ACTIONS_FILE_CONTENT
                def write_sync():
                    actions_dir_parent_path = self.hass.config.path(ACTIONS_DIR_BASENAME)
                    if not os.path.exists(actions_dir_parent_path):
                        os.makedirs(actions_dir_parent_path, exist_ok=True)
                    with open(actions_file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                await self.hass.async_add_executor_job(write_sync)
                _LOGGER.info("Skapade åtgärdsfil %s med standardinnehåll.", actions_file_path)
                return content
        except Exception as e:
            _LOGGER.error("Kunde inte läsa eller skapa åtgärdsfil %s för Options Flow: %s", actions_file_path, e, exc_info=True)
            return f"# FEL: Kunde inte läsa eller skapa filen {actions_file_path}\n# Orsak: {str(e)}\n# Kontrollera loggarna och filrättigheter.\n\n" + DEFAULT_ACTIONS_FILE_CONTENT

    async def _write_actions_file_content(self, actions_file_path: str, content: str) -> None:
        # ... (samma som i v0.3.15) ...
        def write_sync():
            actions_dir_parent_path = self.hass.config.path(ACTIONS_DIR_BASENAME)
            if not os.path.exists(actions_dir_parent_path):
                os.makedirs(actions_dir_parent_path, exist_ok=True)
            with open(actions_file_path, "w", encoding="utf-8") as f:
                f.write(content)
        await self.hass.async_add_executor_job(write_sync)

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        errors: Dict[str, str] = {}
        actions_file_path = _get_actions_file_path_for_entry(self.hass, self.config_entry)

        if user_input is not None:
            _LOGGER.info("Optionsflöde mottog input för %s", self.config_entry.title)
            
            options_to_save_in_config_entry = {
                CONF_KNX_GROUP_ADDRESS: user_input[CONF_KNX_GROUP_ADDRESS],
                CONF_KNX_VALUE: user_input[CONF_KNX_VALUE],
                CONF_DOUBLE_CLICK_WINDOW_SECONDS: user_input[CONF_DOUBLE_CLICK_WINDOW_SECONDS],
            }

            actions_yaml_from_editor = user_input.get(CONF_ACTIONS_YAML_EDITOR, "")
            try:
                yaml.safe_load(actions_yaml_from_editor) 
            except yaml.YAMLError as e:
                _LOGGER.error("Ogiltig YAML från editor för %s: %s", self.config_entry.title, e)
                errors[CONF_ACTIONS_YAML_EDITOR] = ERROR_INVALID_ACTIONS_YAML_IN_EDITOR
            
            if not errors:
                try:
                    await self._write_actions_file_content(actions_file_path, actions_yaml_from_editor)
                    _LOGGER.info("Åtgärder sparade till filen: %s via OptionsFlow.", actions_file_path)
                    return self.async_create_entry(title="", data=options_to_save_in_config_entry)
                except Exception as e:
                    _LOGGER.error("Kunde inte spara åtgärder till fil %s: %s", actions_file_path, e, exc_info=True)
                    errors["base"] = ERROR_CANNOT_WRITE_ACTIONS_FILE
        
        current_actions_yaml_content_for_editor = await self._read_actions_file_content(actions_file_path)
        if user_input is not None and errors.get(CONF_ACTIONS_YAML_EDITOR):
            current_actions_yaml_content_for_editor = user_input.get(CONF_ACTIONS_YAML_EDITOR, current_actions_yaml_content_for_editor)

        combined_config = {**self.config_entry.data, **self.config_entry.options}
        current_knx_group_address = user_input.get(CONF_KNX_GROUP_ADDRESS, combined_config.get(CONF_KNX_GROUP_ADDRESS, "")) if user_input else combined_config.get(CONF_KNX_GROUP_ADDRESS, "")
        current_knx_value = user_input.get(CONF_KNX_VALUE, combined_config.get(CONF_KNX_VALUE, DEFAULT_KNX_VALUE)) if user_input else combined_config.get(CONF_KNX_VALUE, DEFAULT_KNX_VALUE)
        current_double_click_window = user_input.get(CONF_DOUBLE_CLICK_WINDOW_SECONDS, combined_config.get(CONF_DOUBLE_CLICK_WINDOW_SECONDS, DEFAULT_DOUBLE_CLICK_WINDOW_SECONDS)) if user_input else combined_config.get(CONF_DOUBLE_CLICK_WINDOW_SECONDS, DEFAULT_DOUBLE_CLICK_WINDOW_SECONDS)
        
        options_schema_dict = {
            vol.Required(
                CONF_KNX_GROUP_ADDRESS, default=current_knx_group_address
            ): cv.string,
            vol.Required(
                CONF_KNX_VALUE, default=current_knx_value
            ): vol.Coerce(int),
            vol.Required(
                CONF_DOUBLE_CLICK_WINDOW_SECONDS,
                default=current_double_click_window,
            ): vol.Coerce(float),
            # Använder selector-dictionary direkt som värde för vol.Optional
            vol.Optional(
                CONF_ACTIONS_YAML_EDITOR,
                default=current_actions_yaml_content_for_editor # Standardvärdet för fältet
            ): {"selector": {"code_editor": {"mode": "yaml", "rows": 25}}},
        }
        
        placeholders = {
            "config_entry_name": self.config_entry.title,
            "actions_file_path": f"`{actions_file_path}`" 
        }

        return self.async_show_form(
            step_id="init", 
            data_schema=vol.Schema(options_schema_dict), 
            errors=errors,
            description_placeholders=placeholders
        )