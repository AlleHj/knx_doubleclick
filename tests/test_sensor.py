"""
Tester för Sensor-logik i KNX Dubbelklicksdetektor.
"""
from datetime import timedelta
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from homeassistant.util import dt as dt_util

from custom_components.knx_doubleclick.sensor import KnxDoubleClickSensor
from custom_components.knx_doubleclick.const import (
    CONF_KNX_GROUP_ADDRESS,
    CONF_KNX_VALUE,
    CONF_DOUBLE_CLICK_WINDOW_SECONDS,
    CONF_NAME_SUFFIX
)

# Fixtur för mockad config entry
@pytest.fixture
def mock_config_entry():
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.title = "Test Knapp"
    entry.data = {
        CONF_NAME_SUFFIX: "Test",
        CONF_KNX_GROUP_ADDRESS: "1/1/1",
        CONF_KNX_VALUE: 1,
        CONF_DOUBLE_CLICK_WINDOW_SECONDS: 1.0 # 1 sekunds fönster för enkelhetens skull
    }
    entry.options = {}
    return entry

@pytest.mark.asyncio
async def test_double_click_too_slow(mock_hass, mock_config_entry):
    """
    Testar att inget händer om dubbelklicket är för långsamt.

    Scenario:
    1. Konfigurerat fönster är 1.0 sekund.
    2. Första klicket kommer vid T0.
    3. Andra klicket kommer vid T0 + 1.1 sekunder.

    Förväntat utfall:
    - Ingen åtgärd ska triggas.
    """
    # Setup
    sensor = KnxDoubleClickSensor(mock_hass, mock_config_entry, "Test Sensor")

    # Mocka hass.bus.async_listen (behövs egentligen inte då vi anropar _async_handle_knx_event direkt, men bra för setup)
    mock_hass.bus.async_listen = MagicMock()

    # Mocka filhantering (så vi inte får felmeddelanden om saknad fil, även om den inte ska läsas)
    mock_hass.async_add_executor_job = AsyncMock(return_value=True)

    # Initiera sensorn (sätter upp lyssnare etc.)
    await sensor.async_added_to_hass()

    # Mocka async_write_ha_state för att undvika fel då entiteten inte är fullt registrerad
    sensor.async_write_ha_state = MagicMock()

    # Mocka tid
    now = dt_util.utcnow()

    # Action: Första klicket
    with patch("homeassistant.util.dt.utcnow", return_value=now):
        event1 = MagicMock()
        event1.data = {"destination": "1/1/1", "value": 1}
        await sensor._async_handle_knx_event(event1)

    # Action: Andra klicket (för sent)
    later = now + timedelta(seconds=1.1)
    with patch("homeassistant.util.dt.utcnow", return_value=later):
        event2 = MagicMock()
        event2.data = {"destination": "1/1/1", "value": 1}

        # Vi måste också mocka _load_parsed_actions_from_file för säkerhets skull,
        # för att se att den INTE anropas eller att exekvering inte sker.
        # Men om logiken stämmer ska vi inte ens komma dit.

        with patch.object(sensor, "_load_parsed_actions_from_file", new_callable=AsyncMock) as mock_load:
            await sensor._async_handle_knx_event(event2)

            # Assert
            mock_load.assert_not_called()

@pytest.mark.asyncio
async def test_double_click_success(mock_hass, mock_config_entry):
    """
    Testar att åtgärder körs om dubbelklicket är inom tidsfönstret.

    Scenario:
    1. Konfigurerat fönster är 1.0 sekund.
    2. Första klicket kommer vid T0.
    3. Andra klicket kommer vid T0 + 0.5 sekunder.
    4. Åtgärdsfilen innehåller en enkel 'light.turn_on'.

    Förväntat utfall:
    - Åtgärden 'light.turn_on' ska anropas via hass.services.async_call.
    """
    # Setup
    sensor = KnxDoubleClickSensor(mock_hass, mock_config_entry, "Test Sensor")

    mock_hass.async_add_executor_job = AsyncMock(return_value=True) # Mock file exists check
    mock_hass.services.async_call = AsyncMock()

    await sensor.async_added_to_hass()

    # Mocka async_write_ha_state
    sensor.async_write_ha_state = MagicMock()

    now = dt_util.utcnow()

    # Action: Första klicket
    with patch("homeassistant.util.dt.utcnow", return_value=now):
        event1 = MagicMock()
        event1.data = {"destination": "1/1/1", "value": 1}
        await sensor._async_handle_knx_event(event1)

    # Action: Andra klicket (inom tid)
    later = now + timedelta(seconds=0.5)
    with patch("homeassistant.util.dt.utcnow", return_value=later):
        event2 = MagicMock()
        event2.data = {"destination": "1/1/1", "value": 1}

        # Mocka att vi laddar en giltig åtgärd
        fake_actions = [{"service": "light.turn_on", "target": {"entity_id": "light.test"}}]

        with patch.object(sensor, "_load_parsed_actions_from_file", new_callable=AsyncMock, return_value=fake_actions) as mock_load:
            await sensor._async_handle_knx_event(event2)

            # Assert
            mock_load.assert_called_once()

            # Verifiera att tjänsten anropades
            mock_hass.services.async_call.assert_called_once()
            args, kwargs = mock_hass.services.async_call.call_args
            assert args[0] == "light" # Domain
            assert args[1] == "turn_on" # Service
            # Data och target kan variera beroende på implementering, men vi kollar kwargs
            assert "target" in kwargs
            assert kwargs["target"] == {"entity_id": "light.test"}
