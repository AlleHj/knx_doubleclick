# Versionshistorik:
# Version: 0.8.15 (Fix)
# Datum: 2025-07-22
# Upphovsman: AI-Assistent
# Ändringar:
# - Borttaget anrop till hass.http.register_static_path i async_setup_entry.
#   Denna funktion är borttagen i nyare Home Assistant-versioner (fr.o.m. 2025.7)
#   och orsakade att komponenten inte kunde starta.
# - Raderat all logik relaterad till webbpaneler och den custom API-vyn
#   för att säkerställa att komponentens kärnfunktion (sensor-setup) fungerar.

import logging
import os

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS, ACTIONS_DIR_BASENAME

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Sätter upp KNX Dubbelklicksdetektor från en config entry."""
    _LOGGER.info("Sätter upp config entry för KNX Dubbelklicksdetektor: %s", entry.title)

    # Säkerställ att katalogen för åtgärdsfiler existerar
    actions_dir_path = hass.config.path(ACTIONS_DIR_BASENAME)
    if not await hass.async_add_executor_job(os.path.exists, actions_dir_path):
        try:
            _LOGGER.info("Skapar katalog för åtgärdsfiler: %s", actions_dir_path)
            await hass.async_add_executor_job(os.makedirs, actions_dir_path, exist_ok=True)
        except Exception as e:
            _LOGGER.error("Kunde inte skapa katalog för åtgärdsfiler %s: %s", actions_dir_path, e)
            return False

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data

    # Vidarebefordra setup till sensor-plattformen
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Lägg till en lyssnare för när optioner uppdateras
    entry.async_on_unload(entry.add_update_listener(async_update_options_listener))

    _LOGGER.debug("Config entry %s uppsatt.", entry.title)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Laddar ur en config entry."""
    _LOGGER.info("Laddar ur config entry för KNX Dubbelklicksdetektor: %s", entry.title)
    
    # Korrekt sätt att ladda ur plattformar
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        _LOGGER.debug("Config entry %s urladdad.", entry.title)

    return unload_ok

async def async_update_options_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Hanterar uppdateringar av options för config entry."""
    _LOGGER.info("Optioner uppdaterade för %s, laddar om integrationen.", entry.title)
    await hass.config_entries.async_reload(entry.entry_id)