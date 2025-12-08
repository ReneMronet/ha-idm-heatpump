# Datei: sensor.py
"""
iDM Wärmepumpe (Modbus TCP)
Version: v1.37
Stand: 2025-12-08

Änderungen v1.37:
- IDMHeatpumpFloatSensor.async_update(): Für Sensoren mit state_class TOTAL_INCREASING
  werden negative Werte ignoriert (z. B. -1.0 bei nicht verwendeten Energiezählern),
  um Recorder-Warnungen zu vermeiden.

Änderungen v1.36:
- Import-Fehler in sensor.py (unsichtbares Steuerzeichen vor 'from homeassistant.const')
  behoben, damit alle Sensoren wieder geladen werden.

Änderungen v1.35:
- Sensor idm_durchfluss (B2 / REG_FLOW_SENSOR) auf UCHAR-Lesung mit 0,1-l/min-Skalierung umgestellt

Änderungen v1.34:
- Neuer Sensor idm_betriebsart_warmepumpe (UCHAR RO) für REG_WP_MODE (1090)
  Werte: 0=Bereit, 1=Heizbetrieb, 2=Kühlbetrieb, 3=Abtauung, 4=Warmwasser

Änderungen v1.33:
- Interne Meldung (REG_INTERNAL_MESSAGE/1004) erweitert:
  * Mapping MESSAGE_CODES (020–532) zu Klartext (Attribut code_text)
  * Event bei Änderung: idm_internal_message_changed {code:int, text:str}
  * Persistent Notification: Titel "iDM interne Meldung", Text "Code XYZ – <Beschreibung>"

Änderungen v1.30:
- Neuer Sensor idm_interne_meldung (UCHAR RO) für REG_INTERNAL_MESSAGE (1004), zeigt aktuelle NAVIGATOR-Meldungsnummer 020–999

Änderungen v1.29:
- Neuer Sensor idm_luftansaug_2 für REG_AIR_INLET_TEMP_2 (1064 / B46 Luftansaugtemperatur 2)
- Bestehende Sensoren unverändert
"""

from datetime import timedelta

from homeassistant.components.persistent_notification import async_create as pn_create
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.helpers.entity import EntityCategory

from .const import (
    # Temperaturen & WP
    REG_AIR_INLET_TEMP,
    REG_AIR_INLET_TEMP_2,
    REG_FLOW_SENSOR,
    REG_HEATBUFFER_TEMP,
    REG_LOAD_TEMP,
    REG_OUTDOOR_TEMP,
    REG_OUTDOOR_TEMP_AVG,
    REG_RETURN_TEMP,
    REG_WP_VL_TEMP,
    REG_WW_BOTTOM_TEMP,
    REG_WW_TAP_TEMP,
    REG_WW_TOP_TEMP,
    # Heizkreise
    REG_HKA_ACTIVE_MODE,
    REG_HKA_VL,
    REG_HKA_VL_SOLL,
    REG_HKC_ACTIVE_MODE,
    REG_HKC_VL,
    REG_HKC_VL_SOLL,
    # PV/Batterie
    REG_BATTERIE_ENTLADUNG,
    REG_BATTERIE_FUELLSTAND,
    REG_EHEIZSTAB,
    REG_HAUSVERBRAUCH,
    REG_PV_PRODUKTION,
    REG_PV_SURPLUS,
    # System/Status & Leistung
    REG_INTERNAL_MESSAGE,
    REG_THERMAL_POWER,
    REG_WP_POWER,
    REG_WP_STATUS,
    # Energiemengen & Leistungen
    REG_EN_COOLING,
    REG_EN_DEFROST,
    REG_EN_DHW,
    REG_EN_EHEATER,
    REG_EN_HEATING,
    REG_EN_PASSIVE_COOL,
    REG_EN_SOLAR,
    REG_EN_TOTAL,
    REG_SOLAR_POWER,
    # Solar-Temperaturen
    REG_SOLAR_CHARGE_TEMP,
    REG_SOLAR_COLLECTOR_TEMP,
    REG_SOLAR_RETURN_TEMP,
    # Setup
    CONF_UNIT_ID,
    DEFAULT_UNIT_ID,
    DOMAIN,
)

# Fallback, falls REG_WP_MODE in const.py noch nicht definiert ist
try:
    from .const import REG_WP_MODE as _REG_WP_MODE
except Exception:  # pragma: no cover
    _REG_WP_MODE = 1090  # UCHAR RO Betriebsart Wärmepumpe
REG_WP_MODE = _REG_WP_MODE

from .modbus_handler import IDMModbusHandler


# -------------------------------------------------------------------
# NAVIGATOR-Meldungscode -> Klartext (020–532). 0 = Keine Meldung.
# -------------------------------------------------------------------
MESSAGE_CODES = {
    0: "Keine Meldung",
    20: "Wärmepumpenvorlauf Maximaltemperatur",
    21: "Wärmepumpenvorlauf Minimaltemperatur",
    22: "Niederdruckstörung",
    23: "Niederdruckstörung",
    221: "Niederdruckstörung",
    231: "Niederdruckstörung",
    24: "Hochdruckstörung",
    25: "Hochdruckstörung",
    241: "Hochdruckstörung",
    251: "Hochdruckstörung",
    26: "Strömungsüberwachung",
    27: "Strömungsüberwachung",
    28: "Anlaufstrombegrenzer",
    29: "Anlaufstrombegrenzer",
    74: "Anlaufstrombegrenzer",
    75: "Anlaufstrombegrenzer",
    30: "Motorschutz Wärmequellenpumpe",
    31: "Motorschutz Wärmequellenpumpe",
    32: "Maximale Abtauzeit überschritten",
    232: "Maximale Abtauzeit überschritten",
    33: "Minimale Kondensatortemperatur unterschritten",
    56: "Minimale Kondensatortemperatur unterschritten",
    233: "Minimale Kondensatortemperatur unterschritten",
    256: "Minimale Kondensatortemperatur unterschritten",
    34: "Ventilatorfehler",
    38: "Ventilatorfehler",
    234: "Ventilatorfehler",
    238: "Ventilatorfehler",
    35: "Minimale Wärmepumpen- oder Wärmespeichertemperatur",
    57: "Minimale Wärmepumpen- oder Wärmespeichertemperatur",
    235: "Minimale Wärmepumpen- oder Wärmespeichertemperatur",
    257: "Minimale Wärmepumpen- oder Wärmespeichertemperatur",
    36: "E-Heizstab Überhitzung",
    37: "Störung Ladepumpe",
    237: "Störung Ladepumpe",
    42: "Störung Heißgas",
    43: "Störung Heißgas",
    242: "Störung Heißgas",
    243: "Störung Heißgas",
    44: "Störung Durchflussüberwachung Heizungsseite",
    244: "Störung Durchflussüberwachung Heizungsseite",
    46: "Störung Heißgas",
    47: "Störung Heißgas",
    246: "Störung Heißgas",
    247: "Störung Heißgas",
    48: "Strömungsüberwachung",
    49: "Strömungsüberwachung",
    50: "Taupunktwächter angesprochen",
    51: "Taupunktwächter angesprochen",
    54: "Durchflussüberwachung heizungsseitig fehlerhaft",
    55: "Durchflussüberwachung heizungsseitig fehlerhaft",
    58: "Hochdruckstörung im Warmwasserbetrieb mit AQA",
    59: "Hochdruckstörung im Warmwasserbetrieb mit AQA",
    60: "Wärmequellentemperaturfehler",
    61: "Wärmequellentemperaturfehler",
    67: "Wärmequellentemperaturfehler",
    62: "Wicklungsschutz",
    63: "Wicklungsschutz",
    262: "Wicklungsschutz",
    263: "Wicklungsschutz",
    69: "Wärmequellenrückspeisetemperatur zu hoch",
    95: "Einsatzgrenzenstörung",
    96: "Einsatzgrenzenstörung",
    295: "Einsatzgrenzenstörung",
    296: "Einsatzgrenzenstörung",
    97: "Störung Schrittmotor",
    **{i: "Fühlerstörung" for i in range(100, 200)},
    203: "Solar-Log Update erforderlich",
    236: "Sicherheitsabtauintervall zu kurz",
    239: "Batteriefehler",
    240: "Störung Spannungsversorgung",
    265: "Estrich heizen abgebrochen / Solltemperatur nicht erreicht",
    270: "Wärmepumpe verriegelt (Stufen längerfristig blockiert)",
    271: "Bivalenz manuell aktiviert",
    272: "Wärmepumpe verriegelt – Bivalenz im Notbetrieb aktiv",
    280: "Kollektor Maximaltemperatur",
    281: "Hygienik Maximaltemperatur",
    282: "Wärmespeicher Maximaltemperatur",
    283: "Wärmequellen Maximaltemperatur",
    284: "Solarmodul nicht vorhanden",
    285: "Minimale Ladetemperatur unterschritten",
    286: "ISC-Modul nicht gefunden",
    287: "Störung Kältespeicherpumpe",
    288: "Störung Rückkühlpumpe",
    289: "Störung Rückkühlfühler",
    290: "Störung Rückkühlfühler",
    291: "Maximale Rückkühltemperatur unterschritten",
    293: "Minimale Wärmequellenaustrittstemperatur iDM Systemkühlung",
    301: "Boostfunktion – Temperatur nicht erreicht",
    302: "Legionellenfunktion – Temperatur nicht erreicht",
    **{i: "Störung bei gemeinsamer Wärmequelle" for i in range(305, 315)},
    400: "Kommunikation Kaskade",
    **{i: "Kommunikations- oder Inverterstörung" for i in range(516, 533)},
}


def code_to_text(code: int) -> str:
    return MESSAGE_CODES.get(code, "Unbekannte Meldung – siehe NAVIGATOR-Handbuch")


# -------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------
async def async_setup_entry(hass, entry, async_add_entities):
    host = entry.data["host"]
    port = entry.data.get("port")
    unit_id = entry.data.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)
    interval = hass.data[DOMAIN][entry.entry_id]["update_interval"]

    client = IDMModbusHandler(host, port, unit_id)
    await client.connect()

    sensors = [
        # Außentemperaturen
        IDMHeatpumpFloatSensor(
            "idm_aussentemperatur",
            "aussentemperatur",
            REG_OUTDOOR_TEMP,
            UnitOfTemperature.CELSIUS,
            client,
            host,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_aussentemperatur_gemittelt",
            "aussentemperatur_gemittelt",
            REG_OUTDOOR_TEMP_AVG,
            UnitOfTemperature.CELSIUS,
            client,
            host,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
            interval,
        ),

        # Wärmepumpe direkt
        IDMHeatpumpFloatSensor(
            "idm_wp_vorlauf",
            "wp_vorlauf",
            REG_WP_VL_TEMP,
            UnitOfTemperature.CELSIUS,
            client,
            host,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_ruecklauf",
            "ruecklauf",
            REG_RETURN_TEMP,
            UnitOfTemperature.CELSIUS,
            client,
            host,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_ladefuehler",
            "ladefuehler",
            REG_LOAD_TEMP,
            UnitOfTemperature.CELSIUS,
            client,
            host,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
            interval,
        ),

        # Durchfluss B2: UCHAR mit 0,1-l/min-Skalierung
        IDMHeatpumpFlowSensor(
            "idm_durchfluss",
            "durchfluss",
            REG_FLOW_SENSOR,
            client,
            host,
            interval,
        ),

        IDMHeatpumpFloatSensor(
            "idm_luftansaug",
            "luftansaug",
            REG_AIR_INLET_TEMP,
            UnitOfTemperature.CELSIUS,
            client,
            host,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_luftansaug_2",
            "luftansaug_2",
            REG_AIR_INLET_TEMP_2,
            UnitOfTemperature.CELSIUS,
            client,
            host,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
            interval,
        ),

        # Wärmespeicher / Warmwasser
        IDMHeatpumpFloatSensor(
            "idm_waermespeicher",
            "waermespeicher",
            REG_HEATBUFFER_TEMP,
            UnitOfTemperature.CELSIUS,
            client,
            host,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_ww_oben",
            "ww_oben",
            REG_WW_TOP_TEMP,
            UnitOfTemperature.CELSIUS,
            client,
            host,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_ww_unten",
            "ww_unten",
            REG_WW_BOTTOM_TEMP,
            UnitOfTemperature.CELSIUS,
            client,
            host,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_ww_zapftemp",
            "ww_zapftemp",
            REG_WW_TAP_TEMP,
            UnitOfTemperature.CELSIUS,
            client,
            host,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
            interval,
        ),

        # Heizkreis A
        IDMHeatpumpFloatSensor(
            "idm_hka_vorlauftemperatur",
            "hka_vorlauf",
            REG_HKA_VL,
            UnitOfTemperature.CELSIUS,
            client,
            host,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_hka_soll_vorlauf",
            "hka_soll_vorlauf",
            REG_HKA_VL_SOLL,
            UnitOfTemperature.CELSIUS,
            client,
            host,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
            interval,
        ),
        IDMHeatpumpActiveModeSensor(
            "idm_hka_aktive_betriebsart",
            "hka_aktive_betriebsart",
            REG_HKA_ACTIVE_MODE,
            client,
            host,
            interval,
        ),

        # Heizkreis C
        IDMHeatpumpFloatSensor(
            "idm_hkc_vorlauftemperatur",
            "hkc_vorlauf",
            REG_HKC_VL,
            UnitOfTemperature.CELSIUS,
            client,
            host,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_hkc_soll_vorlauf",
            "hkc_soll_vorlauf",
            REG_HKC_VL_SOLL,
            UnitOfTemperature.CELSIUS,
            client,
            host,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
            interval,
        ),
        IDMHeatpumpActiveModeSensor(
            "idm_hkc_aktive_betriebsart",
            "hkc_aktive_betriebsart",
            REG_HKC_ACTIVE_MODE,
            client,
            host,
            interval,
        ),

        # PV & Batterie
        IDMHeatpumpFloatSensor(
            "idm_pv_ueberschuss",
            "pv_ueberschuss",
            REG_PV_SURPLUS,
            UnitOfPower.KILO_WATT,
            client,
            host,
            SensorDeviceClass.POWER,
            SensorStateClass.MEASUREMENT,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_e_heizstab",
            "e_heizstab",
            REG_EHEIZSTAB,
            UnitOfPower.KILO_WATT,
            client,
            host,
            SensorDeviceClass.POWER,
            SensorStateClass.MEASUREMENT,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_pv_produktion",
            "pv_produktion",
            REG_PV_PRODUKTION,
            UnitOfPower.KILO_WATT,
            client,
            host,
            SensorDeviceClass.POWER,
            SensorStateClass.MEASUREMENT,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_hausverbrauch",
            "hausverbrauch",
            REG_HAUSVERBRAUCH,
            UnitOfPower.KILO_WATT,
            client,
            host,
            SensorDeviceClass.POWER,
            SensorStateClass.MEASUREMENT,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_batterie_entladung",
            "batterie_entladung",
            REG_BATTERIE_ENTLADUNG,
            UnitOfPower.KILO_WATT,
            client,
            host,
            SensorDeviceClass.POWER,
            SensorStateClass.MEASUREMENT,
            interval,
        ),
        IDMHeatpumpWordSensor(
            "idm_batterie_fuellstand",
            "batterie_fuellstand",
            REG_BATTERIE_FUELLSTAND,
            PERCENTAGE,
            client,
            host,
            interval,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),

        # System: Interne Meldung mit Klartext + Events
        IDMHeatpumpInternalMessageSensor(
            "idm_interne_meldung",
            "interne_meldung",
            REG_INTERNAL_MESSAGE,
            client,
            host,
            interval,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),

        # Betriebsart Wärmepumpe (1090) + bisheriger Status (1091)
        IDMHeatpumpWpModeSensor(
            "idm_betriebsart_warmepumpe",
            "betriebsart_warmepumpe",
            REG_WP_MODE,
            client,
            host,
            interval,
        ),
        IDMHeatpumpStatusSensor(
            "idm_status_warmepumpe",
            "status_warmepumpe",
            REG_WP_STATUS,
            client,
            host,
            interval,
        ),

        # Elektrische Leistungsaufnahme WP
        IDMHeatpumpFloatSensor(
            "idm_wp_power",
            "wp_power",
            REG_WP_POWER,
            UnitOfPower.KILO_WATT,
            client,
            host,
            SensorDeviceClass.POWER,
            SensorStateClass.MEASUREMENT,
            interval,
        ),

        # Energiemengen (kWh)
        IDMHeatpumpFloatSensor(
            "idm_en_heizen",
            "en_heizen",
            REG_EN_HEATING,
            UnitOfEnergy.KILO_WATT_HOUR,
            client,
            host,
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL_INCREASING,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_en_gesamt",
            "en_gesamt",
            REG_EN_TOTAL,
            UnitOfEnergy.KILO_WATT_HOUR,
            client,
            host,
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL_INCREASING,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_en_kuehlen",
            "en_kuehlen",
            REG_EN_COOLING,
            UnitOfEnergy.KILO_WATT_HOUR,
            client,
            host,
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL_INCREASING,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_en_warmwasser",
            "en_warmwasser",
            REG_EN_DHW,
            UnitOfEnergy.KILO_WATT_HOUR,
            client,
            host,
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL_INCREASING,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_en_abtauung",
            "en_abtauung",
            REG_EN_DEFROST,
            UnitOfEnergy.KILO_WATT_HOUR,
            client,
            host,
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL_INCREASING,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_en_passivkuehlung",
            "en_passivkuehlung",
            REG_EN_PASSIVE_COOL,
            UnitOfEnergy.KILO_WATT_HOUR,
            client,
            host,
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL_INCREASING,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_en_solar",
            "en_solar",
            REG_EN_SOLAR,
            UnitOfEnergy.KILO_WATT_HOUR,
            client,
            host,
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL_INCREASING,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_en_eheizer",
            "en_eheizer",
            REG_EN_EHEATER,
            UnitOfEnergy.KILO_WATT_HOUR,
            client,
            host,
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL_INCREASING,
            interval,
        ),

        # Thermische Leistungen
        IDMHeatpumpFloatSensor(
            "idm_thermische_leistung",
            "thermische_leistung",
            REG_THERMAL_POWER,
            UnitOfPower.KILO_WATT,
            client,
            host,
            SensorDeviceClass.POWER,
            SensorStateClass.MEASUREMENT,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_solar_leistung",
            "solar_leistung",
            REG_SOLAR_POWER,
            UnitOfPower.KILO_WATT,
            client,
            host,
            SensorDeviceClass.POWER,
            SensorStateClass.MEASUREMENT,
            interval,
        ),

        # Solar-Temperaturen
        IDMHeatpumpFloatSensor(
            "idm_solar_kollektor",
            "solar_kollektor",
            REG_SOLAR_COLLECTOR_TEMP,
            UnitOfTemperature.CELSIUS,
            client,
            host,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_solar_ruecklauf",
            "solar_ruecklauf",
            REG_SOLAR_RETURN_TEMP,
            UnitOfTemperature.CELSIUS,
            client,
            host,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
            interval,
        ),
        IDMHeatpumpFloatSensor(
            "idm_solar_ladetemp",
            "solar_ladetemp",
            REG_SOLAR_CHARGE_TEMP,
            UnitOfTemperature.CELSIUS,
            client,
            host,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
            interval,
        ),
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
    def __init__(
        self,
        unique_id,
        translation_key,
        register,
        unit,
        client,
        host,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
        interval=30,
        entity_category=None,
    ):
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
        if value is None:
            return

        # Für TOTAL_INCREASING sind negative Werte ungültig (z. B. -1.0 = "keine Daten").
        # In diesem Fall den letzten gültigen Wert beibehalten und nichts aktualisieren.
        if (
            self._attr_state_class == SensorStateClass.TOTAL_INCREASING
            and value < 0
        ):
            return

        self._attr_native_value = value


# -------------------------------------------------------------------
# Durchflusssensor (B2 / REG_FLOW_SENSOR) – UCHAR mit 0,1-l/min-Skalierung
# -------------------------------------------------------------------
class IDMHeatpumpFlowSensor(IDMBaseEntity, SensorEntity):
    def __init__(
        self,
        unique_id,
        translation_key,
        register,
        client,
        host,
        interval=30,
        entity_category=None,
    ):
        super().__init__(host)
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._attr_has_entity_name = True
        self._register = register
        self._client = client
        self._attr_native_unit_of_measurement = "l/min"
        self._attr_native_value = None
        self._attr_device_class = None
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_scan_interval = timedelta(seconds=interval)
        self._attr_entity_category = entity_category

    async def async_update(self):
        raw = await self._client.read_uchar(self._register)
        if raw is None:
            return

        # 0,1-l/min-Skalierung: 172 -> 17,2 l/min; 255 als Fehlerwert behandeln
        if raw == 255:
            self._attr_native_value = None
        else:
            self._attr_native_value = round(raw / 10.0, 1)


# -------------------------------------------------------------------
# Interne Meldung (UCHAR) mit Klartext + Event/Notification
# -------------------------------------------------------------------
class IDMHeatpumpInternalMessageSensor(IDMBaseEntity, SensorEntity):
    def __init__(
        self,
        unique_id,
        translation_key,
        register,
        client,
        host,
        interval=30,
        entity_category=None,
    ):
        super().__init__(host)
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._attr_has_entity_name = True
        self._register = register
        self._client = client
        self._attr_native_value = None  # numerischer Code
        self._last_code = None
        self._attr_device_class = None
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_scan_interval = timedelta(seconds=interval)
        self._attr_entity_category = entity_category

    async def async_update(self):
        code = await self._client.read_uchar(self._register)
        if code is None:
            return

        code = int(code)
        self._attr_native_value = code

        if self._last_code is None:
            self._last_code = code
            return

        if code != self._last_code:
            text = code_to_text(code)
            self.hass.bus.async_fire(
                "idm_internal_message_changed",
                {"code": code, "text": text},
            )
            pn_create(
                self.hass,
                f"Code {code:03d} – {text}",
                title="iDM interne Meldung",
            )
            self._last_code = code

    @property
    def extra_state_attributes(self):
        code = self._attr_native_value
        return {"code_text": code_to_text(int(code)) if code is not None else None}

    @property
    def icon(self):
        code = self._attr_native_value or 0
        return "mdi:information-outline" if code == 0 else "mdi:alert-circle-outline"


# -------------------------------------------------------------------
# Word-Sensor
# -------------------------------------------------------------------
class IDMHeatpumpWordSensor(IDMBaseEntity, SensorEntity):
    def __init__(
        self,
        unique_id,
        translation_key,
        register,
        unit,
        client,
        host,
        interval=30,
        entity_category=None,
    ):
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
# Status-Sensor Wärmepumpe (1091)
# -------------------------------------------------------------------
class IDMHeatpumpStatusSensor(IDMBaseEntity, SensorEntity):
    def __init__(
        self,
        unique_id,
        translation_key,
        register,
        client,
        host,
        interval=30,
    ):
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
        if self._attr_native_value == "Heizbetrieb":
            return "mdi:radiator"
        return "mdi:alert-circle-outline"


# -------------------------------------------------------------------
# Aktive Betriebsart Heizkreis A/C
# -------------------------------------------------------------------
class IDMHeatpumpActiveModeSensor(IDMBaseEntity, SensorEntity):
    def __init__(
        self,
        unique_id,
        translation_key,
        register,
        client,
        host,
        interval=30,
    ):
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
        if self._attr_native_value == "Heizen":
            return "mdi:radiator"
        if self._attr_native_value == "Kühlen":
            return "mdi:snowflake"
        return "mdi:alert-circle-outline"


# -------------------------------------------------------------------
# Betriebsart Wärmepumpe (1090)
# -------------------------------------------------------------------
class IDMHeatpumpWpModeSensor(IDMBaseEntity, SensorEntity):
    def __init__(
        self,
        unique_id,
        translation_key,
        register,
        client,
        host,
        interval=30,
    ):
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
        mapping = {
            0: "Bereit",
            1: "Heizbetrieb",
            2: "Kühlbetrieb",
            3: "Unbekannt",
            4: "Warmwasser",
            8: "Abtauen",
        }
        self._attr_native_value = mapping.get(value, f"Unbekannt ({value})")

    @property
    def icon(self):
        return {
            "Bereit": "mdi:power-standby",
            "Heizbetrieb": "mdi:radiator",
            "Kühlbetrieb": "mdi:snowflake",
            "Abtauen": "mdi:water-sync",
            "Warmwasser": "mdi:water-boiler",
            "Unbekannt": "mdi:alert-circle-outline",
        }.get(self._attr_native_value, "mdi:alert-circle-outline")
