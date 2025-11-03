# Datei: select.py
"""
iDM Wärmepumpe (Modbus TCP)
Version: v1.6
Stand: 2025-11-03

Änderungen v1.6:
- Dynamisches Icon je nach Betriebsart für Reg. 1005.
- Hinweis-Attribut unverändert.
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
    "Urlaub": 3,
    "Nur Warmwasser": 4,
    "Nur Heizen/Kühlen": 5,
}

# Hinweis-Texte für die Systembetriebsart
SYSTEM_INFO = {
    "Standby": "Gerät auf Standby. Frostschutz ist aktiv.",
    "Automatik": "Bei Einstellung „Automatik“ läuft das System nach den eingestellten Heiz-, Kühl- und Warmwasserladezeiten.",
    "Abwesend": "Bei Einstellung „Abwesend“ läuft das System im Eco-Betrieb. Räume mit Eco-Temperatur. Warmwasser gemäß eingestellten Ladezeiten.",
    "Urlaub": "Bei Einstellung „Urlaub“ läuft das System für Heizen und Kühlen im Eco-Betrieb. Die Warmwasserladung kann ein-/ausgeschaltet werden.",
    "Nur Warmwasser": "Bei der Einstellung „Nur Warmwasser“ läuft die Wärmepumpe nur für Warmwasserladung ohne Heizbetrieb.",
    "Nur Heizen/Kühlen": "Bei der Einstellung „Nur Heizen/Kühlen“ arbeitet die Anlage nur für Raumheizen bzw. aktives Kühlen. Keine Warmwasserladung.",
}

# Icons pro Systemmodus
SYSTEM_ICONS = {
    "Standby": "mdi:power-standby",
    "Automatik": "mdi:home-account",
    "Abwesend": "mdi:home-thermometer-outline",
    "Urlaub": "mdi:bag-suitcase-outline",
    "Nur Warmwasser": "mdi:water-thermometer",
    "Nur Heizen/Kühlen": "mdi:heat-wave",  # alternativ: mdi:radiator / mdi:snowflake
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
                info_map=SYSTEM_INFO,
                icon_map=SYSTEM_ICONS,      # dynamisches Icon nur für Systemmodus
                interval=interval,
            ),
            _ModeSelect(
                unique_id="idm_hka_betriebsart",
                translation_key="hka_betriebsart",
                client=client,
                host=host,
                register=REG_HKA_MODE,
                options_map=HK_OPTIONS,
                info_map=None,
                icon_map=None,
                interval=interval,
            ),
            _ModeSelect(
                unique_id="idm_hkc_betriebsart",
                translation_key="hkc_betriebsart",
                client=client,
                host=host,
                register=REG_HKC_MODE,
                options_map=HK_OPTIONS,
                info_map=None,
                icon_map=None,
                interval=interval,
            ),
            _ModeSelect(
                unique_id="idm_solar_betriebsart",
                translation_key="solar_betriebsart",
                client=client,
                host=host,
                register=REG_SOLAR_MODE,
                options_map=SOLAR_OPTIONS,
                info_map=None,
                icon_map=None,
                interval=interval,
            ),
        ]
    )


class _ModeSelect(SelectEntity):
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True

    def __init__(self, unique_id, translation_key, client, host, register, options_map, info_map, icon_map, interval):
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._client = client
        self._host = host
        self._register = register
        self._options_map = options_map
        self._info_map = info_map or {}
        self._icon_map = icon_map or {}
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
    def extra_state_attributes(self):
        if self._current_value in self._info_map:
            return {"hinweis": self._info_map[self._current_value]}
        return {}

    @property
    def icon(self):
        # dynamisches Icon je nach aktuellem Modus
        if self._current_value in self._icon_map:
            return self._icon_map[self._current_value]
        return "mdi:tune"

    @property
    def device_info(self):
        return {
            "identifiers": {("idm_heatpump", "idm_system")},
            "name": "iDM Wärmepumpe",
            "manufacturer": "iDM Energiesysteme",
            "model": "AERO ALM 4–12",
            "configuration_url": f"http://{self._host}",
        }
