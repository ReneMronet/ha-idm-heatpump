"""
iDM Wärmepumpe (Modbus TCP)
Version: v5.0
Stand: 2026-02-26

Änderungen v5.0 (Schritt 2):
- Solar-Betriebsart nur bei aktiver Solar-Gruppe
"""

import logging
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    REG_SYSTEM_MODE,
    REG_SOLAR_MODE,
    DEFAULT_HEATING_CIRCUITS,
    DEFAULT_SENSOR_GROUPS,
    hc_reg,
    get_device_info,
)

_LOGGER = logging.getLogger(__name__)

SYSTEM_OPTIONS = {
    "Standby": 0,
    "Automatik": 1,
    "Abwesend": 2,
    "Urlaub": 3,
    "Nur Warmwasser": 4,
    "Nur Heizen/K\u00fchlen": 5,
}

SYSTEM_INFO = {
    "Standby": "Ger\u00e4t auf Standby. Frostschutz ist aktiv.",
    "Automatik": "Bei Einstellung \u201eAutomatik\u201c l\u00e4uft das System nach den eingestellten Heiz-, K\u00fchl- und Warmwasserladezeiten.",
    "Abwesend": "Bei Einstellung \u201eAbwesend\u201c l\u00e4uft das System im Eco-Betrieb. R\u00e4ume mit Eco-Temperatur. Warmwasser gem\u00e4\u00df eingestellten Ladezeiten.",
    "Urlaub": "Bei Einstellung \u201eUrlaub\u201c l\u00e4uft das System f\u00fcr Heizen und K\u00fchlen im Eco-Betrieb. Die Warmwasserladung kann ein-/ausgeschaltet werden.",
    "Nur Warmwasser": "Bei der Einstellung \u201eNur Warmwasser\u201c l\u00e4uft die W\u00e4rmepumpe nur f\u00fcr Warmwasserladung ohne Heizbetrieb.",
    "Nur Heizen/K\u00fchlen": "Bei der Einstellung \u201eNur Heizen/K\u00fchlen\u201c arbeitet die Anlage nur f\u00fcr Raumheizen bzw. aktives K\u00fchlen. Keine Warmwasserladung.",
}

SYSTEM_ICONS = {
    "Standby": "mdi:power-standby",
    "Automatik": "mdi:home-account",
    "Abwesend": "mdi:home-thermometer-outline",
    "Urlaub": "mdi:bag-suitcase-outline",
    "Nur Warmwasser": "mdi:water-thermometer",
    "Nur Heizen/K\u00fchlen": "mdi:heat-wave",
}

HK_OPTIONS = {
    "Aus": 0,
    "Zeitprogramm": 1,
    "Normal": 2,
    "Eco": 3,
    "Manuell Heizen": 4,
    "Manuell K\u00fchlen": 5,
}

SOLAR_OPTIONS = {
    "Automatik": 0,
    "Warmwasser": 1,
    "Heizung": 2,
    "Warmwasser + Heizung": 3,
    "W\u00e4rmequelle / Pool": 4,
}


async def async_setup_entry(hass, entry, async_add_entities):
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    client = entry_data["client"]
    host = entry_data["host"]
    heating_circuits = entry_data.get("heating_circuits", DEFAULT_HEATING_CIRCUITS)
    sensor_groups = entry_data.get("sensor_groups", DEFAULT_SENSOR_GROUPS)

    entities = [
        # System-Betriebsart (immer)
        IDMModeSelect(
            coordinator, client, host,
            unique_id="idm_betriebsart",
            translation_key="betriebsart",
            register=REG_SYSTEM_MODE,
            options_map=SYSTEM_OPTIONS,
            info_map=SYSTEM_INFO,
            icon_map=SYSTEM_ICONS,
        ),
    ]

    # Dynamische Heizkreis-Selects (immer)
    for hc in heating_circuits:
        key = hc.lower()
        entities.append(
            IDMModeSelect(
                coordinator, client, host,
                unique_id=f"idm_hk{key}_betriebsart",
                translation_key=f"hk{key}_betriebsart",
                register=hc_reg(hc, "mode"),
                options_map=HK_OPTIONS,
            )
        )

    # Solar-Betriebsart (nur bei Solar-Gruppe)
    if "solar" in sensor_groups:
        entities.append(
            IDMModeSelect(
                coordinator, client, host,
                unique_id="idm_solar_betriebsart",
                translation_key="solar_betriebsart",
                register=REG_SOLAR_MODE,
                options_map=SOLAR_OPTIONS,
            )
        )

    async_add_entities(entities)


class IDMModeSelect(CoordinatorEntity, SelectEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True

    def __init__(self, coordinator, client, host,
                 unique_id, translation_key, register, options_map,
                 info_map=None, icon_map=None):
        super().__init__(coordinator)
        self._client = client
        self._host = host
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._register = register
        self._options_map = options_map
        self._reverse_map = {v: k for k, v in options_map.items()}
        self._info_map = info_map or {}
        self._icon_map = icon_map or {}

    @property
    def device_info(self):
        return get_device_info(self._host)

    @property
    def options(self):
        return list(self._options_map.keys())

    @property
    def current_option(self):
        raw = self.coordinator.data.get(self._register)
        if raw is None:
            return None
        return self._reverse_map.get(raw)

    async def async_select_option(self, option: str):
        code = self._options_map.get(option)
        if code is not None:
            await self._client.write_uchar(self._register, code)
            await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self):
        option = self.current_option
        if option in self._info_map:
            return {"hinweis": self._info_map[option]}
        return {}

    @property
    def icon(self):
        option = self.current_option
        if option in self._icon_map:
            return self._icon_map[option]
        return "mdi:tune"
