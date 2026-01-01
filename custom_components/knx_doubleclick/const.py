# Versionshistorik:
# Version: 0.8.17
# Datum: 2025-05-25
# Upphovsman: AI-Assistent
# Ändringar:
# - Förberett för nytt försök med selector-syntax för YAML-editor ("code_editor" med mode "yaml").
#
# Version: 0.3.15
# Datum: 2025-05-25
# Upphovsman: AI-Assistent
# Ändringar:
# - Förberett för justerad hantering av default/suggested_value för YAML-editor i config_flow.py.


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
CONF_ACTIONS_YAML_EDITOR = "actions_yaml_editor_content" # Nyckel för YAML-editorns innehåll i Options Flow

# Standardvärden
DEFAULT_KNX_VALUE = 1
DEFAULT_DOUBLE_CLICK_WINDOW_SECONDS = 0.7
DEFAULT_NAME_SUFFIX = "Min Knapp"

# Katalog och standardinnehåll för åtgärdsfiler
ACTIONS_DIR_BASENAME = "knx_doubleclick_actions"

# DEFAULT_ACTIONS_FILE_CONTENT är nu mer omfattande med många utkommenterade exempel
DEFAULT_ACTIONS_FILE_CONTENT = """#---------------------------------------------------------------------------
# Åtgärder för KNX Dubbelklicksdetektor
#
# Denna fil är kopplad till en specifik instans av KNX Dubbelklicksdetektor.
# Du kan identifiera vilken instans genom kommentarerna som automatiskt läggs till
# överst i denna fil när den skapas, via sensor-entitetens attribut,
# eller via "Alternativ"-dialogen i Home Assistant för denna instans.
#
# Lägg till dina önskade Home Assistant-åtgärder i YAML-format nedan.
# Varje åtgärd börjar med ett bindestreck "-".
# Åtgärderna körs i den ordning de listas.
#
# OBS: Komplexa skriptfunktioner (delay, condition, choose, repeat etc.)
# kan eventuellt fallera beroende på din Home Assistant-miljö och Python-version.
# Enkla, direkta serviceanrop har visat sig fungera mest tillförlitligt.
#---------------------------------------------------------------------------

# ----- Exempel på Åtgärder -----

# Exempel: Skicka en persistent notifiering i Home Assistant (utkommenterad som standard)
# - service: persistent_notification.create
#   data:
#     message: "Dubbelklick detekterat för '{{{{ config_entry_name }}}}'!"
#     title: "KNX Dubbelklick"
#     # notification_id: "knx_double_click_{{{{ trigger.name_suffix | slugify }}}}" # För att undvika flera notiser

# Exempel: Tänd en switch
# - service: switch.turn_on
#   target:
#     entity_id: switch.min_switch_entitet

# Exempel: Tänd en dimmerlampa och sätt ljusstyrkan till 50%
# - service: light.turn_on
#   target:
#     entity_id: light.min_dimmer_entitet
#   data:
#     brightness_pct: 50

# Exempel: Aktivera en scen
# - service: scene.turn_on
#   target:
#     entity_id: scene.min_scen

# Exempel: Kör ett befintligt Home Assistant-skript
# - service: script.turn_on
#   target:
#     entity_id: script.mitt_fantastiska_script

# Exempel: Trigga/starta en befintlig Home Assistant-automation
# - service: automation.trigger
#   target:
#     entity_id: automation.min_coola_automation
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

# Felnycklar för översättningar (Options Flow)
ERROR_CANNOT_READ_ACTIONS_FILE = "cannot_read_actions_file"
ERROR_CANNOT_WRITE_ACTIONS_FILE = "cannot_write_actions_file"
ERROR_INVALID_ACTIONS_YAML_IN_EDITOR = "invalid_actions_yaml_in_editor"