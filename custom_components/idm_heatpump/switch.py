"""
iDM Wärmepumpe (Modbus TCP)
Version: v0.8.0
Stand: 2026-11-11

Änderungen v0.8.0:
- Pro HK und Raumsensor ein Kippschalter „verwenden“ (merkt sich seinen
  Zustand über HA-Neustarts, Standard EIN)
- Master-Switch: Attribute hk_x_mittelwert / hk_x_verwendet (nicht im Recorder)
- FIX: Master-Switch merkt sich seinen Zustand über HA-Neustarts (RestoreEntity);
  vorher ging er nach jedem Neustart wieder auf EIN

Änderungen v0.6.0:
- Neuer Master-Switch: Raumtemperatur-Übernahme
- Reagiert auf saisonale Automatik via Event-Bus
"""

import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.core import callback

from .const import (
    DOMAIN,
    ALL_HEATING_CIRCUITS,
    DEFAULT_SENSOR_GROUPS,
    DEFAULT_ROOM_TEMP_ENTITIES,
    DEFAULT_ROOM_TEMP_SOURCES,
    REG_HEAT_REQUEST,
    REG_WW_REQUEST,
    REG_WW_ONETIME,
    REG_COOL_REQUEST,
    get_device_info,
    room_temp_source_unique_id,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    client = entry_data["client"]
    host = entry_data["host"]
    sensor_groups = entry_data.get("sensor_groups", DEFAULT_SENSOR_GROUPS)
    room_temp_entities = entry_data.get("room_temp_entities", DEFAULT_ROOM_TEMP_ENTITIES)
    room_temp_sources = entry_data.get("room_temp_sources", DEFAULT_ROOM_TEMP_SOURCES)
    forwarder = entry_data.get("room_temp_forwarder")

    entities = [
        # Basis-Switches (immer)
        IDMSwitch(coordinator, client, host,
                  "idm_heat_request", "heat_request",
                  REG_HEAT_REQUEST,
                  icon_on="mdi:radiator", icon_off="mdi:radiator-off"),
        IDMSwitch(coordinator, client, host,
                  "idm_ww_request", "ww_request",
                  REG_WW_REQUEST,
                  icon_on="mdi:water-boiler", icon_off="mdi:water-boiler-off"),
        IDMSwitch(coordinator, client, host,
                  "idm_ww_onetime", "ww_onetime",
                  REG_WW_ONETIME,
                  icon_on="mdi:water-boiler", icon_off="mdi:water-boiler-off"),
    ]

    # Kühlungs-Gruppe: Anforderung Kühlen
    if "cooling" in sensor_groups:
        entities.append(
            IDMSwitch(coordinator, client, host,
                      "idm_cool_request", "cool_request",
                      REG_COOL_REQUEST,
                      icon_on="mdi:snowflake", icon_off="mdi:snowflake-off"),
        )

    # Raumtemperatur-Master-Switch (nur wenn Entities konfiguriert)
    if room_temp_entities and forwarder:
        entities.append(
            IDMRoomTempMasterSwitch(
                hass, coordinator, host, forwarder,
            ),
        )

    # Kippschalter je HK und Raumsensor (v0.8.0)
    if room_temp_sources and forwarder:
        for hc in sorted(room_temp_sources):
            for source_id in room_temp_sources[hc]:
                entities.append(
                    IDMRoomTempSourceSwitch(
                        host, forwarder, hc, source_id,
                        _source_display_name(hass, source_id),
                    ),
                )

    async_add_entities(entities)


def _source_display_name(hass, entity_id: str) -> str:
    """Anzeigename eines Raumsensors für den Schalternamen.

    Zuerst aus der Entity-/Geräte-Registry (beim Start immer vorhanden, so
    bleibt der Name stabil), sonst friendly_name, sonst die entity_id.
    """
    entry = er.async_get(hass).async_get(entity_id)
    if entry is not None:
        name = entry.name or entry.original_name
        device_name = None
        if entry.device_id:
            device = dr.async_get(hass).async_get(entry.device_id)
            if device is not None:
                device_name = device.name_by_user or device.name
        if entry.name:
            # Vom Benutzer vergebener Name gilt so, wie er ist
            return entry.name
        if entry.has_entity_name and device_name:
            return f"{device_name} {name}" if name else device_name
        if name:
            return name
    state = hass.states.get(entity_id)
    if state is not None and state.name:
        return state.name
    return entity_id


class IDMSwitch(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, client, host,
                 unique_id, translation_key, register,
                 icon_on="mdi:toggle-switch", icon_off="mdi:toggle-switch-off"):
        super().__init__(coordinator)
        self._client = client
        self._host = host
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._register = register
        self._icon_on = icon_on
        self._icon_off = icon_off

    @property
    def device_info(self):
        return get_device_info(self._host)

    @property
    def is_on(self):
        value = self.coordinator.data.get(self._register)
        return value == 1

    async def async_turn_on(self, **kwargs):
        await self._client.write_uchar(self._register, 1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self._client.write_uchar(self._register, 0)
        await self.coordinator.async_request_refresh()

    @property
    def icon(self):
        return self._icon_on if self.is_on else self._icon_off


class IDMRoomTempMasterSwitch(CoordinatorEntity, SwitchEntity, RestoreEntity):
    """Master-Switch für die Raumtemperatur-Übernahme.

    Manuell AUS übersteuert die Saison-Automatik.
    Reagiert auf saisonale Events vom RoomTempForwarder.
    """

    _attr_has_entity_name = True
    _attr_unique_id = "idm_room_temp_master"
    _attr_translation_key = "room_temp_master"
    # Mittelwerte ändern sich laufend: nicht im Recorder speichern (Platz)
    _unrecorded_attributes = frozenset(
        f"hk_{hc.lower()}_{suffix}"
        for hc in ALL_HEATING_CIRCUITS
        for suffix in ("mittelwert", "verwendet")
    )

    def __init__(self, hass, coordinator, host, forwarder):
        super().__init__(coordinator)
        self._hass = hass
        self._host = host
        self._forwarder = forwarder
        self._is_on = forwarder.is_active
        self._unsub_event = None

    @property
    def device_info(self):
        return get_device_info(self._host)

    @property
    def is_on(self):
        return self._is_on

    @property
    def icon(self):
        return "mdi:home-thermometer" if self._is_on else "mdi:home-thermometer-outline"

    @property
    def extra_state_attributes(self):
        attrs = {}
        if self._forwarder._season_enabled:
            attrs["saisonale_automatik"] = True
            attrs["saison_start"] = f"{self._forwarder._season_start[1]:02d}.{self._forwarder._season_start[0]:02d}."
            attrs["saison_ende"] = f"{self._forwarder._season_end[1]:02d}.{self._forwarder._season_end[0]:02d}."
            attrs["innerhalb_saison"] = self._forwarder._is_in_season()
        attrs["manuell_deaktiviert"] = self._forwarder._manual_override
        attrs["konfigurierte_hk"] = list(self._forwarder.sources.keys())
        # v0.8.0: Mittelwert (vor Offset) und verwendete Sensoren je HK
        for hc in sorted(self._forwarder.sources):
            mean, used = self._forwarder.compute(hc)
            attrs[f"hk_{hc.lower()}_mittelwert"] = mean
            attrs[f"hk_{hc.lower()}_verwendet"] = used
        return attrs

    async def async_turn_on(self, **kwargs):
        self._is_on = True
        self._forwarder.set_master_switch(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._is_on = False
        self._forwarder.set_master_switch(False)
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Registriert Listener für saisonale Events."""
        await super().async_added_to_hass()

        # v0.8.0 (Fix): letzten Zustand nach einem Neustart übernehmen.
        # Ohne das startet die Weiterleitung immer mit EIN, auch wenn der Schalter vorher AUS war.
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state == "off" and self._is_on:
            self._is_on = False
            self._forwarder.set_master_switch(False)

        @callback
        def _handle_season_event(event):
            self._is_on = event.data.get("active", False)
            self.async_write_ha_state()

        self._unsub_event = self._hass.bus.async_listen(
            f"{DOMAIN}_room_temp_season_changed",
            _handle_season_event,
        )

    async def async_will_remove_from_hass(self):
        """Entfernt Event-Listener."""
        if self._unsub_event:
            self._unsub_event()


class IDMRoomTempSourceSwitch(SwitchEntity, RestoreEntity):
    """Kippschalter „Sensor verwenden“ je HK und Raumsensor (v0.8.0).

    EIN: Der Sensor zählt zum Mittelwert, der an die WP geht.
    AUS: Der Sensor wird für diesen HK ignoriert.
    Merkt sich seinen Zustand über HA-Neustarts, neu angelegt steht er auf EIN.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, host, forwarder, hc, source_entity_id, source_name):
        self._host = host
        self._forwarder = forwarder
        self._hc = hc
        self._source_entity_id = source_entity_id
        self._attr_unique_id = room_temp_source_unique_id(hc, source_entity_id)
        self._attr_name = f"HK {hc} · {source_name}"

    @property
    def device_info(self):
        return get_device_info(self._host)

    @property
    def is_on(self):
        return self._forwarder.is_source_enabled(self._hc, self._source_entity_id)

    @property
    def icon(self):
        return "mdi:thermometer-check" if self.is_on else "mdi:thermometer-off"

    @property
    def extra_state_attributes(self):
        return {
            "heizkreis": self._hc,
            "sensor": self._source_entity_id,
        }

    async def async_turn_on(self, **kwargs):
        self._forwarder.set_source_enabled(self._hc, self._source_entity_id, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._forwarder.set_source_enabled(self._hc, self._source_entity_id, False)
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Letzten Zustand nach einem Neustart übernehmen (ohne zu schreiben)."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state == "off":
            self._forwarder.set_source_enabled(
                self._hc, self._source_entity_id, False, write=False
            )

