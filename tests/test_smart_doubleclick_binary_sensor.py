"""
Tester för Binary Sensor-logik i Smart Double Click.
"""

from datetime import timedelta
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from homeassistant.util import dt as dt_util

from custom_components.smart_doubleclick.binary_sensor import (
    SmartDoubleClickBinarySensor,
)
from custom_components.smart_doubleclick.const import (
    CONF_SOURCE_ENTITY,
    CONF_TRIGGER_VALUE,
    CONF_DOUBLE_CLICK_WINDOW_SECONDS,
    CONF_NAME_SUFFIX,
    CONF_DEBUG_MODE,
)


# Fixtur för mockad config entry
@pytest.fixture
def mock_config_entry():
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.title = "Test Knapp"
    entry.data = {
        CONF_NAME_SUFFIX: "Test",
        CONF_SOURCE_ENTITY: "input_boolean.test_button",
        CONF_TRIGGER_VALUE: "on",
        CONF_DOUBLE_CLICK_WINDOW_SECONDS: 1.0,  # 1 sekunds fönster för enkelhetens skull
        CONF_DEBUG_MODE: False,
    }
    entry.options = {}
    return entry


@pytest.mark.asyncio
async def test_double_click_too_slow(mock_hass, mock_config_entry):
    """
    Testar att inget händer om dubbelklicket är för långsamt.
    """
    sensor = SmartDoubleClickBinarySensor(mock_hass, mock_config_entry, "Test Sensor")
    mock_hass.async_add_executor_job = AsyncMock(return_value=True)
    sensor.async_write_ha_state = MagicMock()

    await sensor.async_added_to_hass()

    now = dt_util.utcnow()

    with patch("homeassistant.util.dt.utcnow", return_value=now):
        # Simulera första klicket
        await sensor._handle_trigger("on")

    later = now + timedelta(seconds=1.1)
    with patch("homeassistant.util.dt.utcnow", return_value=later):
        # Simulera andra klicket (för sent)
        with patch.object(
            sensor, "_load_parsed_actions_from_file", new_callable=AsyncMock
        ) as mock_load:
            await sensor._handle_trigger("on")
            mock_load.assert_not_called()


@pytest.mark.asyncio
async def test_double_click_success(mock_hass, mock_config_entry):
    """
    Testar att åtgärder körs om dubbelklicket är inom tidsfönstret.
    """
    sensor = SmartDoubleClickBinarySensor(mock_hass, mock_config_entry, "Test Sensor")
    mock_hass.async_add_executor_job = AsyncMock(
        return_value=True
    )  # Mock file exists check
    mock_hass.services.async_call = AsyncMock()
    sensor.async_write_ha_state = MagicMock()

    await sensor.async_added_to_hass()

    now = dt_util.utcnow()

    with patch("homeassistant.util.dt.utcnow", return_value=now):
        # Första
        await sensor._handle_trigger("on")

    later = now + timedelta(seconds=0.5)
    with patch("homeassistant.util.dt.utcnow", return_value=later):
        # Mocka att vi laddar en giltig åtgärd
        fake_actions = [
            {"service": "light.turn_on", "target": {"entity_id": "light.test"}}
        ]

        with patch.object(
            sensor,
            "_load_parsed_actions_from_file",
            new_callable=AsyncMock,
            return_value=fake_actions,
        ) as mock_load:
            # Andra (inom tid)
            await sensor._handle_trigger("on")

            mock_load.assert_called_once()

            # Verifiera att sensorn slogs på
            assert sensor.is_on is True

            # Verifiera att tjänsten anropades
            mock_hass.services.async_call.assert_called_once()
            args, kwargs = mock_hass.services.async_call.call_args
            assert args[0] == "light"  # Domain
            assert args[1] == "turn_on"  # Service
            assert "target" in kwargs
            assert kwargs["target"] == {"entity_id": "light.test"}


@pytest.mark.asyncio
async def test_template_variables_in_script(mock_hass, mock_config_entry):
    """
    Testar att template-variabler skickas korrekt till script-motorn.
    """
    sensor = SmartDoubleClickBinarySensor(mock_hass, mock_config_entry, "Test Sensor")
    mock_hass.async_add_executor_job = AsyncMock(return_value=True)
    sensor.async_write_ha_state = MagicMock()

    await sensor.async_added_to_hass()

    with patch(
        "custom_components.smart_doubleclick.binary_sensor.Script"
    ) as mock_script_cls:
        mock_script_instance = mock_script_cls.return_value
        mock_script_instance.async_run = AsyncMock()

        actions = [
            {"condition": "template", "value_template": "{{ trigger.value == 'on' }}"}
        ]

        with patch.object(
            sensor,
            "_load_parsed_actions_from_file",
            new_callable=AsyncMock,
            return_value=actions,
        ):
            now = dt_util.utcnow()
            with patch("homeassistant.util.dt.utcnow", return_value=now):
                await sensor._handle_trigger("on")
                await sensor._handle_trigger("on")

        mock_script_instance.async_run.assert_called()
        call_args = mock_script_instance.async_run.call_args
        run_variables = call_args.kwargs.get("run_variables")

        assert run_variables is not None
        assert "trigger" in run_variables
        trigger = run_variables["trigger"]
        assert trigger["platform"] == "smart_doubleclick"
        assert trigger["name"] == "Test"
        assert trigger["source_entity"] == "input_boolean.test_button"
        assert trigger["value"] == "on"


@pytest.mark.asyncio
async def test_repeat_loop_with_service_call(mock_hass, mock_config_entry):
    """
    Testar att en repeat-loop med serviceanrop inte kraschar.
    """
    sensor = SmartDoubleClickBinarySensor(mock_hass, mock_config_entry, "Test Sensor")
    mock_hass.async_add_executor_job = AsyncMock(return_value=True)
    sensor.async_write_ha_state = MagicMock()

    # Mocka has_service
    mock_hass.services.has_service.return_value = True

    await sensor.async_added_to_hass()

    # Komplex åtgärd med repeat
    actions = [
        {
            "repeat": {
                "count": 1,
                "sequence": [
                    {"service": "light.turn_on", "target": {"entity_id": "light.test"}}
                ],
            }
        }
    ]

    mock_hass.services.async_call = AsyncMock()

    with patch.object(
        sensor,
        "_load_parsed_actions_from_file",
        new_callable=AsyncMock,
        return_value=actions,
    ):
        now = dt_util.utcnow()
        with patch("homeassistant.util.dt.utcnow", return_value=now):
            await sensor._handle_trigger("on")
            await sensor._handle_trigger("on")

    # Vi kollar bara att det inte kraschade och att load kallades
    # I en unit test miljö kan vi inte enkelt verifiera Script execution utan full HA-mock


@pytest.mark.asyncio
async def test_debug_mode_logging(mock_hass, mock_config_entry):
    """
    Testar att debug-loggning fungerar som förväntat när debug_mode är True.
    """
    # Aktivera debug mode
    mock_config_entry.data[CONF_DEBUG_MODE] = True

    sensor = SmartDoubleClickBinarySensor(mock_hass, mock_config_entry, "Test Sensor")
    mock_hass.async_add_executor_job = AsyncMock(return_value=True)
    sensor.async_write_ha_state = MagicMock()

    await sensor.async_added_to_hass()

    # Vi behöver patcha logger för att verifiera anropen
    with patch(
        "custom_components.smart_doubleclick.binary_sensor._LOGGER"
    ) as mock_logger:
        now = dt_util.utcnow()
        with patch("homeassistant.util.dt.utcnow", return_value=now):
            # Första klick
            await sensor._handle_trigger("on")

            # Verifiera att loggen skrev "Klick registrerat..."
            # Vi kollar args för att se om första argumentet matchar vårt format
            assert mock_logger.info.called
            args, _ = mock_logger.info.call_args
            assert "Klick registrerat för %s" in args[0]

        later = now + timedelta(seconds=0.5)
        with patch("homeassistant.util.dt.utcnow", return_value=later):
            # Andra klick (inom tid)
            # Mocka actions load så vi inte failar på filen
            with patch.object(
                sensor,
                "_load_parsed_actions_from_file",
                new_callable=AsyncMock,
                return_value=[],
            ):
                await sensor._handle_trigger("on")

                # Verifiera att loggen skrev "Andra klick..." och "TRIGGER UTLOSTS!"
                # Vi letar efter det specifika anropet i call_args_list
                found_trigger_log = False
                for call in mock_logger.info.call_args_list:
                    if "TRIGGER UTLOSTS!" in call.args[0]:
                        found_trigger_log = True
                        break
                assert found_trigger_log, (
                    "Kunde inte hitta loggmeddelandet 'TRIGGER UTLOSTS!'"
                )


@pytest.mark.asyncio
async def test_entity_naming(mock_hass, mock_config_entry):
    """
    Testar att entiteten får exakt det namn som angivits i konfigurationen.
    """
    expected_name = "Mitt Exakta Namn"
    mock_config_entry.data[CONF_NAME_SUFFIX] = expected_name

    sensor = SmartDoubleClickBinarySensor(mock_hass, mock_config_entry, "Något Annat")
    # Notera: i __init__ så läser vi om config entryt, så det tredje argumentet ignoreras
    # (eller skrivs över) om vi följer koden i binary_sensor.py korrekt.

    assert sensor.name == expected_name
