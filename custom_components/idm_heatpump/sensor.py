"""
iDM Wärmepumpe (Modbus TCP)
Version: v5.0
Stand: 2026-02-26

Änderungen v5.0 (Schritt 2 – Neue Features):
- Neue Sensoren: SmartGrid, Verdichter, Ladepumpe, EVU-Sperre, Summenstörung,
  Kühlanforderung, WW-Anforderung WP, Umschaltventil, Zirkulation, Variabler Eingang,
  Strompreis, Luftwärmetauscher, Wärmesenke VL/RL, Kältespeicher, Feuchte,
  Raumtemperatur pro HK
- Sensor-Gruppen: Entities werden nur erzeugt wenn Gruppe aktiv
- Auto-Detect: IDMAutoDetectFloatSensor wird unavailable wenn Fühler nicht verbaut
- Default-Disabled: Diagnose-Entities (entity_registry_enabled_default=False)
"""

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
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    DEFAULT_HEATING_CIRCUITS,
    DEFAULT_SENSOR_GROUPS,
    INVALID_FLOAT,
    AUTO_DETECT_THRESHOLD,
    hc_reg,
    get_device_info,
    # Basis-Register
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
    REG_INTERNAL_MESSAGE,
    REG_THERMAL_POWER,
    REG_WP_MODE,
    REG_WP_POWER,
    REG_WP_STATUS,
    REG_EN_COOLING,
    REG_EN_DEFROST,
    REG_EN_DHW,
    REG_EN_EHEATER,
    REG_EN_HEATING,
    REG_EN_PASSIVE_COOL,
    REG_EN_SOLAR,
    REG_EN_TOTAL,
    # Solar-Gruppe
    REG_SOLAR_CHARGE_TEMP,
    REG_SOLAR_COLLECTOR_TEMP,
    REG_SOLAR_POWER,
    REG_SOLAR_RETURN_TEMP,
    # PV/Batterie-Gruppe
    REG_BATTERIE_ENTLADUNG,
    REG_BATTERIE_FUELLSTAND,
    REG_EHEIZSTAB,
    REG_HAUSVERBRAUCH,
    REG_PV_PRODUKTION,
    REG_PV_SURPLUS,
    REG_SMARTGRID_STATUS,
    REG_CURRENT_ELEC_PRICE,
    # Kühlungs-Gruppe
    REG_COOLING_REQUEST_WP,
    REG_WW_REQUEST_WP,
    # Diagnose-Gruppe
    REG_FAULT_SUMMARY,
    REG_EVU_LOCK,
    REG_COMPRESSOR_1,
    REG_CHARGE_PUMP,
    REG_VARIABLE_INPUT,
    REG_SWITCH_VALVE_HC,
    REG_CIRC_PUMP,
    # Einzelraumregelung-Gruppe
    REG_HUMIDITY_SENSOR,
    # Erweiterte Temperaturen-Gruppe
    REG_HEAT_EXCHANGER_TEMP,
    REG_HEATSINK_RETURN,
    REG_HEATSINK_SUPPLY,
    REG_COLD_STORAGE_TEMP,
)


# -------------------------------------------------------------------
# Meldungscodes (unverändert)
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


# SmartGrid Status Mapping
SMARTGRID_MAP = {
    0: "Aus",
    1: "Normalbetrieb",
    2: "Empfehlung: Einschalten",
    3: "Einschaltbefehl",
    4: "Abschaltbefehl",
}

# Variabler Eingang Mapping
VARIABLE_INPUT_MAP = {
    0: "Keine Funktion",
    1: "EVU-Sperre",
    2: "Sperre Verdichter",
    3: "Externer Fehler",
    4: "Sommerbetrieb",
    5: "Winterbetrieb",
}


# -------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------
async def async_setup_entry(hass, entry, async_add_entities):
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    host = entry_data["host"]
    heating_circuits = entry_data.get("heating_circuits", DEFAULT_HEATING_CIRCUITS)
    sensor_groups = entry_data.get("sensor_groups", DEFAULT_SENSOR_GROUPS)

    sensors = []

    # ===================================================================
    # BASIS-SENSOREN (immer aktiv)
    # ===================================================================
    sensors.extend([
        # Außentemperaturen
        IDMFloatSensor(coordinator, host, "idm_aussentemperatur", "aussentemperatur",
                       REG_OUTDOOR_TEMP, UnitOfTemperature.CELSIUS,
                       SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
        IDMFloatSensor(coordinator, host, "idm_aussentemperatur_gemittelt", "aussentemperatur_gemittelt",
                       REG_OUTDOOR_TEMP_AVG, UnitOfTemperature.CELSIUS,
                       SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),

        # Wärmepumpe direkt
        IDMFloatSensor(coordinator, host, "idm_wp_vorlauf", "wp_vorlauf",
                       REG_WP_VL_TEMP, UnitOfTemperature.CELSIUS,
                       SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
        IDMFloatSensor(coordinator, host, "idm_ruecklauf", "ruecklauf",
                       REG_RETURN_TEMP, UnitOfTemperature.CELSIUS,
                       SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
        IDMFloatSensor(coordinator, host, "idm_ladefuehler", "ladefuehler",
                       REG_LOAD_TEMP, UnitOfTemperature.CELSIUS,
                       SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
        IDMFlowSensor(coordinator, host, "idm_durchfluss", "durchfluss", REG_FLOW_SENSOR),
        IDMFloatSensor(coordinator, host, "idm_luftansaug", "luftansaug",
                       REG_AIR_INLET_TEMP, UnitOfTemperature.CELSIUS,
                       SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
        IDMFloatSensor(coordinator, host, "idm_luftansaug_2", "luftansaug_2",
                       REG_AIR_INLET_TEMP_2, UnitOfTemperature.CELSIUS,
                       SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),

        # Wärmespeicher / Warmwasser
        IDMFloatSensor(coordinator, host, "idm_waermespeicher", "waermespeicher",
                       REG_HEATBUFFER_TEMP, UnitOfTemperature.CELSIUS,
                       SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
        IDMFloatSensor(coordinator, host, "idm_ww_oben", "ww_oben",
                       REG_WW_TOP_TEMP, UnitOfTemperature.CELSIUS,
                       SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
        IDMFloatSensor(coordinator, host, "idm_ww_unten", "ww_unten",
                       REG_WW_BOTTOM_TEMP, UnitOfTemperature.CELSIUS,
                       SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
        IDMFloatSensor(coordinator, host, "idm_ww_zapftemp", "ww_zapftemp",
                       REG_WW_TAP_TEMP, UnitOfTemperature.CELSIUS,
                       SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),

        # System: Interne Meldung
        IDMInternalMessageSensor(coordinator, host, "idm_interne_meldung", "interne_meldung",
                                 REG_INTERNAL_MESSAGE,
                                 entity_category=EntityCategory.DIAGNOSTIC),

        # Betriebsart + Status WP
        IDMMappedSensor(
            coordinator, host,
            "idm_betriebsart_warmepumpe", "betriebsart_warmepumpe",
            REG_WP_MODE,
            {0: "Bereit", 1: "Heizbetrieb", 2: "Kühlbetrieb", 3: "Unbekannt",
             4: "Warmwasser", 8: "Abtauen"},
            icon_map={
                "Bereit": "mdi:power-standby",
                "Heizbetrieb": "mdi:radiator",
                "Kühlbetrieb": "mdi:snowflake",
                "Abtauen": "mdi:water-sync",
                "Warmwasser": "mdi:water-boiler",
            },
        ),
        IDMMappedSensor(
            coordinator, host,
            "idm_status_warmepumpe", "status_warmepumpe",
            REG_WP_STATUS,
            {0: "Bereit", 1: "Heizbetrieb"},
            icon_map={
                "Bereit": "mdi:power-standby",
                "Heizbetrieb": "mdi:radiator",
            },
        ),

        # Leistungen
        IDMFloatSensor(coordinator, host, "idm_wp_power", "wp_power",
                       REG_WP_POWER, UnitOfPower.KILO_WATT,
                       SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
        IDMFloatSensor(coordinator, host, "idm_thermische_leistung", "thermische_leistung",
                       REG_THERMAL_POWER, UnitOfPower.KILO_WATT,
                       SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),

        # Energiemengen
        IDMFloatSensor(coordinator, host, "idm_en_heizen", "en_heizen",
                       REG_EN_HEATING, UnitOfEnergy.KILO_WATT_HOUR,
                       SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        IDMFloatSensor(coordinator, host, "idm_en_gesamt", "en_gesamt",
                       REG_EN_TOTAL, UnitOfEnergy.KILO_WATT_HOUR,
                       SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        IDMFloatSensor(coordinator, host, "idm_en_kuehlen", "en_kuehlen",
                       REG_EN_COOLING, UnitOfEnergy.KILO_WATT_HOUR,
                       SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        IDMFloatSensor(coordinator, host, "idm_en_warmwasser", "en_warmwasser",
                       REG_EN_DHW, UnitOfEnergy.KILO_WATT_HOUR,
                       SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        IDMFloatSensor(coordinator, host, "idm_en_abtauung", "en_abtauung",
                       REG_EN_DEFROST, UnitOfEnergy.KILO_WATT_HOUR,
                       SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        IDMFloatSensor(coordinator, host, "idm_en_passivkuehlung", "en_passivkuehlung",
                       REG_EN_PASSIVE_COOL, UnitOfEnergy.KILO_WATT_HOUR,
                       SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        IDMFloatSensor(coordinator, host, "idm_en_solar", "en_solar",
                       REG_EN_SOLAR, UnitOfEnergy.KILO_WATT_HOUR,
                       SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        IDMFloatSensor(coordinator, host, "idm_en_eheizer", "en_eheizer",
                       REG_EN_EHEATER, UnitOfEnergy.KILO_WATT_HOUR,
                       SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    ])

    # Dynamische Heizkreis-Sensoren (Basis – immer)
    for hc in heating_circuits:
        key = hc.lower()
        sensors.extend([
            IDMFloatSensor(
                coordinator, host,
                f"idm_hk{key}_vorlauftemperatur", f"hk{key}_vorlauf",
                hc_reg(hc, "vl"), UnitOfTemperature.CELSIUS,
                SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT,
            ),
            IDMFloatSensor(
                coordinator, host,
                f"idm_hk{key}_soll_vorlauf", f"hk{key}_soll_vorlauf",
                hc_reg(hc, "vl_soll"), UnitOfTemperature.CELSIUS,
                SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT,
            ),
            IDMMappedSensor(
                coordinator, host,
                f"idm_hk{key}_aktive_betriebsart", f"hk{key}_aktive_betriebsart",
                hc_reg(hc, "active_mode"),
                {0: "Aus", 1: "Heizen", 2: "Kühlen"},
                icon_map={
                    "Aus": "mdi:power-standby",
                    "Heizen": "mdi:radiator",
                    "Kühlen": "mdi:snowflake",
                },
            ),
        ])

    # ===================================================================
    # SOLAR-GRUPPE
    # ===================================================================
    if "solar" in sensor_groups:
        sensors.extend([
            IDMFloatSensor(coordinator, host, "idm_solar_kollektor", "solar_kollektor",
                           REG_SOLAR_COLLECTOR_TEMP, UnitOfTemperature.CELSIUS,
                           SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
            IDMFloatSensor(coordinator, host, "idm_solar_ruecklauf", "solar_ruecklauf",
                           REG_SOLAR_RETURN_TEMP, UnitOfTemperature.CELSIUS,
                           SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
            IDMFloatSensor(coordinator, host, "idm_solar_ladetemp", "solar_ladetemp",
                           REG_SOLAR_CHARGE_TEMP, UnitOfTemperature.CELSIUS,
                           SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
            IDMFloatSensor(coordinator, host, "idm_solar_leistung", "solar_leistung",
                           REG_SOLAR_POWER, UnitOfPower.KILO_WATT,
                           SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
        ])

    # ===================================================================
    # PV / BATTERIE-GRUPPE
    # ===================================================================
    if "pv_battery" in sensor_groups:
        sensors.extend([
            IDMFloatSensor(coordinator, host, "idm_pv_ueberschuss", "pv_ueberschuss",
                           REG_PV_SURPLUS, UnitOfPower.KILO_WATT,
                           SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
            IDMFloatSensor(coordinator, host, "idm_e_heizstab", "e_heizstab",
                           REG_EHEIZSTAB, UnitOfPower.KILO_WATT,
                           SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
            IDMFloatSensor(coordinator, host, "idm_pv_produktion", "pv_produktion",
                           REG_PV_PRODUKTION, UnitOfPower.KILO_WATT,
                           SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
            IDMFloatSensor(coordinator, host, "idm_hausverbrauch", "hausverbrauch",
                           REG_HAUSVERBRAUCH, UnitOfPower.KILO_WATT,
                           SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
            IDMFloatSensor(coordinator, host, "idm_batterie_entladung", "batterie_entladung",
                           REG_BATTERIE_ENTLADUNG, UnitOfPower.KILO_WATT,
                           SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
            IDMWordSensor(coordinator, host, "idm_batterie_fuellstand", "batterie_fuellstand",
                          REG_BATTERIE_FUELLSTAND, PERCENTAGE,
                          entity_category=EntityCategory.DIAGNOSTIC),
            # NEU: SmartGrid Status
            IDMMappedSensor(
                coordinator, host,
                "idm_smartgrid_status", "smartgrid_status",
                REG_SMARTGRID_STATUS,
                SMARTGRID_MAP,
                icon_map={
                    "Aus": "mdi:transmission-tower-off",
                    "Normalbetrieb": "mdi:transmission-tower",
                    "Empfehlung: Einschalten": "mdi:flash",
                    "Einschaltbefehl": "mdi:flash-alert",
                    "Abschaltbefehl": "mdi:flash-off",
                },
            ),
            # NEU: Aktueller Strompreis
            IDMFloatSensor(coordinator, host, "idm_strompreis", "strompreis",
                           REG_CURRENT_ELEC_PRICE, "ct/kWh",
                           None, SensorStateClass.MEASUREMENT),
        ])

    # ===================================================================
    # KÜHLUNGS-GRUPPE (Sensoren)
    # ===================================================================
    if "cooling" in sensor_groups:
        sensors.extend([
            IDMMappedSensor(
                coordinator, host,
                "idm_kuehlanforderung_wp", "kuehlanforderung_wp",
                REG_COOLING_REQUEST_WP,
                {0: "Keine Anforderung", 1: "Anforderung aktiv"},
                icon_map={
                    "Keine Anforderung": "mdi:snowflake-off",
                    "Anforderung aktiv": "mdi:snowflake-alert",
                },
            ),
            IDMMappedSensor(
                coordinator, host,
                "idm_ww_anforderung_wp", "ww_anforderung_wp",
                REG_WW_REQUEST_WP,
                {0: "Keine Anforderung", 1: "Anforderung aktiv"},
                icon_map={
                    "Keine Anforderung": "mdi:water-boiler-off",
                    "Anforderung aktiv": "mdi:water-boiler-alert",
                },
            ),
        ])

    # ===================================================================
    # DIAGNOSE-GRUPPE (Default-Disabled!)
    # ===================================================================
    if "diagnostic" in sensor_groups:
        sensors.extend([
            # Summenstörung
            IDMMappedSensor(
                coordinator, host,
                "idm_summenstoerung", "summenstoerung",
                REG_FAULT_SUMMARY,
                {0: "Keine Störung", 1: "Störung aktiv"},
                icon_map={
                    "Keine Störung": "mdi:check-circle-outline",
                    "Störung aktiv": "mdi:alert-circle",
                },
                entity_category=EntityCategory.DIAGNOSTIC,
                default_enabled=False,
            ),
            # EVU-Sperrkontakt
            IDMMappedSensor(
                coordinator, host,
                "idm_evu_sperre", "evu_sperre",
                REG_EVU_LOCK,
                {0: "Nicht gesperrt", 1: "Gesperrt"},
                icon_map={
                    "Nicht gesperrt": "mdi:lock-open-outline",
                    "Gesperrt": "mdi:lock",
                },
                entity_category=EntityCategory.DIAGNOSTIC,
                default_enabled=False,
            ),
            # Verdichter 1
            IDMMappedSensor(
                coordinator, host,
                "idm_verdichter_1", "verdichter_1",
                REG_COMPRESSOR_1,
                {0: "Aus", 1: "Ein"},
                icon_map={
                    "Aus": "mdi:engine-off-outline",
                    "Ein": "mdi:engine",
                },
                entity_category=EntityCategory.DIAGNOSTIC,
                default_enabled=False,
            ),
            # Ladepumpe (WORD → %)
            IDMWordSensor(coordinator, host, "idm_ladepumpe", "ladepumpe",
                          REG_CHARGE_PUMP, PERCENTAGE,
                          entity_category=EntityCategory.DIAGNOSTIC,
                          default_enabled=False),
            # Variabler Eingang
            IDMMappedSensor(
                coordinator, host,
                "idm_variabler_eingang", "variabler_eingang",
                REG_VARIABLE_INPUT,
                VARIABLE_INPUT_MAP,
                entity_category=EntityCategory.DIAGNOSTIC,
                default_enabled=False,
            ),
            # Umschaltventil Heizen/Kühlen
            IDMWordSensor(coordinator, host, "idm_umschaltventil", "umschaltventil",
                          REG_SWITCH_VALVE_HC, PERCENTAGE,
                          entity_category=EntityCategory.DIAGNOSTIC,
                          default_enabled=False),
            # Zirkulationspumpe
            IDMWordSensor(coordinator, host, "idm_zirkulationspumpe", "zirkulationspumpe",
                          REG_CIRC_PUMP, PERCENTAGE,
                          entity_category=EntityCategory.DIAGNOSTIC,
                          default_enabled=False),
        ])

    # ===================================================================
    # EINZELRAUMREGELUNG-GRUPPE
    # ===================================================================
    if "room_control" in sensor_groups:
        # Raumtemperatur pro Heizkreis (Auto-Detect!)
        for hc in heating_circuits:
            key = hc.lower()
            sensors.append(
                IDMAutoDetectFloatSensor(
                    coordinator, host,
                    f"idm_hk{key}_raumtemperatur", f"hk{key}_raumtemperatur",
                    hc_reg(hc, "room_temp"), UnitOfTemperature.CELSIUS,
                    SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT,
                )
            )
        # Feuchtesensor (Auto-Detect!)
        sensors.append(
            IDMAutoDetectFloatSensor(
                coordinator, host,
                "idm_feuchtesensor", "feuchtesensor",
                REG_HUMIDITY_SENSOR, PERCENTAGE,
                SensorDeviceClass.HUMIDITY, SensorStateClass.MEASUREMENT,
            )
        )

    # ===================================================================
    # ERWEITERTE TEMPERATUREN-GRUPPE (Auto-Detect!)
    # ===================================================================
    if "extended_temps" in sensor_groups:
        sensors.extend([
            IDMAutoDetectFloatSensor(
                coordinator, host,
                "idm_luftwaermetauscher", "luftwaermetauscher",
                REG_HEAT_EXCHANGER_TEMP, UnitOfTemperature.CELSIUS,
                SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT,
            ),
            IDMAutoDetectFloatSensor(
                coordinator, host,
                "idm_waermesenke_ruecklauf", "waermesenke_ruecklauf",
                REG_HEATSINK_RETURN, UnitOfTemperature.CELSIUS,
                SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT,
            ),
            IDMAutoDetectFloatSensor(
                coordinator, host,
                "idm_waermesenke_vorlauf", "waermesenke_vorlauf",
                REG_HEATSINK_SUPPLY, UnitOfTemperature.CELSIUS,
                SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT,
            ),
            IDMAutoDetectFloatSensor(
                coordinator, host,
                "idm_kaeltespeicher", "kaeltespeicher",
                REG_COLD_STORAGE_TEMP, UnitOfTemperature.CELSIUS,
                SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT,
            ),
        ])

    async_add_entities(sensors)


# -------------------------------------------------------------------
# Entity-Klassen
# -------------------------------------------------------------------

class IDMFloatSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, host, unique_id, translation_key,
                 register, unit, device_class=None,
                 state_class=SensorStateClass.MEASUREMENT,
                 entity_category=None):
        super().__init__(coordinator)
        self._host = host
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._register = register
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_entity_category = entity_category

    @property
    def device_info(self):
        return get_device_info(self._host)

    @property
    def native_value(self):
        value = self.coordinator.data.get(self._register)
        if value is None:
            return None
        if self._attr_state_class == SensorStateClass.TOTAL_INCREASING and value < 0:
            return None
        return value


class IDMAutoDetectFloatSensor(CoordinatorEntity, SensorEntity):
    """Float-Sensor mit Auto-Erkennung nicht verbauter Fühler.

    Wird unavailable wenn nach AUTO_DETECT_THRESHOLD aufeinanderfolgenden
    Lesungen nur ungültige Werte (-1.0) kommen. Wird automatisch wieder
    available sobald gültige Werte empfangen werden.
    """
    _attr_has_entity_name = True

    def __init__(self, coordinator, host, unique_id, translation_key,
                 register, unit, device_class=None,
                 state_class=SensorStateClass.MEASUREMENT):
        super().__init__(coordinator)
        self._host = host
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._register = register
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._invalid_count = 0

    @property
    def device_info(self):
        return get_device_info(self._host)

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        return self._invalid_count < AUTO_DETECT_THRESHOLD

    @property
    def native_value(self):
        value = self.coordinator.data.get(self._register)
        if value is None:
            return None
        return value

    def _handle_coordinator_update(self) -> None:
        value = self.coordinator.data.get(self._register)
        if value is None or value == INVALID_FLOAT:
            self._invalid_count += 1
        else:
            self._invalid_count = 0
        super()._handle_coordinator_update()


class IDMMappedSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, host, unique_id, translation_key,
                 register, value_map, icon_map=None, entity_category=None,
                 default_enabled=True):
        super().__init__(coordinator)
        self._host = host
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._register = register
        self._value_map = value_map
        self._icon_map = icon_map or {}
        self._attr_entity_category = entity_category
        if not default_enabled:
            self._attr_entity_registry_enabled_default = False

    @property
    def device_info(self):
        return get_device_info(self._host)

    @property
    def native_value(self):
        raw = self.coordinator.data.get(self._register)
        if raw is None:
            return None
        return self._value_map.get(raw, f"Unbekannt ({raw})")

    @property
    def icon(self):
        val = self.native_value
        return self._icon_map.get(val, "mdi:alert-circle-outline")


class IDMWordSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, host, unique_id, translation_key,
                 register, unit, entity_category=None, default_enabled=True):
        super().__init__(coordinator)
        self._host = host
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._register = register
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = None
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = entity_category
        if not default_enabled:
            self._attr_entity_registry_enabled_default = False

    @property
    def device_info(self):
        return get_device_info(self._host)

    @property
    def native_value(self):
        return self.coordinator.data.get(self._register)


class IDMFlowSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "l/min"
    _attr_device_class = None
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, host, unique_id, translation_key, register):
        super().__init__(coordinator)
        self._host = host
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._register = register

    @property
    def device_info(self):
        return get_device_info(self._host)

    @property
    def native_value(self):
        raw = self.coordinator.data.get(self._register)
        if raw is None or raw == 255:
            return None
        return round(raw / 10.0, 1)


class IDMInternalMessageSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_device_class = None
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, host, unique_id, translation_key,
                 register, entity_category=None):
        super().__init__(coordinator)
        self._host = host
        self._attr_unique_id = unique_id
        self._attr_translation_key = translation_key
        self._register = register
        self._attr_entity_category = entity_category
        self._last_code = None

    @property
    def device_info(self):
        return get_device_info(self._host)

    @property
    def native_value(self):
        return self.coordinator.data.get(self._register)

    def _handle_coordinator_update(self) -> None:
        code = self.coordinator.data.get(self._register)
        if code is not None:
            code = int(code)
            if self._last_code is not None and code != self._last_code:
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
        super()._handle_coordinator_update()

    @property
    def extra_state_attributes(self):
        code = self.native_value
        return {"code_text": code_to_text(int(code)) if code is not None else None}

    @property
    def icon(self):
        code = self.native_value or 0
        return "mdi:information-outline" if code == 0 else "mdi:alert-circle-outline"
