"""Konstanter för KNX Dubbelklicksdetektor-integrationen."""

# Domänen för integrationen
DOMAIN = "knx_doubleclick"

# Plattformar
PLATFORMS = ["sensor"]

# Konfigurationsnycklar
CONF_NAME_SUFFIX = "name_suffix"
CONF_KNX_GROUP_ADDRESS = "knx_group_address"
CONF_KNX_VALUE = "knx_value"
CONF_DOUBLE_CLICK_WINDOW_SECONDS = "double_click_window_seconds"
CONF_YAML_CONTENT = "yaml_content" # Nyckel för att hantera innehållet i native editor

# Standardvärden
DEFAULT_KNX_VALUE = 1
DEFAULT_DOUBLE_CLICK_WINDOW_SECONDS = 0.7
DEFAULT_NAME_SUFFIX = "Min Knapp"

# Katalog och standardinnehåll för åtgärdsfiler
ACTIONS_DIR_BASENAME = "knx_doubleclick_actions"

# DEFAULT_ACTIONS_FILE_CONTENT
DEFAULT_ACTIONS_FILE_CONTENT = """#---------------------------------------------------------------------------
# Åtgärder för KNX Dubbelklicksdetektor
#
# Denna fil är kopplad till en specifik instans av KNX Dubbelklicksdetektor.
# Lägg till dina önskade Home Assistant-åtgärder i YAML-format nedan.
#---------------------------------------------------------------------------

# Exempel: Tänd en switch
# - service: switch.turn_on
#   target:
#     entity_id: switch.min_switch_entitet
"""

# Attribut
ATTR_LAST_CLICK_TIME = "last_click_time"
ATTR_KNX_GROUP_ADDRESS = "knx_group_address"
ATTR_KNX_LISTEN_VALUE = "knx_listen_value"
ATTR_DOUBLE_CLICK_WINDOW = "double_click_window_seconds"
ATTR_ACTIONS_FILE_PATH = "actions_file_path"
ATTR_LAST_TIME_DIFFERENCE = "last_time_difference_seconds"

# Nycklar som indikerar att en åtgärd är mer komplex än ett enkelt serviceanrop
COMPLEX_ACTION_KEYS = [
    "condition", "delay", "repeat", "choose", "sequence",
    "wait_template", "wait_for_trigger", "event", "event_template",
    "variables", "stop", "parallel", "scene"
]

# Felnycklar
ERROR_CANNOT_READ_ACTIONS_FILE = "cannot_read_actions_file"
ERROR_CANNOT_WRITE_ACTIONS_FILE = "cannot_write_actions_file"