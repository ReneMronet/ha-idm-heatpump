"""
iDM Wärmepumpe (Modbus TCP)
Version: v0.6.0
Stand: 2026-02-26

Änderungen v0.6.0:
- Neuer Master-Switch: Raumtemperatur-Übernahme
- Reagiert auf saisonale Automatik via Event-Bus
"""

import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import callback

from .const import (
    DOMAIN,
    DEFAULT_SENSOR_GROUPS,
    DEFAULT_ROOM_TEMP_ENTITIES,
    REG_HEAT_REQUEST,
    REG_WW_REQUEST,
    REG_WW_ONETIME,
    REG_COOL_REQUEST,
    get_device_info,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    client = entry_data["client"]
    host = entry_data["host"]
    sensor_groups = entry_data.get("sensor_groups", DEFAULT_SENSOR_GROUPS)
    room_temp_entities = entry_data.get("room_temp_entities", DEFAULT_ROOM_TEMP_ENTITIES)
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

    async_add_entities(entities)


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


class IDMRoomTempMasterSwitch(CoordinatorEntity, SwitchEntity):
    """Master-Switch für die Raumtemperatur-Übernahme.

    Manuell AUS übersteuert die Saison-Automatik.
    Reagiert auf saisonale Events vom RoomTempForwarder.
    """

    _attr_has_entity_name = True
    _attr_unique_id = "idm_room_temp_master"
    _attr_translation_key = "room_temp_master"

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
        attrs["konfigurierte_hk"] = list(self._forwarder._entity_map.keys())
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

