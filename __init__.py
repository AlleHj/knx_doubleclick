# Versionshistorik:
# Version: 0.3.16
# Datum: 2025-05-25
# Upphovsman: AI-Assistent
# Ändringar:
# - Inga funktionella ändringar.
#
# Version: 0.3.15
# Datum: 2025-05-25
# Upphovsman: AI-Assistent
# Ändringar:
# - Inga funktionella ändringar.

"""KNX Dubbelklicksdetektor Custom Component."""
import logging
import os

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS, ACTIONS_DIR_BASENAME

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Sätter upp KNX Dubbelklicksdetektor från en config entry."""
    _LOGGER.info("Sätter upp config entry för KNX Dubbelklicksdetektor: %s", entry.title)

    actions_dir_path = hass.config.path(ACTIONS_DIR_BASENAME)
    
    _LOGGER.info(
        "Sökväg för åtgärdsfiler för KNX Dubbelklicksdetektor är: %s.",
        actions_dir_path
    )

    if not await hass.async_add_executor_job(os.path.exists, actions_dir_path):
        try:
            _LOGGER.info("Skapar katalog för åtgärdsfiler: %s", actions_dir_path)
            await hass.async_add_executor_job(os.makedirs, actions_dir_path, {"exist_ok": True})
        except Exception as e:
            _LOGGER.error("Kunde inte skapa katalog för åtgärdsfiler %s: %s", actions_dir_path, e)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    entry.async_on_unload(entry.add_update_listener(async_update_options_listener))

    _LOGGER.debug("Config entry %s uppsatt.", entry.title)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Laddar ur en config entry."""
    _LOGGER.info("Laddar ur config entry för KNX Dubbelklicksdetektor: %s", entry.title)
    
    results = []
    for platform in PLATFORMS:
        results.append(await hass.config_entries.async_forward_entry_unload(entry, platform))
    unload_ok = all(results)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.debug("Config entry %s urladdad.", entry.title)

    return unload_ok

async def async_update_options_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Hanterar uppdateringar av options för config entry."""
    _LOGGER.info("Optioner uppdaterade för %s, laddar om integrationen.", entry.title)
    await hass.config_entries.async_reload(entry.entry_id)