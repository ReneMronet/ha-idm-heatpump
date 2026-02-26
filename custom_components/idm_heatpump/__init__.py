# Datei: __init__.py
"""
iDM Wärmepumpe (Modbus TCP)
Version: v2.0
Stand: 2026-02-26

Änderungen v2.0:
- heating_circuits in hass.data verfügbar
- Options-Update-Listener: Reload bei Änderung der Heizkreise
- Migration von Config-Version 1 → 2 (Fallback auf ["A", "C"])
"""

import logging
from homeassistant.const import Platform
from .const import (
    DOMAIN,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    CONF_HEATING_CIRCUITS,
    DEFAULT_HEATING_CIRCUITS,
)

_LOGGER = logging.getLogger(__name__)

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

    heating_circuits = entry.options.get(
        CONF_HEATING_CIRCUITS,
        entry.data.get(CONF_HEATING_CIRCUITS, DEFAULT_HEATING_CIRCUITS),
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "data": entry.data,
        "options": entry.options,
        "update_interval": update_interval,
        "heating_circuits": heating_circuits,
    }

    # Listener: bei Options-Änderung Integration neu laden
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass, entry):
    """Wird aufgerufen wenn Options geändert werden → Reload."""
    _LOGGER.info("iDM Wärmepumpe: Options geändert, Integration wird neu geladen")
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_migrate_entry(hass, config_entry):
    """Migration von älteren Config-Versionen."""
    if config_entry.version == 1:
        _LOGGER.info("Migriere iDM Config von Version 1 → 2")
        new_data = {**config_entry.data}
        if CONF_HEATING_CIRCUITS not in new_data:
            new_data[CONF_HEATING_CIRCUITS] = DEFAULT_HEATING_CIRCUITS
        hass.config_entries.async_update_entry(
            config_entry, data=new_data, version=2
        )
    return True
