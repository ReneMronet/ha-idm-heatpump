"""
switch.py – v1.3 (2025-09-22)

Schalter-Definitionen für iDM Wärmepumpe.
"""

import logging
from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN, REG_HEAT_REQUEST, REG_WW_REQUEST, REG_WW_ONETIME, CONF_UNIT_ID, DEFAULT_UNIT_ID
from .modbus_handler import IDMModbusHandler

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    host = entry.data["host"]
    port = entry.data.get("port")
    unit_id = entry.data.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)

    client = IDMModbusHandler(host, port, unit_id)
    await client.connect()

    async_add_entities([
        IDMHeatpumpHeatSwitch("idm_heat_request", "heat_request", REG_HEAT_REQUEST, client, host),
        IDMHeatpumpWWSwitch("idm_ww_request", "ww_request", REG_WW_REQUEST, client, host),
        IDMHeatpumpWWOnetimeSwitch("idm_ww_onetime", "ww_onetime", REG_WW_ONETIME, client, host),
    ])


class IDMHeatpumpHeatSwitch(SwitchEntity):
    """Schalter für Heizungsanforderung."""
    _attr_has_entity_name = True

    def __init__(self, unique_id, translation_key, register, client, host):
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._register = register
        self._client = client
        self._host = host
        self._is_on = False

    async def async_update(self):
        value = await self._client.read_uchar(self._register)
        self._is_on = value == 1

    async def async_turn_on(self, **kwargs):
        await self._client.write_uchar(self._register, 1)
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self._client.write_uchar(self._register, 0)
        self._is_on = False
        self.async_write_ha_state()

    @property
    def is_on(self):
        return self._is_on

    @property
    def icon(self):
        return "mdi:radiator" if self._is_on else "mdi:radiator-off"

    @property
    def device_info(self):
        return {
            "identifiers": {("idm_heatpump", "idm_system")},
            "name": "iDM Wärmepumpe",
            "manufacturer": "iDM Energiesysteme",
            "model": "AERO ALM 4–12",
            "configuration_url": f"http://{self._host}",
        }


class IDMHeatpumpWWSwitch(SwitchEntity):
    """Schalter für Warmwasseranforderung."""
    _attr_has_entity_name = True

    def __init__(self, unique_id, translation_key, register, client, host):
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._register = register
        self._client = client
        self._host = host
        self._is_on = False

    async def async_update(self):
        value = await self._client.read_uchar(self._register)
        self._is_on = value == 1

    async def async_turn_on(self, **kwargs):
        await self._client.write_uchar(self._register, 1)
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self._client.write_uchar(self._register, 0)
        self._is_on = False
        self.async_write_ha_state()

    @property
    def is_on(self):
        return self._is_on

    @property
    def icon(self):
        return "mdi:water-boiler" if self._is_on else "mdi:water-boiler-off"

    @property
    def device_info(self):
        return {
            "identifiers": {("idm_heatpump", "idm_system")},
            "name": "iDM Wärmepumpe",
            "manufacturer": "iDM Energiesysteme",
            "model": "AERO ALM 4–12",
            "configuration_url": f"http://{self._host}",
        }


class IDMHeatpumpWWOnetimeSwitch(SwitchEntity):
    """Schalter für einmalige Warmwasserladung."""
    _attr_has_entity_name = True

    def __init__(self, unique_id, translation_key, register, client, host):
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._register = register
        self._client = client
        self._host = host
        self._is_on = False

    async def async_update(self):
        value = await self._client.read_uchar(self._register)
        self._is_on = value == 1

    async def async_turn_on(self, **kwargs):
        await self._client.write_uchar(self._register, 1)
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self._client.write_uchar(self._register, 0)
        self._is_on = False
        self.async_write_ha_state()

    @property
    def is_on(self):
        return self._is_on

    @property
    def icon(self):
        return "mdi:water-boiler" if self._is_on else "mdi:water-boiler-off"

    @property
    def device_info(self):
        return {
            "identifiers": {("idm_heatpump", "idm_system")},
            "name": "iDM Wärmepumpe",
            "manufacturer": "iDM Energiesysteme",
            "model": "AERO ALM 4–12",
            "configuration_url": f"http://{self._host}",
        }
