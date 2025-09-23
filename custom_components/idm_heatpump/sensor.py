"""
sensor.py – v1.27 (2025-09-23)

Sensor-Definitionen für iDM Wärmepumpe.
"""

from datetime import timedelta
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfPower,
    UnitOfEnergy,
    PERCENTAGE,
)
from homeassistant.helpers.entity import EntityCategory

from .const import (
    # Temperaturen & WP
    REG_OUTDOOR_TEMP,
    REG_OUTDOOR_TEMP_AVG,
    REG_HEATBUFFER_TEMP,
    REG_WW_TOP_TEMP,
    REG_WW_BOTTOM_TEMP,
    REG_WW_TAP_TEMP,
    REG_AIR_INLET_TEMP,
    REG_WP_VL_TEMP,
    REG_RETURN_TEMP,
    REG_LOAD_TEMP,
    REG_FLOW_SENSOR,
    REG_EVAP_OUT_TEMP,
    REG_FLUID_LINE_TEMP,
    REG_HOT_GAS_TEMP,
    # Heizkreise
    REG_HKA_VL,
    REG_HKA_VL_SOLL,
    REG_HKC_VL,
    REG_HKC_VL_SOLL,
    REG_HKA_ACTIVE_MODE,
    REG_HKC_ACTIVE_MODE,
    # PV/Batterie
    REG_PV_SURPLUS,
    REG_EHEIZSTAB,
    REG_PV_PRODUKTION,
    REG_HAUSVERBRAUCH,
    REG_BATTERIE_ENTLADUNG,
    REG_BATTERIE_FUELLSTAND,
    # Status & Leistung
    REG_WP_STATUS,
    REG_WP_POWER,
    # Energiemengen & Leistungen
    REG_EN_HEATING,
    REG_EN_TOTAL,
    REG_EN_COOLING,
    REG_EN_DHW,
    REG_EN_DEFROST,
    REG_EN_PASSIVE_COOL,
    REG_EN_SOLAR,
    REG_EN_EHEATER,
    REG_THERMAL_POWER,
    REG_SOLAR_POWER,
    # Solar-Temperaturen
    REG_SOLAR_COLLECTOR_TEMP,
    REG_SOLAR_RETURN_TEMP,
    REG_SOLAR_CHARGE_TEMP,
    # Setup
    CONF_UNIT_ID,
    DEFAULT_UNIT_ID,
    DOMAIN,
)
from .modbus_handler import IDMModbusHandler


async def async_setup_entry(hass, entry, async_add_entities):
    host = entry.data["host"]
    port = entry.data.get("port")
    unit_id = entry.data.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)
    interval = hass.data[DOMAIN][entry.entry_id]["update_interval"]

    client = IDMModbusHandler(host, port, unit_id)
    await client.connect()

    sensors = [
        # Außentemperaturen
        IDMHeatpumpFloatSensor("idm_aussentemperatur", "aussentemperatur", REG_OUTDOOR_TEMP,
                               UnitOfTemperature.CELSIUS, client, host, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpFloatSensor("idm_aussentemperatur_gemittelt", "aussentemperatur_gemittelt", REG_OUTDOOR_TEMP_AVG,
                               UnitOfTemperature.CELSIUS, client, host, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, interval),

        # Wärmepumpe direkt
        IDMHeatpumpFloatSensor("idm_wp_vorlauf", "wp_vorlauf", REG_WP_VL_TEMP,
                               UnitOfTemperature.CELSIUS, client, host, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpFloatSensor("idm_ruecklauf", "ruecklauf", REG_RETURN_TEMP,
                               UnitOfTemperature.CELSIUS, client, host, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpFloatSensor("idm_ladefuehler", "ladefuehler", REG_LOAD_TEMP,
                               UnitOfTemperature.CELSIUS, client, host, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpFloatSensor("idm_durchfluss", "durchfluss", REG_FLOW_SENSOR,
                               "l/min", client, host, None, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpFloatSensor("idm_luftansaug", "luftansaug", REG_AIR_INLET_TEMP,
                               UnitOfTemperature.CELSIUS, client, host, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, interval),

        # Zusätzliche WP-Sensoren
        IDMHeatpumpFloatSensor("idm_verdampferaustritt_1", "verdampferaustritt_1", REG_EVAP_OUT_TEMP,
                               UnitOfTemperature.CELSIUS, client, host, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpFloatSensor("idm_fluessigkeitsleitung", "fluessigkeitsleitung", REG_FLUID_LINE_TEMP,
                               UnitOfTemperature.CELSIUS, client, host, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpFloatSensor("idm_heissgas_1", "heissgas_1", REG_HOT_GAS_TEMP,
                               UnitOfTemperature.CELSIUS, client, host, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, interval),

        # Wärmespeicher / Warmwasser
        IDMHeatpumpFloatSensor("idm_waermespeicher", "waermespeicher", REG_HEATBUFFER_TEMP,
                               UnitOfTemperature.CELSIUS, client, host, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpFloatSensor("idm_ww_oben", "ww_oben", REG_WW_TOP_TEMP,
                               UnitOfTemperature.CELSIUS, client, host, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpFloatSensor("idm_ww_unten", "ww_unten", REG_WW_BOTTOM_TEMP,
                               UnitOfTemperature.CELSIUS, client, host, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpFloatSensor("idm_ww_zapftemp", "ww_zapftemp", REG_WW_TAP_TEMP,
                               UnitOfTemperature.CELSIUS, client, host, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, interval),

        # Heizkreis A
        IDMHeatpumpFloatSensor("idm_hka_vorlauftemperatur", "hka_vorlauf", REG_HKA_VL,
                               UnitOfTemperature.CELSIUS, client, host, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpFloatSensor("idm_hka_soll_vorlauf", "hka_soll_vorlauf", REG_HKA_VL_SOLL,
                               UnitOfTemperature.CELSIUS, client, host, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpActiveModeSensor("idm_hka_aktive_betriebsart", "hka_aktive_betriebsart",
                                    REG_HKA_ACTIVE_MODE, client, host, interval),

        # Heizkreis C
        IDMHeatpumpFloatSensor("idm_hkc_vorlauftemperatur", "hkc_vorlauf", REG_HKC_VL,
                               UnitOfTemperature.CELSIUS, client, host, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpFloatSensor("idm_hkc_soll_vorlauf", "hkc_soll_vorlauf", REG_HKC_VL_SOLL,
                               UnitOfTemperature.CELSIUS, client, host, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpActiveModeSensor("idm_hkc_aktive_betriebsart", "hkc_aktive_betriebsart",
                                    REG_HKC_ACTIVE_MODE, client, host, interval),

        # PV & Batterie
        IDMHeatpumpFloatSensor("idm_pv_ueberschuss", "pv_ueberschuss", REG_PV_SURPLUS,
                               UnitOfPower.KILO_WATT, client, host, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpFloatSensor("idm_e_heizstab", "e_heizstab", REG_EHEIZSTAB,
                               UnitOfPower.KILO_WATT, client, host, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpFloatSensor("idm_pv_produktion", "pv_produktion", REG_PV_PRODUKTION,
                               UnitOfPower.KILO_WATT, client, host, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpFloatSensor("idm_hausverbrauch", "hausverbrauch", REG_HAUSVERBRAUCH,
                               UnitOfPower.KILO_WATT, client, host, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpFloatSensor("idm_batterie_entladung", "batterie_entladung", REG_BATTERIE_ENTLADUNG,
                               UnitOfPower.KILO_WATT, client, host, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpWordSensor("idm_batterie_fuellstand", "batterie_fuellstand", REG_BATTERIE_FUELLSTAND,
                              PERCENTAGE, client, host, interval, entity_category=EntityCategory.DIAGNOSTIC),

        # Status WP
        IDMHeatpumpStatusSensor("idm_status_warmepumpe", "status_warmepumpe", REG_WP_STATUS,
                                client, host, interval),

        # Elektrische Leistungsaufnahme WP
        IDMHeatpumpFloatSensor("idm_wp_power", "wp_power", REG_WP_POWER,
                               UnitOfPower.KILO_WATT, client, host, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, interval),

        # Energiemengen (kWh) total_increasing
        IDMHeatpumpFloatSensor("idm_en_heizen", "en_heizen", REG_EN_HEATING,
                               UnitOfEnergy.KILO_WATT_HOUR, client, host, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, interval),
        IDMHeatpumpFloatSensor("idm_en_gesamt", "en_gesamt", REG_EN_TOTAL,
                               UnitOfEnergy.KILO_WATT_HOUR, client, host, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, interval),
        IDMHeatpumpFloatSensor("idm_en_kuehlen", "en_kuehlen", REG_EN_COOLING,
                               UnitOfEnergy.KILO_WATT_HOUR, client, host, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, interval),
        IDMHeatpumpFloatSensor("idm_en_warmwasser", "en_warmwasser", REG_EN_DHW,
                               UnitOfEnergy.KILO_WATT_HOUR, client, host, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, interval),
        IDMHeatpumpFloatSensor("idm_en_abtauung", "en_abtauung", REG_EN_DEFROST,
                               UnitOfEnergy.KILO_WATT_HOUR, client, host, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, interval),
        IDMHeatpumpFloatSensor("idm_en_passivkuehlung", "en_passivkuehlung", REG_EN_PASSIVE_COOL,
                               UnitOfEnergy.KILO_WATT_HOUR, client, host, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, interval),
        IDMHeatpumpFloatSensor("idm_en_solar", "en_solar", REG_EN_SOLAR,
                               UnitOfEnergy.KILO_WATT_HOUR, client, host, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, interval),
        IDMHeatpumpFloatSensor("idm_en_eheizer", "en_eheizer", REG_EN_EHEATER,
                               UnitOfEnergy.KILO_WATT_HOUR, client, host, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, interval),

        # Thermische Leistungen
        IDMHeatpumpFloatSensor("idm_thermische_leistung", "thermische_leistung", REG_THERMAL_POWER,
                               UnitOfPower.KILO_WATT, client, host, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpFloatSensor("idm_solar_leistung", "solar_leistung", REG_SOLAR_POWER,
                               UnitOfPower.KILO_WATT, client, host, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, interval),

        # Solar-Temperaturen
        IDMHeatpumpFloatSensor("idm_solar_kollektor", "solar_kollektor", REG_SOLAR_COLLECTOR_TEMP,
                               UnitOfTemperature.CELSIUS, client, host, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpFloatSensor("idm_solar_ruecklauf", "solar_ruecklauf", REG_SOLAR_RETURN_TEMP,
                               UnitOfTemperature.CELSIUS, client, host, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, interval),
        IDMHeatpumpFloatSensor("idm_solar_ladetemp", "solar_ladetemp", REG_SOLAR_CHARGE_TEMP,
                               UnitOfTemperature.CELSIUS, client, host, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, interval),
    ]

    async_add_entities(sensors)


# -------------------------------------------------------------------
# Basisklasse
# -------------------------------------------------------------------
class IDMBaseEntity:
    def __init__(self, host: str):
        self._host = host

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
# Float-Sensor
# -------------------------------------------------------------------
class IDMHeatpumpFloatSensor(IDMBaseEntity, SensorEntity):
    def __init__(self, unique_id, translation_key, register, unit, client, host,
                 device_class=None, state_class=SensorStateClass.MEASUREMENT, interval=30,
                 entity_category=None):
        super().__init__(host)
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._attr_has_entity_name = True
        self._register = register
        self._attr_native_unit_of_measurement = unit
        self._client = client
        self._attr_native_value = None
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_scan_interval = timedelta(seconds=interval)
        self._attr_entity_category = entity_category

    async def async_update(self):
        value = await self._client.read_float(self._register)
        if value is not None:
            self._attr_native_value = value


# -------------------------------------------------------------------
# Word-Sensor
# -------------------------------------------------------------------
class IDMHeatpumpWordSensor(IDMBaseEntity, SensorEntity):
    def __init__(self, unique_id, translation_key, register, unit, client, host, interval=30,
                 entity_category=None):
        super().__init__(host)
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._attr_has_entity_name = True
        self._register = register
        self._attr_native_unit_of_measurement = unit
        self._client = client
        self._attr_native_value = None
        self._attr_device_class = None
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_scan_interval = timedelta(seconds=interval)
        self._attr_entity_category = entity_category

    async def async_update(self):
        value = await self._client.read_word(self._register)
        if value is not None:
            self._attr_native_value = value


# -------------------------------------------------------------------
# Status-Sensor Wärmepumpe
# -------------------------------------------------------------------
class IDMHeatpumpStatusSensor(IDMBaseEntity, SensorEntity):
    def __init__(self, unique_id, translation_key, register, client, host, interval=30):
        super().__init__(host)
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._attr_has_entity_name = True
        self._register = register
        self._client = client
        self._attr_native_value = None
        self._attr_scan_interval = timedelta(seconds=interval)

    async def async_update(self):
        value = await self._client.read_uchar(self._register)
        if value == 0:
            self._attr_native_value = "Bereit"
        elif value == 1:
            self._attr_native_value = "Heizbetrieb"
        else:
            self._attr_native_value = "Unbekannt"

    @property
    def icon(self):
        if self._attr_native_value == "Bereit":
            return "mdi:power-standby"
        elif self._attr_native_value == "Heizbetrieb":
            return "mdi:radiator"
        return "mdi:alert-circle-outline"


# -------------------------------------------------------------------
# Aktive Betriebsart Heizkreis A/C
# -------------------------------------------------------------------
class IDMHeatpumpActiveModeSensor(IDMBaseEntity, SensorEntity):
    def __init__(self, unique_id, translation_key, register, client, host, interval=30):
        super().__init__(host)
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._attr_has_entity_name = True
        self._register = register
        self._client = client
        self._attr_native_value = None
        self._attr_scan_interval = timedelta(seconds=interval)

    async def async_update(self):
        value = await self._client.read_uchar(self._register)
        if value == 0:
            self._attr_native_value = "Aus"
        elif value == 1:
            self._attr_native_value = "Heizen"
        elif value == 2:
            self._attr_native_value = "Kühlen"
        else:
            self._attr_native_value = "Unbekannt"

    @property
    def icon(self):
        if self._attr_native_value == "Aus":
            return "mdi:power-standby"
        elif self._attr_native_value == "Heizen":
            return "mdi:radiator"
        elif self._attr_native_value == "Kühlen":
            return "mdi:snowflake"
        return "mdi:alert-circle-outline"
