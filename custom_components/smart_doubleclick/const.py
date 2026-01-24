# Versionshistorik:
# Version: 1.0.0
# Datum: 2026-01-15
# Upphovsman: Home Assistant Expert
# Ändringar:
# - Renasat bort konstanter för YAML-editor då den funktionen tagits bort från UI.
# - Lagt till Debug-läge.

"""Konstanter för Smart Double Click-integrationen."""

# Domänen för integrationen
DOMAIN = "smart_doubleclick"

# Plattformar
PLATFORMS = ["binary_sensor"]

# Konfigurationsnycklar
CONF_NAME_SUFFIX = "name_suffix"
CONF_KNX_GROUP_ADDRESS = "knx_group_address"  # Deprecated/Legacy
CONF_SOURCE_ENTITY = "source_entity"
CONF_KNX_VALUE = "knx_value"  # Deprecated/Legacy
CONF_TRIGGER_VALUE = "trigger_value"
CONF_DOUBLE_CLICK_WINDOW_SECONDS = "double_click_window_seconds"
CONF_DEBUG_MODE = "debug_mode"

# Standardvärden
DEFAULT_KNX_VALUE = 1
DEFAULT_TRIGGER_VALUE = "on"
DEFAULT_DOUBLE_CLICK_WINDOW_SECONDS = 0.7
DEFAULT_NAME_SUFFIX = "Min Knapp"
DEFAULT_DEBUG_MODE = False

# Katalog och standardinnehåll för åtgärdsfiler
ACTIONS_DIR_BASENAME = "smart_doubleclick_actions"

# DEFAULT_ACTIONS_FILE_CONTENT
DEFAULT_ACTIONS_FILE_CONTENT = """#---------------------------------------------------------------------------
# Åtgärder för Smart Double Click
#
# Denna fil är kopplad till en specifik instans av Smart Double Click.
# Lägg till dina önskade Home Assistant-åtgärder i YAML-format nedan.
#---------------------------------------------------------------------------

# --- Grundläggande Exempel: Styr en specifik enhet ---
# Detta exempel tänder en specifik lampa eller switch.
# Ersätt 'switch.min_switch_entitet' med ditt eget entity_id.
#
# - service: switch.turn_on
#   target:
#     entity_id: switch.min_switch_entitet
"""

# Attribut
ATTR_LAST_CLICK_TIME = "last_click_time"
ATTR_KNX_GROUP_ADDRESS = "knx_group_address"
ATTR_SOURCE_ENTITY = "source_entity"
ATTR_KNX_LISTEN_VALUE = "knx_listen_value"
ATTR_TRIGGER_VALUE = "trigger_value"
ATTR_DOUBLE_CLICK_WINDOW = "double_click_window_seconds"
ATTR_ACTIONS_FILE_PATH = "actions_file_path"
ATTR_LAST_TIME_DIFFERENCE = "last_time_difference_seconds"

# Nycklar som indikerar att en åtgärd är mer komplex än ett enkelt serviceanrop
COMPLEX_ACTION_KEYS = [
    "condition",
    "delay",
    "repeat",
    "choose",
    "sequence",
    "wait_template",
    "wait_for_trigger",
    "event",
    "event_template",
    "variables",
    "stop",
    "parallel",
    "scene",
]

# Felnycklar
ERROR_CANNOT_READ_ACTIONS_FILE = "cannot_read_actions_file"
ERROR_CANNOT_WRITE_ACTIONS_FILE = "cannot_write_actions_file"
ERROR_INVALID_YAML = "invalid_yaml"

# Menyval
CONF_MENU_OPTION_SETTINGS = "settings"
CONF_MENU_OPTION_YAML = "yaml_editor"
CONF_YAML_CONTENT = "yaml_content"
