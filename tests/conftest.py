"""
Konfiguration för pytest-fixturer.
Denna fil innehåller fixturer som används av testerna för att mocka Home Assistant-funktioner.
"""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_hass():
    """Skapar en mock av Home Assistant-objektet."""
    hass = MagicMock()
    hass.config.path = MagicMock(side_effect=lambda *args: "/".join(args))
    return hass
