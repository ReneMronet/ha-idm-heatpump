"""
iDM Wärmepumpe (Modbus TCP)
Version: v5.0
Stand: 2026-02-26

Änderungen v5.0 (Schritt 2):
- Neuer Switch: Anforderung Kühlen (Reg. 1711, Kühlungs-Gruppe)
"""

import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    DEFAULT_SENSOR_GROUPS,
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
