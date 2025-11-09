"""
iDM Wärmepumpe (Modbus TCP)
Version: v1.9
Stand: 2025-11-09

Änderungen v1.9:
- Neue Number-Entities (FLOAT): Heizkurve HK A (1429) und HK C (1433), 0.0..3.5, Schritt 0.1, Default 0.6
- Bestand: Heizgrenze HK A/C (1442/1444) und Parallelverschiebung HK A/C (1505/1507)
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
    REG_HKA_PARALLEL,
    REG_HKC_PARALLEL,
    REG_HKA_HEATLIMIT,
    REG_HKC_HEATLIMIT,
    REG_HKA_CURVE,
    REG_HKC_CURVE,
)
from .modbus_handler import IDMModbusHandler

_LOGGER = logging.getLogger(__name__)

# Register-Adressen Heizkreise (Vorlauf-Solltemperaturen, FLOAT)
REG_HKA_NORMAL = 1401
REG_HKC_NORMAL = 1405
REG_HKA_ECO    = 1415
REG_HKC_ECO    = 1419


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

        # Heizkurve Heizkreise (FLOAT 0.0..3.5)
        IDMSollTempFloatNumber("idm_hka_curve", "hka_curve", REG_HKA_CURVE,
                               0.0, 3.5, 0.1, 0.6, client, host, interval),
        IDMSollTempFloatNumber("idm_hkc_curve", "hkc_curve", REG_HKC_CURVE,
                               0.0, 3.5, 0.1, 0.6, client, host, interval),

        # Parallelverschiebung Heizkreise (UCHAR 0..30 °C)
        IDMSollTempUcharNumber("idm_hka_parallel", "hka_parallel", REG_HKA_PARALLEL,
                               0, 30, 1, 0, client, host, interval),
        IDMSollTempUcharNumber("idm_hkc_parallel", "hkc_parallel", REG_HKC_PARALLEL,
                               0, 30, 1, 0, client, host, interval),

        # Heizgrenzen Heizkreise (UCHAR 0..50 °C)
        IDMSollTempUcharNumber("idm_hka_heat_limit", "hka_heat_limit", REG_HKA_HEATLIMIT,
                               0, 50, 1, 15, client, host, interval),
        IDMSollTempUcharNumber("idm_hkc_heat_limit", "hkc_heat_limit", REG_HKC_HEATLIMIT,
                               0, 50, 1, 15, client, host, interval),

        # Warmwasser (UCHAR)
        IDMSollTempUcharNumber("idm_ww_target", "ww_target", REG_WW_TARGET,
                               30, 60, 1, 46, client, host, interval),
        IDMSollTempUcharNumber("idm_ww_start", "ww_start", REG_WW_START,
                               30, 50, 1, 46, client, host, interval),
        IDMSollTempUcharNumber("idm_ww_stop", "ww_stop", REG_WW_STOP,
                               46, 67, 1, 50, client, host, interval),
    ]

    async_add_entities(entities)


# -------------------------------------------------------------------
# FLOAT-Nummern (HK A/C Solltemperaturen, Heizkurve)
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
        self._attr_native_min_value = float(min_value)
        self._attr_native_max_value = float(max_value)
        self._attr_native_step = float(step)
        self._attr_native_value = None
        self._default = float(default)
        self._attr_scan_interval = timedelta(seconds=interval)

    async def async_update(self):
        value = await self._client.read_float(self._register)
        if value is not None:
            # 1 Nachkommastelle reicht für Heizkurve
            self._attr_native_value = round(float(value), 1)

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
# UCHAR-Nummern (WW + Parallelverschiebung + Heizgrenze)
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
        self._attr_native_min_value = int(min_value)
        self._attr_native_max_value = int(max_value)
        self._attr_native_step = int(step)
        self._attr_native_value = None
        self._default = int(default)
        self._attr_scan_interval = timedelta(seconds=interval)

    async def async_update(self):
        value = await self._client.read_uchar(self._register)
        if value is not None:
            self._attr_native_value = int(value)

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
