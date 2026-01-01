# Versionshistorik:
# Version: 0.8.17
# Datum: 2026-01-01
# Upphovsman: AI-Assistent
# Ändringar:
# - Fixat krasch vid skapande av katalog genom att använda functools.partial
#   för att skicka 'exist_ok=True' till os.makedirs via async_add_executor_job.

import logging
import os
from functools import partial

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
            # ANVÄND PARTIAL HÄR: async_add_executor_job stöder inte kwargs direkt
            await hass.async_add_executor_job(partial(os.makedirs, actions_dir_path, exist_ok=True))
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