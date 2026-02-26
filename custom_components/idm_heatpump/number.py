"""
iDM Wärmepumpe (Modbus TCP)
Version: v2.0
Stand: 2026-02-26

Änderungen v2.0:
- Heizkreise A–G dynamisch über hc_reg() und Konfiguration
- Alle HC-Number-Entities (Normal, Eco, Curve, Parallel, Heizgrenze) per Schleife
"""

import logging
from datetime import timedelta
from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfTemperature

from .const import (
    DOMAIN,
    CONF_UNIT_ID,
    DEFAULT_UNIT_ID,
    CONF_HEATING_CIRCUITS,
    DEFAULT_HEATING_CIRCUITS,
    REG_WW_TARGET,
    REG_WW_START,
    REG_WW_STOP,
    hc_reg,
)
from .modbus_handler import IDMModbusHandler

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    host = entry.data["host"]
    port = entry.data.get("port")
    unit_id = entry.data.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)
    interval = hass.data[DOMAIN][entry.entry_id]["update_interval"]
    heating_circuits = hass.data[DOMAIN][entry.entry_id].get(
        "heating_circuits", DEFAULT_HEATING_CIRCUITS
    )

    client = IDMModbusHandler(host, port, unit_id)
    await client.connect()

    entities = []

    # ----------------------------------------------------------
    # Dynamische Heizkreis-Numbers (A–G, je nach Konfiguration)
    # ----------------------------------------------------------
    for hc in heating_circuits:
        key = hc.lower()
        entities.extend([
            # Solltemperatur Normal (FLOAT, 15–30 °C)
            IDMSollTempFloatNumber(
                f"idm_hk{key}_temp_normal", f"hk{key}_temp_normal",
                hc_reg(hc, "temp_normal"),
                15, 30, 0.5, 22, client, host, interval,
            ),
            # Solltemperatur Eco (FLOAT, 10–25 °C)
            IDMSollTempFloatNumber(
                f"idm_hk{key}_temp_eco", f"hk{key}_temp_eco",
                hc_reg(hc, "temp_eco"),
                10, 25, 0.5, 18, client, host, interval,
            ),
            # Heizkurve (FLOAT, 0.0–3.5)
            IDMSollTempFloatNumber(
                f"idm_hk{key}_curve", f"hk{key}_curve",
                hc_reg(hc, "curve"),
                0.0, 3.5, 0.1, 0.6, client, host, interval,
            ),
            # Parallelverschiebung (UCHAR, 0–30 °C)
            IDMSollTempUcharNumber(
                f"idm_hk{key}_parallel", f"hk{key}_parallel",
                hc_reg(hc, "parallel"),
                0, 30, 1, 0, client, host, interval,
            ),
            # Heizgrenze (UCHAR, 0–50 °C)
            IDMSollTempUcharNumber(
                f"idm_hk{key}_heat_limit", f"hk{key}_heat_limit",
                hc_reg(hc, "heat_limit"),
                0, 50, 1, 15, client, host, interval,
            ),
        ])

    # Warmwasser (unabhängig von Heizkreisen)
    entities.extend([
        IDMSollTempUcharNumber("idm_ww_target", "ww_target", REG_WW_TARGET,
                               30, 60, 1, 46, client, host, interval),
        IDMSollTempUcharNumber("idm_ww_start", "ww_start", REG_WW_START,
                               30, 50, 1, 46, client, host, interval),
        IDMSollTempUcharNumber("idm_ww_stop", "ww_stop", REG_WW_STOP,
                               46, 67, 1, 50, client, host, interval),
    ])

    async_add_entities(entities)


# -------------------------------------------------------------------
# FLOAT-Nummern (HK Solltemperaturen, Heizkurve)
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
