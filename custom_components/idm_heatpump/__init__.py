# Datei: __init__.py
"""
iDM Wärmepumpe (Modbus TCP)
Version: v1.9 (Dokumentations-Update)
Stand: 2025-09-24
"""

from homeassistant.const import Platform
from .const import DOMAIN, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL

# Jetzt auch NUMBER dabei
PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.NUMBER,
]


async def async_setup_entry(hass, entry):
    hass.data.setdefault(DOMAIN, {})

    update_interval = entry.options.get(
        CONF_UPDATE_INTERVAL,
        entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "data": entry.data,
        "options": entry.options,
        "update_interval": update_interval,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
