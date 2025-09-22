"""
switch.py – v1.4 (2025-09-22)

Schalter-Definitionen für iDM Wärmepumpe.
- Nutzt update_interval aus hass.data[DOMAIN][entry_id]
"""

import logging
from datetime import timedelta
from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN, REG_HEAT_REQUEST, REG_WW_REQUEST, REG_WW_ONETIME, CONF_UNIT_ID, DEFAULT_UNIT_ID
from .modbus_handler import IDMModbusHandler

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    host = entry.data["host"]
    port = entry.data.get("port")
    unit_id = entry.data.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)

    # Update-Intervall aus hass.data holen
    interval = hass.data[DOMAIN][entry.entry_id]["update_interval"]

    client = IDMModbusHandler(host, port, unit_id)
    await client.connect()

    async_add_entities([
        IDMHeatpumpHeatSwitch("idm_heat_request", "heat_request", REG_HEAT_REQUEST, client, host, interval),
        IDMHeatpumpWWSwitch("idm_ww_request", "ww_request", REG_WW_REQUEST, client, host, interval),
        IDMHeatpumpWWOnetimeSwitch("idm_ww_onetime", "ww_onetime", REG_WW_ONETIME, client, host, interval),
    ])


class IDMHeatpumpHeatSwitch(SwitchEntity):
    """Schalter für Heizungsanforderung."""
    _attr_has_entity_name = True

    def __init__(self, unique_id, translation_key, register, client, host, interval):
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._register = register
        self._client = client
        self._host = host
        self._is_on = False
        self._attr_scan_interval = timedelta(seconds=interval)

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


class IDMHeatpumpWWSwitch(IDMHeatpumpHeatSwitch):
    """Schalter für Warmwasseranforderung."""

    @property
    def icon(self):
        return "mdi:water-boiler" if self._is_on else "mdi:water-boiler-off"


class IDMHeatpumpWWOnetimeSwitch(IDMHeatpumpHeatSwitch):
    """Schalter für einmalige Warmwasserladung."""

    @property
    def icon(self):
        return "mdi:water-boiler" if self._is_on else "mdi:water-boiler-off"
