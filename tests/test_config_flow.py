"""
Tester för Config Flow i KNX Dubbelklicksdetektor.
"""
from unittest.mock import MagicMock, mock_open, patch

import pytest
from homeassistant import config_entries, data_entry_flow

from custom_components.knx_doubleclick.config_flow import (
    KnxDoubleClickOptionsFlowHandler,
)
from custom_components.knx_doubleclick.const import (
    CONF_YAML_CONTENT,
    DOMAIN,
    ERROR_INVALID_YAML,
)


# Fixtur för en mockad config entry
@pytest.fixture
def mock_config_entry(mock_hass):
    entry = MagicMock(spec=config_entries.ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.domain = DOMAIN
    entry.title = "Test Knapp"
    entry.data = {
        "name_suffix": "Test",
        "knx_group_address": "1/1/1",
        "knx_value": 1,
        "double_click_window_seconds": 0.5
    }
    entry.options = {}

    # Mocka hass.config_entries.async_get_entry
    mock_hass.config_entries.async_get_entry.return_value = entry
    # Nödvändigt för OptionsFlow i nyare HA versioner
    mock_hass.config_entries.async_get_known_entry.return_value = entry
    return entry

@pytest.mark.asyncio
async def test_options_flow_init_menu(mock_hass, mock_config_entry):
    """
    Testar att options flow startar med en meny.

    Setup: Initiera options flow.
    Action: Kör async_step_init.
    Assert: Verifiera att resultatet är av typen MENU och har rätt alternativ.
    """

    # Initiera flödet manuellt eftersom vi mockar mycket
    flow = KnxDoubleClickOptionsFlowHandler(mock_config_entry)
    flow.hass = mock_hass
    # Sätt handler attributet manuellt (som HA gör internt)
    flow.handler = mock_config_entry.entry_id

    result = await flow.async_step_init()

    assert result["type"] == data_entry_flow.FlowResultType.MENU
    assert result["step_id"] == "init"
    assert "basic_options" in result["menu_options"]
    assert "edit_yaml" in result["menu_options"]

    # Verifiera att placeholders skickas med för att fixa UI-buggen
    assert "description_placeholders" in result
    assert "config_entry_name" in result["description_placeholders"]
    assert result["description_placeholders"]["config_entry_name"] == "Test Knapp"


@pytest.mark.asyncio
async def test_options_flow_edit_yaml_load(mock_hass, mock_config_entry):
    """
    Testar att edit_yaml steget laddar filinnehåll.

    Setup: Mocka filsystemet (os.path.exists och open) för att simulera en existerande fil.
    Action: Kör async_step_edit_yaml utan user_input.
    Assert: Verifiera att formuläret visas och att default-värdet är filens innehåll.
    """

    flow = KnxDoubleClickOptionsFlowHandler(mock_config_entry)
    flow = KnxDoubleClickOptionsFlowHandler(mock_config_entry)
    flow = KnxDoubleClickOptionsFlowHandler(mock_config_entry)
    flow.hass = mock_hass
    flow.handler = mock_config_entry.entry_id

    file_content = "some_key: some_value"

    # Vi måste mocka hass.async_add_executor_job eftersom config_flow kör blocking IO där
    async def mock_async_add_executor_job(func, *args, **kwargs):
        return func(*args, **kwargs)

    mock_hass.async_add_executor_job = mock_async_add_executor_job

    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=file_content)):

        result = await flow.async_step_edit_yaml()

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "edit_yaml"


@pytest.mark.asyncio
async def test_options_flow_edit_yaml_save_valid(mock_hass, mock_config_entry):
    """
    Testar att spara giltig YAML.

    Setup: Mocka filsystemet (os.replace och open).
    Action: Skicka in giltig YAML till async_step_edit_yaml.
    Assert: Verifiera att os.replace anropas (atomärt sparande) och att flödet avslutas (CREATE_ENTRY).
    """

    flow = KnxDoubleClickOptionsFlowHandler(mock_config_entry)
    flow = KnxDoubleClickOptionsFlowHandler(mock_config_entry)
    flow.hass = mock_hass
    flow.handler = mock_config_entry.entry_id

    # Mocka executor
    async def mock_async_add_executor_job(func, *args, **kwargs):
        return func(*args, **kwargs)
    mock_hass.async_add_executor_job = mock_async_add_executor_job

    user_input = {CONF_YAML_CONTENT: "key: value"}

    with patch("os.replace") as mock_replace, \
         patch("builtins.open", mock_open()) as mock_file:

        result = await flow.async_step_edit_yaml(user_input)

        # Verifiera att filen skrevs
        mock_file.assert_called()
        # Verifiera att filen flyttades (atomärt sparande)
        mock_replace.assert_called()

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY


@pytest.mark.asyncio
async def test_options_flow_edit_yaml_save_invalid(mock_hass, mock_config_entry):
    """
    Testar att spara ogiltig YAML.

    Setup: Förbered ogiltig YAML-sträng (tabbar istället för spaces, eller syntaxfel).
    Action: Skicka in ogiltig YAML.
    Assert: Verifiera att vi får tillbaka formuläret med felkod 'invalid_yaml'.
    """

    flow = KnxDoubleClickOptionsFlowHandler(mock_config_entry)
    flow.hass = mock_hass
    flow.handler = mock_config_entry.entry_id

    user_input = {CONF_YAML_CONTENT: "key: value\n  sub: [} # Syntax error"}

    result = await flow.async_step_edit_yaml(user_input)

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"]["base"] == ERROR_INVALID_YAML
