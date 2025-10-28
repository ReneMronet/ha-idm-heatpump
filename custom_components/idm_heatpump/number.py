# Datei: number.py
"""
iDM Wärmepumpe (Modbus TCP)
Version: v1.5 (Dokumentations-Update)
Stand: 2025-09-24
"""

import logging
from datetime import timedelta
from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfTemperature
from .const import (
    DOMAIN,
    CONF_UNIT_ID,
    DEFAULT_UNIT_ID,
    REG_WW_TARGET,
    REG_WW_START,
    REG_WW_STOP,
)
from .modbus_handler import IDMModbusHandler

_LOGGER = logging.getLogger(__name__)

# Register-Adressen Heizkreise
REG_HKA_NORMAL = 1401
REG_HKC_NORMAL = 1405
REG_HKA_ECO = 1415
REG_HKC_ECO = 1419


async def async_setup_entry(hass, entry, async_add_entities):
    host = entry.data["host"]
    port = entry.data.get("port")
    unit_id = entry.data.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)
    interval = hass.data[DOMAIN][entry.entry_id]["update_interval"]

    client = IDMModbusHandler(host, port, unit_id)
    await client.connect()

    entities = [
        # Heizkreise (FLOAT)
        IDMSollTempFloatNumber("idm_hka_temp_normal", "hka_temp_normal", REG_HKA_NORMAL,
                               15, 30, 0.5, 22, client, host, interval),
        IDMSollTempFloatNumber("idm_hkc_temp_normal", "hkc_temp_normal", REG_HKC_NORMAL,
                               15, 30, 0.5, 22, client, host, interval),
        IDMSollTempFloatNumber("idm_hka_temp_eco", "hka_temp_eco", REG_HKA_ECO,
                               10, 25, 0.5, 18, client, host, interval),
        IDMSollTempFloatNumber("idm_hkc_temp_eco", "hkc_temp_eco", REG_HKC_ECO,
                               10, 25, 0.5, 18, client, host, interval),

        # Warmwasser (UCHAR)
        IDMSollTempUcharNumber("idm_ww_target", "ww_target", REG_WW_TARGET,
                               35, 60, 1, 46, client, host, interval),
        IDMSollTempUcharNumber("idm_ww_start", "ww_start", REG_WW_START,
                               30, 50, 1, 46, client, host, interval),
        IDMSollTempUcharNumber("idm_ww_stop", "ww_stop", REG_WW_STOP,
                               46, 53, 1, 50, client, host, interval),
    ]

    async_add_entities(entities)


# -------------------------------------------------------------------
# FLOAT-Nummern (HK A/C Solltemperaturen)
# -------------------------------------------------------------------
class IDMSollTempFloatNumber(NumberEntity):
    _attr_has_entity_name = True
    _attr_device_class = "temperature"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_should_poll = True

    def __init__(self, unique_id, translation_key, register, min_value, max_value, step, default, client, host, interval):
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._register = register
        self._client = client
        self._host = host
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_native_value = None
        self._default = default
        self._attr_scan_interval = timedelta(seconds=interval)

    async def async_update(self):
        value = await self._client.read_float(self._register)
        if value is not None:
            self._attr_native_value = round(value, 1)

    async def async_set_native_value(self, value: float):
        if value != self._attr_native_value:
            await self._client.write_float(self._register, float(value))
            self._attr_native_value = float(value)
            self.async_write_ha_state()

    @property
    def extra_state_attributes(self):
        return {"default_value": self._default}

    @property
    def device_info(self):
        return {
            "identifiers": {("idm_heatpump", "idm_system")},
            "name": "iDM Wärmepumpe",
            "manufacturer": "iDM Energiesysteme",
            "model": "AERO ALM 4–12",
            "configuration_url": f"http://{self._host}",
        }


# -------------------------------------------------------------------
# UCHAR-Nummern (Warmwasser-Sollwerte)
# -------------------------------------------------------------------
class IDMSollTempUcharNumber(NumberEntity):
    _attr_has_entity_name = True
    _attr_device_class = "temperature"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_should_poll = True

    def __init__(self, unique_id, translation_key, register, min_value, max_value, step, default, client, host, interval):
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._register = register
        self._client = client
        self._host = host
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_native_value = None
        self._default = default
        self._attr_scan_interval = timedelta(seconds=interval)

    async def async_update(self):
        value = await self._client.read_uchar(self._register)
        if value is not None:
            self._attr_native_value = value

    async def async_set_native_value(self, value: float):
        if value != self._attr_native_value:
            await self._client.write_uchar(self._register, int(value))
            self._attr_native_value = int(value)
            self.async_write_ha_state()

    @property
    def extra_state_attributes(self):
        return {"default_value": self._default}

    @property
    def device_info(self):
        return {
            "identifiers": {("idm_heatpump", "idm_system")},
            "name": "iDM Wärmepumpe",
            "manufacturer": "iDM Energiesysteme",
            "model": "AERO ALM 4–12",
            "configuration_url": f"http://{self._host}",
        }
