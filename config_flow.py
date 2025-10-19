# knx_doubleclick/config_flow.py
# Version: 0.8.15
# Ändringar:
# - Lade till 'config_entry_name' i `description_placeholders` för
#   `async_step_edit_yaml_dialog` för att lösa översättningsfelet.

import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries, core
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    CONF_NAME_SUFFIX,
    CONF_KNX_GROUP_ADDRESS,
    CONF_KNX_VALUE,
    CONF_DOUBLE_CLICK_WINDOW_SECONDS,
    DEFAULT_KNX_VALUE,
    DEFAULT_DOUBLE_CLICK_WINDOW_SECONDS,
    DEFAULT_NAME_SUFFIX,
    ACTIONS_DIR_BASENAME
)

_LOGGER = logging.getLogger(__name__)

def _config_flow_get_actions_file_path(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> str:
    from homeassistant.util import slugify as util_slugify
    name_suffix = entry.data.get(CONF_NAME_SUFFIX, DEFAULT_NAME_SUFFIX)
    s_name_suffix = util_slugify(name_suffix if name_suffix else DEFAULT_NAME_SUFFIX)
    filename = f"{s_name_suffix}--{entry.entry_id}.yaml"
    return hass.config.path(ACTIONS_DIR_BASENAME, filename)

class KnxDoubleClickConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
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
    def __init__(self, config_entry: config_entries.ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> config_entries.FlowResult:
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
        errors: Dict[str, str] = {}
        actions_file_path = _config_flow_get_actions_file_path(self.hass, self.config_entry)
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        current_config = {**self.config_entry.data, **self.config_entry.options}
        options_schema = vol.Schema(
            {
                vol.Required(CONF_KNX_GROUP_ADDRESS, default=current_config.get(CONF_KNX_GROUP_ADDRESS, "")): cv.string,
                vol.Required(CONF_KNX_VALUE, default=current_config.get(CONF_KNX_VALUE, DEFAULT_KNX_VALUE)): vol.Coerce(int),
                vol.Required(
                    CONF_DOUBLE_CLICK_WINDOW_SECONDS, default=current_config.get(CONF_DOUBLE_CLICK_WINDOW_SECONDS, DEFAULT_DOUBLE_CLICK_WINDOW_SECONDS)
                ): vol.Coerce(float),
            }
        )
        placeholders = {
            "config_entry_name": self.config_entry.title or self.config_entry.data.get(CONF_NAME_SUFFIX, "Okänd"),
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
        entry_id = self.config_entry.entry_id
        _LOGGER.info("Visar YAML editor-dialog för entry: %s ('%s')",
                     entry_id, self.config_entry.title)

        panel_html = f'<knx-yaml-editor-panel entryid="{entry_id}"></knx-yaml-editor-panel>'

        # Hämta namnet på config entry för att använda i titeln
        config_entry_name = self.config_entry.title or \
                            self.config_entry.data.get(CONF_NAME_SUFFIX, f"Instans {entry_id[:8]}")


        return self.async_show_form(
            step_id="edit_yaml_dialog",
            data_schema=vol.Schema({}),
            description_placeholders={
                "panel_html_content": panel_html,
                "config_entry_name": config_entry_name # Lade till denna!
            },
            last_step=True
        )