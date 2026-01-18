# Versionshistorik:
# Version: 0.8.20
# Datum: 2026-01-15
# Upphovsman: Home Assistant Expert
# Ändringar:
# - Renasat bort konstanter för YAML-editor då den funktionen tagits bort från UI.

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

# --- Grundläggande Exempel: Styr en specifik enhet ---
# Detta exempel tänder en specifik lampa eller switch.
# Ersätt 'switch.min_switch_entitet' med ditt eget entity_id.
#
# - service: switch.turn_on
#   target:
#     entity_id: switch.min_switch_entitet


# --- Exempel: Använda Etiketter (Labels) ---
# Du kan styra flera enheter samtidigt genom att använda etiketter (Labels).
# 1. Skapa en etikett i Home Assistant (Inställningar -> Etiketter).
# 2. Tilldela etiketten till de enheter du vill styra (t.ex. alla fönsterlampor).
# 3. Använd 'label_id' i 'target' sektionen.
#
# Exempel: Tänd alla enheter som har etiketten 'kvallsbelysning'.
#
# - service: light.turn_on
#   target:
#     label_id: kvallsbelysning


# --- Exempel: Använda Områden (Areas) ---
# På samma sätt kan du styra alla enheter i ett specifikt rum/område.
#
# Exempel: Släck allt i vardagsrummet.
#
# - service: light.turn_off
#   target:
#     area_id: vardagsrum


# --- Exempel: Avancerad Script-logik ---
# Du kan använda villkor och annan script-logik.
#
# Exempel: Tänd lampan endast om solen har gått ner.
#
# - condition: state
#   entity_id: sun.sun
#   state: "below_horizon"
# - service: light.turn_on
#   target:
#     entity_id: light.hallen
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
ERROR_INVALID_YAML = "invalid_yaml"

# Menyval
CONF_MENU_OPTION_SETTINGS = "settings"
CONF_MENU_OPTION_YAML = "yaml_editor"
CONF_YAML_CONTENT = "yaml_content"
