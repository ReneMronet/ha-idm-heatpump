"""
iDM Wärmepumpe (Modbus TCP)
Version: v0.7.0
Stand: 2026-02-26

Änderungen v0.7.0:
- Temperatur-Offset pro HK (Number-Entity, ±5°C)
- Schreib-Intervall: "Deaktiviert" als Standard + Handling
- Migration v4→v5

Änderungen v0.6.0:
- RoomTempForwarder: Externe Raumtemperaturen → WP (Register 1650+)
- Master-Switch "Raumtemperatur-Übernahme" mit Saison-Automatik
- EEPROM-Schutz: nur bei Änderung >0.1°C schreiben
- Migration v3→v4: room_temp defaults
"""

import logging
from datetime import timedelta, date, time, datetime

from homeassistant.const import (
    Platform,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
    async_track_time_change,
)
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
    CONF_ROOM_TEMP_ENTITIES,
    CONF_ROOM_TEMP_INTERVAL,
    CONF_ROOM_TEMP_SEASON_ENABLED,
    CONF_ROOM_TEMP_SEASON_START_MONTH,
    CONF_ROOM_TEMP_SEASON_START_DAY,
    CONF_ROOM_TEMP_SEASON_END_MONTH,
    CONF_ROOM_TEMP_SEASON_END_DAY,
    DEFAULT_ROOM_TEMP_ENTITIES,
    DEFAULT_ROOM_TEMP_INTERVAL,
    DEFAULT_ROOM_TEMP_SEASON_ENABLED,
    DEFAULT_ROOM_TEMP_SEASON_START_MONTH,
    DEFAULT_ROOM_TEMP_SEASON_START_DAY,
    DEFAULT_ROOM_TEMP_SEASON_END_MONTH,
    DEFAULT_ROOM_TEMP_SEASON_END_DAY,
    CONF_ROOM_TEMP_OFFSETS,
    DEFAULT_ROOM_TEMP_OFFSETS,
    ROOM_TEMP_OFFSET_DEFAULT,
    ROOM_TEMP_WRITE_TOLERANCE,
    ROOM_TEMP_NO_SENSOR,
    hc_room_temp_write_reg,
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


# ===================================================================
# RoomTempForwarder – Externe Raumtemperaturen → WP
# ===================================================================

class RoomTempForwarder:
    """Leitet Raumtemperaturen von HA-Sensoren an die Wärmepumpe weiter.

    Features:
    - Schreib-Intervall: bei State-Änderung, Timer (5–60 Min.) oder Deaktiviert
    - Temperatur-Offset pro HK: Wert wird vor dem Schreiben addiert (v0.7.0)
    - EEPROM-Schutz: nur bei Differenz > 0.1°C schreiben
    - Offline-Erkennung: -1.0 schreiben wenn Sensor unavailable
    - Saisonale Automatik: aktiv nur innerhalb Saison-Zeitraum
    - Master-Switch: manuell AUS übersteuert Saison-Automatik
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: IDMModbusHandler,
        entity_map: dict[str, str],
        interval: str,
        season_enabled: bool,
        season_start: tuple[int, int],
        season_end: tuple[int, int],
    ):
        self._hass = hass
        self._client = client
        self._entity_map = entity_map  # {"A": "sensor.xxx", "C": "sensor.yyy"}
        self._interval = interval
        self._season_enabled = season_enabled
        self._season_start = season_start  # (month, day)
        self._season_end = season_end      # (month, day)

        self._last_written: dict[str, float | None] = {}
        self._unsub_listeners: list = []
        self._master_switch_on = True
        self._manual_override = False  # True wenn manuell ausgeschaltet
        self._offsets: dict[str, float] = {}  # {"A": -2.0, "C": 1.5}

    def get_offset(self, hc: str) -> float:
        """Liefert den aktuellen Offset für einen Heizkreis."""
        return self._offsets.get(hc, ROOM_TEMP_OFFSET_DEFAULT)

    def set_offset(self, hc: str, value: float):
        """Setzt den Offset für einen Heizkreis und triggert Neuschreibung."""
        old = self._offsets.get(hc, ROOM_TEMP_OFFSET_DEFAULT)
        self._offsets[hc] = value
        _LOGGER.info(
            "Raumtemperatur-Offset HK %s: %.1f → %.1f°C",
            hc, old, value,
        )
        # Wert mit neuem Offset sofort neu schreiben
        if self.is_active and hc in self._entity_map:
            self._last_written.pop(hc, None)  # Cache invalidieren
            state = self._hass.states.get(self._entity_map[hc])
            state_value = state.state if state else STATE_UNAVAILABLE
            self._hass.async_create_task(
                self._write_single(hc, state_value)
            )

    @property
    def is_active(self) -> bool:
        """Prüft ob die Weiterleitung aktiv sein soll."""
        if self._manual_override:
            return False
        if self._season_enabled:
            return self._is_in_season()
        return self._master_switch_on

    def _is_in_season(self) -> bool:
        """Prüft ob das aktuelle Datum innerhalb der Saison liegt."""
        today = date.today()
        start = date(today.year, self._season_start[0], self._season_start[1])
        end = date(today.year, self._season_end[0], self._season_end[1])

        if start <= end:
            # Saison innerhalb eines Jahres (z.B. März–Oktober)
            return start <= today <= end
        else:
            # Saison über Jahreswechsel (z.B. Oktober–April)
            return today >= start or today <= end

    def set_master_switch(self, is_on: bool):
        """Wird vom Master-Switch aufgerufen."""
        if is_on:
            self._master_switch_on = True
            self._manual_override = False
            _LOGGER.info("Raumtemperatur-Übernahme: Master-Switch EIN")
        else:
            self._master_switch_on = False
            self._manual_override = True
            _LOGGER.info("Raumtemperatur-Übernahme: Master-Switch AUS (manuell)")
            self._hass.async_create_task(self._write_all_inactive())

    async def async_start(self):
        """Startet die Listener/Timer."""
        if not self._entity_map:
            _LOGGER.debug("Raumtemperatur-Übernahme: Keine Sensoren konfiguriert")
            return

        if self._interval == "disabled":
            _LOGGER.info(
                "Raumtemperatur-Übernahme: Deaktiviert (Sensoren konfiguriert, aber Intervall=Deaktiviert)"
            )
            return

        # Tägliche Saison-Prüfung um Mitternacht
        if self._season_enabled:
            self._unsub_listeners.append(
                async_track_time_change(
                    self._hass, self._async_season_check,
                    hour=0, minute=0, second=30,
                )
            )

        if self._interval == "on_change":
            # State-Change-Listener
            entity_ids = list(self._entity_map.values())
            self._unsub_listeners.append(
                async_track_state_change_event(
                    self._hass, entity_ids, self._async_state_changed
                )
            )
            _LOGGER.info(
                "Raumtemperatur-Übernahme: Listener für %d Sensoren gestartet",
                len(entity_ids),
            )
        else:
            # Timer-basiert
            seconds = int(self._interval)
            self._unsub_listeners.append(
                async_track_time_interval(
                    self._hass,
                    self._async_timer_tick,
                    timedelta(seconds=seconds),
                )
            )
            _LOGGER.info(
                "Raumtemperatur-Übernahme: Timer alle %d Sekunden gestartet",
                seconds,
            )

        # Initialer Schreibvorgang
        if self.is_active:
            await self._write_all_active()
        else:
            await self._write_all_inactive()

    async def async_stop(self):
        """Stoppt alle Listener/Timer und schreibt -1.0."""
        for unsub in self._unsub_listeners:
            unsub()
        self._unsub_listeners.clear()
        await self._write_all_inactive()
        _LOGGER.info("Raumtemperatur-Übernahme: Gestoppt")

    @callback
    def _async_state_changed(self, event):
        """Callback bei State-Änderung eines Quell-Sensors."""
        if not self.is_active:
            return
        entity_id = event.data.get("entity_id")
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        # Finde den zugehörigen Heizkreis
        for hc, eid in self._entity_map.items():
            if eid == entity_id:
                self._hass.async_create_task(
                    self._write_single(hc, new_state.state)
                )
                break

    async def _async_timer_tick(self, now=None):
        """Timer-Callback: Alle konfigurierten Werte schreiben."""
        if self.is_active:
            await self._write_all_active()

    async def _async_season_check(self, now=None):
        """Tägliche Saison-Prüfung um Mitternacht."""
        if self._manual_override:
            _LOGGER.debug("Raumtemperatur-Übernahme: Saison-Check übersprungen (manuell AUS)")
            return

        in_season = self._is_in_season()
        was_on = self._master_switch_on

        if in_season and not was_on:
            _LOGGER.info("Raumtemperatur-Übernahme: Saison gestartet – aktiviere")
            self._master_switch_on = True
            await self._write_all_active()
            # Switch-State aktualisieren
            self._hass.bus.async_fire(
                f"{DOMAIN}_room_temp_season_changed",
                {"active": True},
            )
        elif not in_season and was_on:
            _LOGGER.info("Raumtemperatur-Übernahme: Saison beendet – deaktiviere")
            self._master_switch_on = False
            await self._write_all_inactive()
            self._hass.bus.async_fire(
                f"{DOMAIN}_room_temp_season_changed",
                {"active": False},
            )

    async def _write_single(self, hc: str, state_value: str):
        """Schreibt einen einzelnen Temperaturwert mit EEPROM-Schutz und Offset."""
        register = hc_room_temp_write_reg(hc)

        if state_value in (STATE_UNAVAILABLE, STATE_UNKNOWN, None, ""):
            await self._write_if_changed(hc, register, ROOM_TEMP_NO_SENSOR)
            return

        try:
            temp = round(float(state_value), 1)
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Raumtemperatur HK %s: Ungültiger Wert '%s' von %s",
                hc, state_value, self._entity_map.get(hc),
            )
            return

        # Offset anwenden (v0.7.0)
        offset = self.get_offset(hc)
        adjusted_temp = round(temp + offset, 1)

        if offset != 0.0:
            _LOGGER.debug(
                "Raumtemperatur HK %s: %.1f°C + Offset %.1f°C = %.1f°C",
                hc, temp, offset, adjusted_temp,
            )

        await self._write_if_changed(hc, register, adjusted_temp)

    async def _write_if_changed(self, hc: str, register: int, value: float):
        """Schreibt nur wenn Differenz > Toleranz (EEPROM-Schutz)."""
        last = self._last_written.get(hc)

        if last is not None:
            if abs(value - last) <= ROOM_TEMP_WRITE_TOLERANCE:
                return

        try:
            await self._client.write_float(register, value)
            self._last_written[hc] = value
            _LOGGER.debug(
                "Raumtemperatur HK %s: %.1f°C → Register %d",
                hc, value, register,
            )
        except Exception as e:
            _LOGGER.error(
                "Raumtemperatur HK %s: Schreibfehler Register %d: %s",
                hc, register, e,
            )

    async def _write_all_active(self):
        """Liest alle konfigurierten Sensoren und schreibt die Werte."""
        for hc, entity_id in self._entity_map.items():
            state = self._hass.states.get(entity_id)
            state_value = state.state if state else STATE_UNAVAILABLE
            await self._write_single(hc, state_value)

    async def _write_all_inactive(self):
        """Schreibt -1.0 in alle konfigurierten Register."""
        for hc in self._entity_map:
            register = hc_room_temp_write_reg(hc)
            await self._write_if_changed(hc, register, ROOM_TEMP_NO_SENSOR)
        _LOGGER.info("Raumtemperatur-Übernahme: -1.0 in alle Register geschrieben")


# ===================================================================
# Entity Cleanup
# ===================================================================

def build_expected_unique_ids(
    heating_circuits: list[str],
    sensor_groups: list[str],
    room_temp_entities: dict | None = None,
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

    # --- Raumtemperatur-Master-Switch (wenn Entities konfiguriert) ---
    if room_temp_entities:
        ids.add("idm_room_temp_master")
        # Offset Number-Entities pro konfiguriertem HK (v0.7.0)
        for hc in room_temp_entities:
            key = hc.lower()
            ids.add(f"idm_hk{key}_room_temp_offset")

    # --- Pro Heizkreis (immer) ---
    for hc in heating_circuits:
        key = hc.lower()
        ids.update([
            f"idm_hk{key}_vorlauftemperatur",
            f"idm_hk{key}_soll_vorlauf",
            f"idm_hk{key}_aktive_betriebsart",
        ])
        ids.update([
            f"idm_hk{key}_temp_normal",
            f"idm_hk{key}_temp_eco",
            f"idm_hk{key}_curve",
            f"idm_hk{key}_parallel",
            f"idm_hk{key}_heat_limit",
        ])
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


async def _async_cleanup_entities(hass, entry, heating_circuits, sensor_groups, room_temp_entities):
    """Entfernt verwaiste Entitäten, die nicht mehr zur Konfiguration gehören."""
    registry = er.async_get(hass)
    expected = build_expected_unique_ids(heating_circuits, sensor_groups, room_temp_entities)

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


# ===================================================================
# Hilfsfunktion: Config/Options auslesen
# ===================================================================

def _get_config(entry, key, default=None):
    """Holt einen Wert aus options → data → default."""
    return entry.options.get(key, entry.data.get(key, default))


# ===================================================================
# Setup / Unload
# ===================================================================

async def async_setup_entry(hass, entry):
    hass.data.setdefault(DOMAIN, {})

    # --- Konfiguration auslesen ---
    host = entry.data["host"]
    port = entry.data.get("port", 502)
    unit_id = entry.data.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)

    update_interval = _get_config(entry, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    heating_circuits = _get_config(entry, CONF_HEATING_CIRCUITS, DEFAULT_HEATING_CIRCUITS)
    sensor_groups = _get_config(entry, CONF_SENSOR_GROUPS, DEFAULT_SENSOR_GROUPS)

    # Raumtemperatur-Übernahme Konfiguration
    room_temp_entities = _get_config(entry, CONF_ROOM_TEMP_ENTITIES, DEFAULT_ROOM_TEMP_ENTITIES)
    room_temp_interval = _get_config(entry, CONF_ROOM_TEMP_INTERVAL, DEFAULT_ROOM_TEMP_INTERVAL)
    room_temp_offsets = _get_config(entry, CONF_ROOM_TEMP_OFFSETS, DEFAULT_ROOM_TEMP_OFFSETS)
    season_enabled = _get_config(entry, CONF_ROOM_TEMP_SEASON_ENABLED, DEFAULT_ROOM_TEMP_SEASON_ENABLED)
    season_start = (
        _get_config(entry, CONF_ROOM_TEMP_SEASON_START_MONTH, DEFAULT_ROOM_TEMP_SEASON_START_MONTH),
        _get_config(entry, CONF_ROOM_TEMP_SEASON_START_DAY, DEFAULT_ROOM_TEMP_SEASON_START_DAY),
    )
    season_end = (
        _get_config(entry, CONF_ROOM_TEMP_SEASON_END_MONTH, DEFAULT_ROOM_TEMP_SEASON_END_MONTH),
        _get_config(entry, CONF_ROOM_TEMP_SEASON_END_DAY, DEFAULT_ROOM_TEMP_SEASON_END_DAY),
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

    # --- RoomTempForwarder erstellen ---
    forwarder = None
    if room_temp_entities:
        forwarder = RoomTempForwarder(
            hass=hass,
            client=client,
            entity_map=room_temp_entities,
            interval=room_temp_interval,
            season_enabled=season_enabled,
            season_start=season_start,
            season_end=season_end,
        )

    # --- Alles in hass.data ablegen ---
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
        "host": host,
        "heating_circuits": heating_circuits,
        "sensor_groups": sensor_groups,
        "update_interval": update_interval,
        "room_temp_entities": room_temp_entities,
        "room_temp_forwarder": forwarder,
        "room_temp_offsets": room_temp_offsets,
    }

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # RoomTempForwarder starten (nach Platform-Setup, damit Switch existiert)
    if forwarder:
        await forwarder.async_start()

    # Verwaiste Entitäten aufräumen
    await _async_cleanup_entities(hass, entry, heating_circuits, sensor_groups, room_temp_entities)

    return True


async def _async_update_listener(hass, entry):
    _LOGGER.info("iDM W\u00e4rmepumpe: Options ge\u00e4ndert, Integration wird neu geladen")
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry):
    # Forwarder stoppen
    entry_data = hass.data[DOMAIN].get(entry.entry_id, {})
    forwarder = entry_data.get("room_temp_forwarder")
    if forwarder:
        await forwarder.async_stop()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id, None)
        if entry_data and "client" in entry_data:
            await entry_data["client"].close()
            _LOGGER.info("iDM Modbus-Verbindung geschlossen")
    return unload_ok


# ===================================================================
# Migration
# ===================================================================

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

    if config_entry.version == 3:
        _LOGGER.info("Migriere iDM Config von Version 3 → 4")
        new_data = {**config_entry.data}
        new_data.setdefault(CONF_ROOM_TEMP_ENTITIES, DEFAULT_ROOM_TEMP_ENTITIES)
        new_data.setdefault(CONF_ROOM_TEMP_INTERVAL, DEFAULT_ROOM_TEMP_INTERVAL)
        new_data.setdefault(CONF_ROOM_TEMP_SEASON_ENABLED, DEFAULT_ROOM_TEMP_SEASON_ENABLED)
        new_data.setdefault(CONF_ROOM_TEMP_SEASON_START_MONTH, DEFAULT_ROOM_TEMP_SEASON_START_MONTH)
        new_data.setdefault(CONF_ROOM_TEMP_SEASON_START_DAY, DEFAULT_ROOM_TEMP_SEASON_START_DAY)
        new_data.setdefault(CONF_ROOM_TEMP_SEASON_END_MONTH, DEFAULT_ROOM_TEMP_SEASON_END_MONTH)
        new_data.setdefault(CONF_ROOM_TEMP_SEASON_END_DAY, DEFAULT_ROOM_TEMP_SEASON_END_DAY)
        hass.config_entries.async_update_entry(
            config_entry, data=new_data, version=4
        )

    if config_entry.version == 4:
        _LOGGER.info("Migriere iDM Config von Version 4 → 5")
        new_data = {**config_entry.data}
        new_data.setdefault(CONF_ROOM_TEMP_OFFSETS, DEFAULT_ROOM_TEMP_OFFSETS)
        # Bestehende Installationen mit on_change behalten ihre Einstellung
        hass.config_entries.async_update_entry(
            config_entry, data=new_data, version=5
        )

    return True
