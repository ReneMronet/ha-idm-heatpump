"""
iDM Wärmepumpe (Modbus TCP)
Version: v0.7.0
Stand: 2026-02-26

Änderungen v0.7.0:
- Temperatur-Offset Number-Entity pro HK (±5°C, Step 0.5)
- Persistiert via RestoreEntity, wirkt direkt auf RoomTempForwarder

Änderungen v5.0 (Schritt 2):
- Kühl-Numbers pro HK: cool_normal, cool_eco, cool_limit, cool_vl
- Leistungsbegrenzung WP (Reg. 4108, Diagnose-Gruppe)
- PV-Zielwert (Reg. 88, PV/Batterie-Gruppe)
- Sensor-Gruppen-Filterung
"""

import logging
from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfTemperature, UnitOfPower
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    DEFAULT_HEATING_CIRCUITS,
    DEFAULT_SENSOR_GROUPS,
    DEFAULT_ROOM_TEMP_ENTITIES,
    ROOM_TEMP_OFFSET_MIN,
    ROOM_TEMP_OFFSET_MAX,
    ROOM_TEMP_OFFSET_STEP,
    ROOM_TEMP_OFFSET_DEFAULT,
    REG_WW_TARGET,
    REG_WW_START,
    REG_WW_STOP,
    REG_POWER_LIMIT,
    REG_PV_TARGET,
    hc_reg,
    get_device_info,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    client = entry_data["client"]
    host = entry_data["host"]
    heating_circuits = entry_data.get("heating_circuits", DEFAULT_HEATING_CIRCUITS)
    sensor_groups = entry_data.get("sensor_groups", DEFAULT_SENSOR_GROUPS)
    room_temp_entities = entry_data.get("room_temp_entities", DEFAULT_ROOM_TEMP_ENTITIES)
    forwarder = entry_data.get("room_temp_forwarder")

    entities = []

    # ===================================================================
    # BASIS: Heizkreis-Numbers (immer aktiv)
    # ===================================================================
    for hc in heating_circuits:
        key = hc.lower()
        entities.extend([
            IDMFloatNumber(
                coordinator, client, host,
                f"idm_hk{key}_temp_normal", f"hk{key}_temp_normal",
                hc_reg(hc, "temp_normal"), 15, 30, 0.5, 22,
            ),
            IDMFloatNumber(
                coordinator, client, host,
                f"idm_hk{key}_temp_eco", f"hk{key}_temp_eco",
                hc_reg(hc, "temp_eco"), 10, 25, 0.5, 18,
            ),
            IDMFloatNumber(
                coordinator, client, host,
                f"idm_hk{key}_curve", f"hk{key}_curve",
                hc_reg(hc, "curve"), 0.1, 3.5, 0.1, 0.6,
            ),
            IDMUcharNumber(
                coordinator, client, host,
                f"idm_hk{key}_parallel", f"hk{key}_parallel",
                hc_reg(hc, "parallel"), 0, 30, 1, 0,
            ),
            IDMUcharNumber(
                coordinator, client, host,
                f"idm_hk{key}_heat_limit", f"hk{key}_heat_limit",
                hc_reg(hc, "heat_limit"), 0, 50, 1, 15,
            ),
        ])

    # Warmwasser (Basis)
    entities.extend([
        IDMUcharNumber(coordinator, client, host,
                       "idm_ww_target", "ww_target", REG_WW_TARGET,
                       30, 60, 1, 46),
        IDMUcharNumber(coordinator, client, host,
                       "idm_ww_start", "ww_start", REG_WW_START,
                       30, 50, 1, 46),
        IDMUcharNumber(coordinator, client, host,
                       "idm_ww_stop", "ww_stop", REG_WW_STOP,
                       46, 67, 1, 50),
    ])

    # ===================================================================
    # KÜHLUNGS-GRUPPE: Kühl-Numbers pro HK
    # ===================================================================
    if "cooling" in sensor_groups:
        for hc in heating_circuits:
            key = hc.lower()
            entities.extend([
                # Raumsolltemp Kühlen Normal (FLOAT, 18–30 °C)
                IDMFloatNumber(
                    coordinator, client, host,
                    f"idm_hk{key}_cool_normal", f"hk{key}_cool_normal",
                    hc_reg(hc, "cool_normal"), 18, 30, 0.5, 24,
                ),
                # Raumsolltemp Kühlen Eco (FLOAT, 20–32 °C)
                IDMFloatNumber(
                    coordinator, client, host,
                    f"idm_hk{key}_cool_eco", f"hk{key}_cool_eco",
                    hc_reg(hc, "cool_eco"), 20, 32, 0.5, 26,
                ),
                # Kühlgrenze (UCHAR, 10–40 °C)
                IDMUcharNumber(
                    coordinator, client, host,
                    f"idm_hk{key}_cool_limit", f"hk{key}_cool_limit",
                    hc_reg(hc, "cool_limit"), 10, 40, 1, 20,
                ),
                # Soll-Vorlauf Kühlen (UCHAR, 10–25 °C)
                IDMUcharNumber(
                    coordinator, client, host,
                    f"idm_hk{key}_cool_vl", f"hk{key}_cool_vl",
                    hc_reg(hc, "cool_vl"), 10, 25, 1, 18,
                ),
            ])

    # ===================================================================
    # DIAGNOSE-GRUPPE: Leistungsbegrenzung WP
    # ===================================================================
    if "diagnostic" in sensor_groups:
        entities.append(
            IDMFloatNumber(
                coordinator, client, host,
                "idm_leistungsbegrenzung", "leistungsbegrenzung",
                REG_POWER_LIMIT, 0.0, 100.0, 1.0, 100.0,
                unit=UnitOfPower.KILO_WATT,
                entity_category=EntityCategory.CONFIG,
                default_enabled=False,
            ),
        )

    # ===================================================================
    # PV / BATTERIE-GRUPPE: PV-Zielwert
    # ===================================================================
    if "pv_battery" in sensor_groups:
        entities.append(
            IDMFloatNumber(
                coordinator, client, host,
                "idm_pv_zielwert", "pv_zielwert",
                REG_PV_TARGET, 0.0, 50.0, 0.1, 0.0,
                unit=UnitOfPower.KILO_WATT,
            ),
        )

    # ===================================================================
    # RAUMTEMPERATUR-OFFSET pro HK (v0.7.0)
    # ===================================================================
    if room_temp_entities and forwarder:
        for hc in room_temp_entities:
            key = hc.lower()
            entities.append(
                IDMRoomTempOffset(
                    coordinator, host, forwarder, hc,
                    unique_id=f"idm_hk{key}_room_temp_offset",
                    translation_key=f"hk{key}_room_temp_offset",
                ),
            )

    async_add_entities(entities)


# -------------------------------------------------------------------
# FLOAT-Number
# -------------------------------------------------------------------
class IDMFloatNumber(CoordinatorEntity, NumberEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, client, host,
                 unique_id, translation_key, register,
                 min_value, max_value, step, default,
                 unit=None, entity_category=None,
                 default_enabled=True):
        super().__init__(coordinator)
        self._client = client
        self._host = host
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._register = register
        self._attr_native_min_value = float(min_value)
        self._attr_native_max_value = float(max_value)
        self._attr_native_step = float(step)
        self._default = float(default)
        self._attr_native_unit_of_measurement = unit or UnitOfTemperature.CELSIUS
        self._attr_device_class = "temperature" if unit is None else None
        self._attr_entity_category = entity_category
        if not default_enabled:
            self._attr_entity_registry_enabled_default = False

    @property
    def device_info(self):
        return get_device_info(self._host)

    @property
    def native_value(self):
        value = self.coordinator.data.get(self._register)
        if value is not None:
            return round(float(value), 1)
        return None

    async def async_set_native_value(self, value: float):
        await self._client.write_float(self._register, float(value))
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self):
        return {"default_value": self._default}


# -------------------------------------------------------------------
# UCHAR-Number
# -------------------------------------------------------------------
class IDMUcharNumber(CoordinatorEntity, NumberEntity):
    _attr_has_entity_name = True
    _attr_device_class = "temperature"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, client, host,
                 unique_id, translation_key, register,
                 min_value, max_value, step, default):
        super().__init__(coordinator)
        self._client = client
        self._host = host
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._register = register
        self._attr_native_min_value = int(min_value)
        self._attr_native_max_value = int(max_value)
        self._attr_native_step = int(step)
        self._default = int(default)

    @property
    def device_info(self):
        return get_device_info(self._host)

    @property
    def native_value(self):
        value = self.coordinator.data.get(self._register)
        if value is not None:
            return int(value)
        return None

    async def async_set_native_value(self, value: float):
        await self._client.write_uchar(self._register, int(value))
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self):
        return {"default_value": self._default}


# -------------------------------------------------------------------
# Room Temperature Offset (v0.7.0)
# -------------------------------------------------------------------
class IDMRoomTempOffset(CoordinatorEntity, RestoreEntity, NumberEntity):
    """Temperatur-Offset pro Heizkreis.

    Positiver Offset → WP denkt es ist wärmer → heizt weniger
    Negativer Offset → WP denkt es ist kälter → heizt mehr

    Der Wert wird vor dem Schreiben in Register 1650+i*2 addiert.
    Persistiert via RestoreEntity über HA-Neustarts hinweg.
    """

    _attr_has_entity_name = True
    _attr_native_min_value = ROOM_TEMP_OFFSET_MIN
    _attr_native_max_value = ROOM_TEMP_OFFSET_MAX
    _attr_native_step = ROOM_TEMP_OFFSET_STEP
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = "temperature"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:thermometer-plus"

    def __init__(self, coordinator, host, forwarder, hc,
                 unique_id, translation_key):
        super().__init__(coordinator)
        self._host = host
        self._forwarder = forwarder
        self._hc = hc
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._value = ROOM_TEMP_OFFSET_DEFAULT

    @property
    def device_info(self):
        return get_device_info(self._host)

    @property
    def native_value(self):
        return self._value

    async def async_set_native_value(self, value: float):
        self._value = round(float(value), 1)
        self._forwarder.set_offset(self._hc, self._value)
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Restore previous value on startup."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.state not in (None, "unknown", "unavailable"):
            try:
                self._value = round(float(last_state.state), 1)
            except (ValueError, TypeError):
                self._value = ROOM_TEMP_OFFSET_DEFAULT
        # Offset im Forwarder setzen
        self._forwarder.set_offset(self._hc, self._value)
        _LOGGER.debug(
            "Raumtemperatur-Offset HK %s restored: %.1f°C",
            self._hc, self._value,
        )

    @property
    def extra_state_attributes(self):
        return {
            "heizkreis": self._hc,
            "default_value": ROOM_TEMP_OFFSET_DEFAULT,
        }
