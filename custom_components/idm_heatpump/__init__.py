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
from homeassistant.helpers import entity_registry as er
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


def build_expected_unique_ids(
    heating_circuits: list[str],
    sensor_groups: list[str],
) -> set[str]:
    """Erzeugt die Menge aller unique_ids, die bei der aktuellen Konfiguration
    existieren sollen. Wird zum Aufräumen verwaister Entitäten verwendet."""

    ids: set[str] = set()

    # --- Basis-Sensoren (immer) ---
    ids.update([
        "idm_aussentemperatur", "idm_aussentemperatur_gemittelt",
        "idm_wp_vorlauf", "idm_ruecklauf", "idm_ladefuehler",
        "idm_durchfluss", "idm_luftansaug", "idm_luftansaug_2",
        "idm_waermespeicher", "idm_ww_oben", "idm_ww_unten",
        "idm_ww_zapftemp", "idm_interne_meldung",
        "idm_betriebsart_warmepumpe", "idm_status_warmepumpe",
        "idm_wp_power", "idm_thermische_leistung",
        "idm_en_heizen", "idm_en_gesamt", "idm_en_kuehlen",
        "idm_en_warmwasser", "idm_en_abtauung", "idm_en_passivkuehlung",
        "idm_en_solar", "idm_en_eheizer",
    ])

    # --- Basis-Numbers (immer) ---
    ids.update(["idm_ww_target", "idm_ww_start", "idm_ww_stop"])

    # --- Basis-Selects (immer) ---
    ids.add("idm_betriebsart")

    # --- Basis-Switches (immer) ---
    ids.update(["idm_heat_request", "idm_ww_request", "idm_ww_onetime"])

    # --- Pro Heizkreis (immer) ---
    for hc in heating_circuits:
        key = hc.lower()
        # Sensoren
        ids.update([
            f"idm_hk{key}_vorlauftemperatur",
            f"idm_hk{key}_soll_vorlauf",
            f"idm_hk{key}_aktive_betriebsart",
        ])
        # Numbers
        ids.update([
            f"idm_hk{key}_temp_normal",
            f"idm_hk{key}_temp_eco",
            f"idm_hk{key}_curve",
            f"idm_hk{key}_parallel",
            f"idm_hk{key}_heat_limit",
        ])
        # Selects
        ids.add(f"idm_hk{key}_betriebsart")

    # --- Solar-Gruppe ---
    if "solar" in sensor_groups:
        ids.update([
            "idm_solar_kollektor", "idm_solar_ruecklauf",
            "idm_solar_ladetemp", "idm_solar_leistung",
            "idm_solar_betriebsart",
        ])

    # --- PV/Batterie-Gruppe ---
    if "pv_battery" in sensor_groups:
        ids.update([
            "idm_pv_ueberschuss", "idm_e_heizstab",
            "idm_pv_produktion", "idm_hausverbrauch",
            "idm_batterie_entladung", "idm_batterie_fuellstand",
            "idm_smartgrid_status", "idm_strompreis",
            "idm_pv_zielwert",
        ])

    # --- Kühlungs-Gruppe ---
    if "cooling" in sensor_groups:
        ids.update([
            "idm_kuehlanforderung_wp", "idm_ww_anforderung_wp",
            "idm_cool_request",
        ])
        for hc in heating_circuits:
            key = hc.lower()
            ids.update([
                f"idm_hk{key}_cool_normal",
                f"idm_hk{key}_cool_eco",
                f"idm_hk{key}_cool_limit",
                f"idm_hk{key}_cool_vl",
            ])

    # --- Diagnose-Gruppe ---
    if "diagnostic" in sensor_groups:
        ids.update([
            "idm_summenstoerung", "idm_evu_sperre",
            "idm_verdichter_1", "idm_ladepumpe",
            "idm_variabler_eingang", "idm_umschaltventil",
            "idm_zirkulationspumpe", "idm_leistungsbegrenzung",
        ])

    # --- Einzelraumregelung-Gruppe ---
    if "room_control" in sensor_groups:
        ids.add("idm_feuchtesensor")
        for hc in heating_circuits:
            key = hc.lower()
            ids.add(f"idm_hk{key}_raumtemperatur")

    # --- Erweiterte Temperaturen-Gruppe ---
    if "extended_temps" in sensor_groups:
        ids.update([
            "idm_luftwaermetauscher", "idm_waermesenke_ruecklauf",
            "idm_waermesenke_vorlauf", "idm_kaeltespeicher",
        ])

    return ids


async def _async_cleanup_entities(hass, entry, heating_circuits, sensor_groups):
    """Entfernt verwaiste Entitäten, die nicht mehr zur Konfiguration gehören."""
    registry = er.async_get(hass)
    expected = build_expected_unique_ids(heating_circuits, sensor_groups)

    entries = er.async_entries_for_config_entry(registry, entry.entry_id)
    removed = 0
    for entity_entry in entries:
        if entity_entry.unique_id not in expected:
            _LOGGER.info(
                "Entferne verwaiste Entität: %s (unique_id: %s)",
                entity_entry.entity_id,
                entity_entry.unique_id,
            )
            registry.async_remove(entity_entry.entity_id)
            removed += 1

    if removed:
        _LOGGER.info("iDM Cleanup: %d verwaiste Entität(en) entfernt", removed)


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

    # Verwaiste Entitäten aufräumen (z.B. nach Deaktivierung von HK/Gruppen)
    await _async_cleanup_entities(hass, entry, heating_circuits, sensor_groups)

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
