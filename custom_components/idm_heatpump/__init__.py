"""
iDM Wärmepumpe (Modbus TCP)
Version: v5.0
Stand: 2026-02-26

Änderungen v5.0 (Schritt 2):
- Sensor-Gruppen in hass.data (sensor_groups)
- build_register_map() mit sensor_groups-Parameter
- Migration v2→v3: sensor_groups mit Defaults hinzufügen
"""

import logging
from datetime import timedelta

from homeassistant.const import Platform
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    CONF_UNIT_ID,
    DEFAULT_UNIT_ID,
    CONF_HEATING_CIRCUITS,
    DEFAULT_HEATING_CIRCUITS,
    CONF_SENSOR_GROUPS,
    DEFAULT_SENSOR_GROUPS,
    build_register_map,
)
from .modbus_handler import IDMModbusHandler

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.NUMBER,
]


async def async_setup_entry(hass, entry):
    hass.data.setdefault(DOMAIN, {})

    # --- Konfiguration auslesen ---
    host = entry.data["host"]
    port = entry.data.get("port", 502)
    unit_id = entry.data.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)

    update_interval = entry.options.get(
        CONF_UPDATE_INTERVAL,
        entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
    )

    heating_circuits = entry.options.get(
        CONF_HEATING_CIRCUITS,
        entry.data.get(CONF_HEATING_CIRCUITS, DEFAULT_HEATING_CIRCUITS),
    )

    sensor_groups = entry.options.get(
        CONF_SENSOR_GROUPS,
        entry.data.get(CONF_SENSOR_GROUPS, DEFAULT_SENSOR_GROUPS),
    )

    # --- Geteilter Modbus-Client ---
    client = IDMModbusHandler(host, port, unit_id)
    await client.connect()

    # --- Register-Map aufbauen (Basis + Gruppen + HK) ---
    register_map = build_register_map(heating_circuits, sensor_groups)
    _LOGGER.info(
        "iDM Coordinator: %d Register für HK %s, Gruppen %s",
        len(register_map),
        heating_circuits,
        sensor_groups,
    )

    # --- DataUpdateCoordinator ---
    async def _async_update_data():
        try:
            data = await client.read_all(register_map)
            return data
        except Exception as err:
            raise UpdateFailed(f"Modbus-Fehler: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"iDM W\u00e4rmepumpe ({host})",
        update_method=_async_update_data,
        update_interval=timedelta(seconds=update_interval),
    )

    await coordinator.async_config_entry_first_refresh()

    # --- Alles in hass.data ablegen ---
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
        "host": host,
        "heating_circuits": heating_circuits,
        "sensor_groups": sensor_groups,
        "update_interval": update_interval,
    }

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass, entry):
    _LOGGER.info("iDM W\u00e4rmepumpe: Options ge\u00e4ndert, Integration wird neu geladen")
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id, None)
        if entry_data and "client" in entry_data:
            await entry_data["client"].close()
            _LOGGER.info("iDM Modbus-Verbindung geschlossen")
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

    if config_entry.version == 2:
        _LOGGER.info("Migriere iDM Config von Version 2 → 3")
        new_data = {**config_entry.data}
        if CONF_SENSOR_GROUPS not in new_data:
            new_data[CONF_SENSOR_GROUPS] = DEFAULT_SENSOR_GROUPS
        hass.config_entries.async_update_entry(
            config_entry, data=new_data, version=3
        )

    return True
