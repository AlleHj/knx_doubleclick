# knx_doubleclick/config_flow.py
# Version: 0.8.20
# Datum: 2026-01-15
# Ändringar:
# - Tog bort menyn i async_step_init.
# - Options-flödet går nu direkt till "Grundläggande inställningar".
# - Tog bort steget edit_yaml_dialog helt.

import logging
import os
from typing import Any, Dict, Optional

import voluptuous as vol
import yaml
from homeassistant import config_entries, core
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import (
    TemplateSelector,
)

from .const import (
    ACTIONS_DIR_BASENAME,
    CONF_DOUBLE_CLICK_WINDOW_SECONDS,
    CONF_KNX_GROUP_ADDRESS,
    CONF_KNX_VALUE,
    CONF_NAME_SUFFIX,
    CONF_YAML_CONTENT,
    DEFAULT_DOUBLE_CLICK_WINDOW_SECONDS,
    DEFAULT_KNX_VALUE,
    DEFAULT_NAME_SUFFIX,
    DOMAIN,
    ERROR_CANNOT_READ_ACTIONS_FILE,
    ERROR_CANNOT_WRITE_ACTIONS_FILE,
    ERROR_INVALID_YAML,
)

_LOGGER = logging.getLogger(__name__)

def _config_flow_get_actions_file_path(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> str:
    """Hjälpfunktion för att bygga sökväg till åtgärdsfilen."""
    # pylint: disable=import-outside-toplevel
    from homeassistant.util import slugify as util_slugify
    name_suffix = entry.data.get(CONF_NAME_SUFFIX, DEFAULT_NAME_SUFFIX)
    s_name_suffix = util_slugify(name_suffix if name_suffix else DEFAULT_NAME_SUFFIX)
    filename = f"{s_name_suffix}--{entry.entry_id}.yaml"
    return hass.config.path(ACTIONS_DIR_BASENAME, filename)

class KnxDoubleClickConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Hanterar den initiala konfigurationen."""
    # pylint: disable=abstract-method
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> "KnxDoubleClickOptionsFlowHandler":
        """Skapar options flow-hanteraren."""
        return KnxDoubleClickOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> config_entries.FlowResult:
        errors: Dict[str, str] = {}

        if user_input is not None:
            name_suffix = user_input.get(CONF_NAME_SUFFIX, "").strip()
            if not name_suffix:
                name_suffix = DEFAULT_NAME_SUFFIX

            # Kontrollera dubbletter
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



class KnxDoubleClickOptionsFlowHandler(config_entries.OptionsFlow):
    """Hanterar ändringar av inställningar (kugghjulet)."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        pass

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> config_entries.FlowResult:
        """
        Startsteget för options.
        Visar en meny där användaren kan välja mellan inställningar eller YAML-editor.
        """
        # user_input används inte här eftersom vi visar en meny direkt.
        # pylint: disable=unused-argument
        config_entry_name = self.config_entry.title or self.config_entry.data.get(CONF_NAME_SUFFIX, "Okänd")
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "basic_options",
                "edit_yaml"
            ],
            description_placeholders={
                "config_entry_name": config_entry_name
            }
        )

    async def async_step_basic_options(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> config_entries.FlowResult:
        """Redigera grundläggande parametrar."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            # Spara inställningarna och återgå till menyn? Eller avsluta?
            # Standardbeteende för OptionsFlow är att avsluta om man returnerar create_entry.
            # Men vi kanske vill återgå till menyn om det vore en komplex wizard.
            # Här avslutar vi, vilket verkar rimligt.
            return self.async_create_entry(title="", data=user_input)

        # Hämta nuvarande värden
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

        # Förbered placeholders för description (visar filsökväg)
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
            last_step=False # Inte sista steget längre eftersom vi har en meny
        )

    async def async_step_edit_yaml(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> config_entries.FlowResult:
        """
        Steg för att redigera YAML-filen direkt.
        Laddar filen, visar den i en TemplateSelector (kod-editor), validerar och sparar.
        """
        errors: Dict[str, str] = {}
        actions_file_path = _config_flow_get_actions_file_path(self.hass, self.config_entry)

        # Om användaren har skickat in formuläret (spara)
        if user_input is not None:
            yaml_content = user_input.get(CONF_YAML_CONTENT, "")

            # Validera YAML
            try:
                # Kontrollera att det är giltig YAML
                yaml.safe_load(yaml_content)

                # Om validering OK, spara filen atomärt
                # Vi gör detta i executorn för att inte blockera event loopen
                def save_file():
                    # Skriv till en tillfällig fil först för att undvika korruption
                    tmp_filename = f"{actions_file_path}.tmp"
                    with open(tmp_filename, "w", encoding="utf-8") as f:
                        f.write(yaml_content)

                    # Döp om den tillfälliga filen till den riktiga (atomär operation på POSIX)
                    os.replace(tmp_filename, actions_file_path)

                await self.hass.async_add_executor_job(save_file)

                # Om allt gick bra, avsluta flödet (eller återgå till meny)
                return self.async_create_entry(title="", data={})

            except yaml.YAMLError:
                errors["base"] = ERROR_INVALID_YAML
            except OSError:
                errors["base"] = ERROR_CANNOT_WRITE_ACTIONS_FILE
            except Exception: # pylint: disable=broad-exception-caught
                _LOGGER.exception("Oväntat fel vid sparande av YAML")
                errors["base"] = "unknown"

            # Om vi har fel, faller vi igenom och visar formuläret igen med felmeddelanden
            # och behåller användarens inmatning i yaml_content variabeln nedan (via user_input)

        # Ladda filinnehåll om vi inte precis försökte spara (och misslyckades)
        if user_input is None:
            try:
                def read_file():
                    if os.path.exists(actions_file_path):
                        with open(actions_file_path, "r", encoding="utf-8") as f:
                            return f.read()
                    return "" # Eller default content om filen saknas?

                yaml_content = await self.hass.async_add_executor_job(read_file)
            except OSError:
                errors["base"] = ERROR_CANNOT_READ_ACTIONS_FILE
                yaml_content = ""

        # Skapa schema för formuläret
        # Vi använder TemplateSelector för att få en bra editor.
        # Notera: TemplateSelector är egentligen för Jinja2 templates, men den ger
        # ofta syntax highlighting och multiline-stöd som är bättre än TextSelector.
        # Alternativt ObjectSelector, men den kan vara striktare med formatet.

        data_schema = vol.Schema({
            vol.Required(CONF_YAML_CONTENT, default=yaml_content): TemplateSelector()
        })

        return self.async_show_form(
            step_id="edit_yaml",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "actions_file_path": actions_file_path
            },
            last_step=True
        )
