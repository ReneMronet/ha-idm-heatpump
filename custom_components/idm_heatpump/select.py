"""
select.py – v1.10 (2025-09-23)

Dropdowns für die Betriebsarten:
- System (1005)
- Heizkreis A (1393)
- Heizkreis C (1395)
- Solar (1856)
"""

import logging
from datetime import timedelta
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import EntityCategory
from .const import (
    DOMAIN,
    REG_SYSTEM_MODE,
    REG_HKA_MODE,
    REG_HKC_MODE,
    REG_SOLAR_MODE,
    CONF_UNIT_ID,
    DEFAULT_UNIT_ID,
)
from .modbus_handler import IDMModbusHandler

_LOGGER = logging.getLogger(__name__)

SYSTEM_OPTIONS = {
    "Standby": 0,
    "Automatik": 1,
    "Abwesend": 2,
    "Nur Warmwasser": 4,
    "Nur Heizen/Kühlen": 5,
}

HK_OPTIONS = {
    "Aus": 0,
    "Zeitprogramm": 1,
    "Normal": 2,
    "Eco": 3,
    "Manuell Heizen": 4,
    "Manuell Kühlen": 5,
}

SOLAR_OPTIONS = {
    "Automatik": 0,
    "Warmwasser": 1,
    "Heizung": 2,
    "Warmwasser + Heizung": 3,
    "Wärmequelle / Pool": 4,
}


async def async_setup_entry(hass, entry, async_add_entities):
    host = entry.data["host"]
    port = entry.data.get("port")
    unit_id = entry.data.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)
    interval = hass.data[DOMAIN][entry.entry_id]["update_interval"]

    client = IDMModbusHandler(host, port, unit_id)
    await client.connect()

    async_add_entities(
        [
            _ModeSelect(
                unique_id="idm_betriebsart",
                translation_key="betriebsart",
                client=client,
                host=host,
                register=REG_SYSTEM_MODE,
                options_map=SYSTEM_OPTIONS,
                interval=interval,
            ),
            _ModeSelect(
                unique_id="idm_hka_betriebsart",
                translation_key="hka_betriebsart",
                client=client,
                host=host,
                register=REG_HKA_MODE,
                options_map=HK_OPTIONS,
                interval=interval,
            ),
            _ModeSelect(
                unique_id="idm_hkc_betriebsart",
                translation_key="hkc_betriebsart",
                client=client,
                host=host,
                register=REG_HKC_MODE,
                options_map=HK_OPTIONS,
                interval=interval,
            ),
            _ModeSelect(
                unique_id="idm_solar_betriebsart",
                translation_key="solar_betriebsart",
                client=client,
                host=host,
                register=REG_SOLAR_MODE,
                options_map=SOLAR_OPTIONS,
                interval=interval,
            ),
        ]
    )


class _ModeSelect(SelectEntity):
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True

    def __init__(self, unique_id, translation_key, client, host, register, options_map, interval):
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._client = client
        self._host = host
        self._register = register
        self._options_map = options_map
        self._current_value = None
        self._attr_scan_interval = timedelta(seconds=interval)

    @property
    def options(self):
        return list(self._options_map.keys())

    @property
    def current_option(self):
        return self._current_value

    async def async_update(self):
        value = await self._client.read_uchar(self._register)
        if value is not None:
            for name, code in self._options_map.items():
                if code == value:
                    self._current_value = name
                    break

    async def async_select_option(self, option: str):
        code = self._options_map.get(option)
        if code is not None:
            await self._client.write_uchar(self._register, code)
            self._current_value = option
            self.async_write_ha_state()

    @property
    def device_info(self):
        return {
            "identifiers": {("idm_heatpump", "idm_system")},
            "name": "iDM Wärmepumpe",
            "manufacturer": "iDM Energiesysteme",
            "model": "AERO ALM 4–12",
            "configuration_url": f"http://{self._host}",
        }
