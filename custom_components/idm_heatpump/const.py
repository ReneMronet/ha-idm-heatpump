DOMAIN = "idm_heatpump"
DEFAULT_NAME = "iDM Navigator 10"
DEFAULT_PORT = 502
DEFAULT_SLAVE = 1
DEFAULT_SCAN_INTERVAL = 30

# Configuration keys
CONF_HOST = "host"
CONF_PORT = "port"
CONF_UNIT_ID = "unit_id"
CONF_SCAN_INTERVAL = "scan_interval"

# iDM Navigator 2.0 Betriebsmodi
SYSTEM_MODES = {
    0: "Standby",
    1: "Automatik", 
    2: "Abwesend",
    4: "Nur Warmwasser",
    5: "Nur Heizung/Kühlung"
}

HEATPUMP_MODES = {
    0: "Aus",
    1: "Heizbetrieb",
    2: "Kühlbetrieb", 
    4: "Warmwasser",
    8: "Abtauung"
}

HEATING_CIRCUIT_MODES = {
    0: "Aus",
    1: "Zeitprogramm",
    2: "Normal",
    3: "Eco",
    4: "Manuell Heizen",
    5: "Manuell Kühlen"
}

SMART_GRID_STATUS = {
    0: "EVU-Sperre + kein PV-Ertrag",
    1: "EVU-Bezug + kein PV-Ertrag", 
    2: "Kein EVU-Bezug + PV-Ertrag",
    4: "EVU-Sperre + PV-Ertrag"
}

ACTIVE_HEATING_MODES = {
    0: "Aus",
    1: "Heizen", 
    2: "Kühlen"
}

# Modbus Register Definition basierend auf iDM Navigator 2.0 Dokumentation
MODBUS_REGISTERS = {
    # Temperaturen (Input Registers - FLOAT)
    "outdoor_temperature": {
        "address": 0,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "state_class": "measurement",
        "name": "Außentemperatur",
        "icon": "mdi:thermometer",
        "precision": 1,
        "entity_category": None
    },
    "outdoor_temperature_avg": {
        "address": 2,
        "type": "input", 
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "state_class": "measurement",
        "name": "Gemittelte Außentemperatur",
        "icon": "mdi:thermometer",
        "precision": 1,
        "entity_category": EntityCategory.DIAGNOSTIC
    },
    "heat_storage_temperature": {
        "address": 8,
        "type": "input",
        "data_type": "float32", 
        "swap": "word",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "state_class": "measurement",
        "name": "Wärmespeichertemperatur",
        "icon": "mdi:thermometer",
        "precision": 1,
        "entity_category": None
    },
    "cold_storage_temperature": {
        "address": 10,
        "type": "input",
        "data_type": "float32",
        "swap": "word", 
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "state_class": "measurement",
        "name": "Kältespeichertemperatur",
        "icon": "mdi:thermometer",
        "precision": 1,
        "entity_category": None
    },
    "dhw_temperature_bottom": {
        "address": 12,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "state_class": "measurement", 
        "name": "Warmwasser unten",
        "icon": "mdi:water-thermometer",
        "precision": 1,
        "entity_category": None
    },
    "dhw_temperature_top": {
        "address": 14,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "state_class": "measurement",
        "name": "Warmwasser oben", 
        "icon": "mdi:water-thermometer",
        "precision": 1,
        "entity_category": None
    },
    "dhw_tap_temperature": {
        "address": 30,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "state_class": "measurement",
        "name": "Warmwasser Zapftemperatur",
        "icon": "mdi:water-thermometer",
        "precision": 1,
        "entity_category": None
    },
    "heatpump_supply_temperature": {
        "address": 50,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "state_class": "measurement",
        "name": "Wärmepumpe Vorlauftemperatur",
        "icon": "mdi:thermometer",
        "precision": 1,
        "entity_category": None
    },
    "heatpump_return_temperature": {
        "address": 52,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "state_class": "measurement",
        "name": "Wärmepumpe Rücklauftemperatur",
        "icon": "mdi:thermometer",
        "precision": 1,
        "entity_category": None
    },
    "hgl_supply_temperature": {
        "address": 54,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "state_class": "measurement",
        "name": "HGL Vorlauftemperatur",
        "icon": "mdi:thermometer",
        "precision": 1,
        "entity_category": EntityCategory.DIAGNOSTIC
    },
    "heat_source_inlet_temperature": {
        "address": 56,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "state_class": "measurement",
        "name": "Wärmequelle Eintritt",
        "icon": "mdi:thermometer",
        "precision": 1,
        "entity_category": None
    },
    "heat_source_outlet_temperature": {
        "address": 58,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "state_class": "measurement",
        "name": "Wärmequelle Austritt",
        "icon": "mdi:thermometer",
        "precision": 1,
        "entity_category": None
    },
    "air_intake_temperature": {
        "address": 60,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "state_class": "measurement",
        "name": "Luftansaugtemperatur",
        "icon": "mdi:thermometer",
        "precision": 1,
        "entity_category": EntityCategory.DIAGNOSTIC
    },
    "air_heat_exchanger_temperature": {
        "address": 62,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "state_class": "measurement",
        "name": "Luftwärmetauscher",
        "icon": "mdi:thermometer",
        "precision": 1,
        "entity_category": EntityCategory.DIAGNOSTIC
    },
    "heating_circuit_a_supply_temperature": {
        "address": 350,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "state_class": "measurement",
        "name": "Heizkreis A Vorlauf",
        "icon": "mdi:thermometer",
        "precision": 1,
        "entity_category": None
    },
    "heating_circuit_a_room_temperature": {
        "address": 364,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "state_class": "measurement",
        "name": "Heizkreis A Raumtemperatur",
        "icon": "mdi:home-thermometer",
        "precision": 1,
        "entity_category": None
    },
    "heating_circuit_a_target_supply_temperature": {
        "address": 378,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "state_class": "measurement",
        "name": "Heizkreis A Soll-Vorlauf",
        "icon": "mdi:thermometer",
        "precision": 1,
        "entity_category": EntityCategory.DIAGNOSTIC
    },
    "humidity_sensor": {
        "address": 392,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": PERCENTAGE,
        "device_class": "humidity",
        "state_class": "measurement",
        "name": "Luftfeuchtigkeit",
        "icon": "mdi:water-percent",
        "precision": 0,
        "entity_category": None
    },
    
    # Status Register (Input Registers - UINT16) - KORRIGIERT ALS TEXT-SENSOREN
    "current_error_number": {
        "address": 4,
        "type": "input",
        "data_type": "uint16",
        "name": "Aktuelle Störungsnummer",
        "icon": "mdi:alert-circle",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "device_class": None,
        "state_class": None,
        "unit": None,
        "precision": None
    },
    "smart_grid_status": {
        "address": 6,
        "type": "input",
        "data_type": "uint16",
        "name": "Smart Grid Status",
        "icon": "mdi:solar-power",
        "options": SMART_GRID_STATUS,
        "entity_category": None,
        "device_class": None,
        "state_class": None,
        "unit": None,
        "precision": None
    },
    "heatpump_operating_mode": {
        "address": 90,
        "type": "input",
        "data_type": "uint16",
        "name": "Wärmepumpe Betriebsart",
        "icon": "mdi:heat-pump",
        "options": HEATPUMP_MODES,
        "entity_category": None,
        "device_class": None,
        "state_class": None,
        "unit": None,
        "precision": None
    },
    "heatpump_malfunction_summary": {
        "address": 99,
        "type": "input",
        "data_type": "uint16",
        "name": "Summenstörung Wärmepumpe",
        "icon": "mdi:alert",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "device_class": None,
        "state_class": None,
        "unit": None,
        "precision": None
    },
    "compressor_1_status": {
        "address": 100,
        "type": "input",
        "data_type": "uint16",
        "name": "Verdichter 1 Status",
        "icon": "mdi:engine",
        "entity_category": None,
        "device_class": None,
        "state_class": None,
        "unit": None,
        "precision": None
    },
    "compressor_2_status": {
        "address": 101,
        "type": "input",
        "data_type": "uint16",
        "name": "Verdichter 2 Status",
        "icon": "mdi:engine",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "device_class": None,
        "state_class": None,
        "unit": None,
        "precision": None
    },
    "charging_pump_status": {
        "address": 104,
        "type": "input",
        "data_type": "uint16",
        "unit": PERCENTAGE,
        "state_class": "measurement",
        "name": "Ladepumpe Status",
        "icon": "mdi:pump",
        "precision": 0,
        "entity_category": None
    },
    "brine_pump_status": {
        "address": 105,
        "type": "input",
        "data_type": "uint16",
        "unit": PERCENTAGE,
        "state_class": "measurement",
        "name": "Sole-/Zwischenkreispumpe",
        "icon": "mdi:pump",
        "precision": 0,
        "entity_category": None
    },
    "heat_source_pump_status": {
        "address": 106,
        "type": "input",
        "data_type": "uint16",
        "unit": PERCENTAGE,
        "state_class": "measurement",
        "name": "Wärmequellenpumpe",
        "icon": "mdi:pump",
        "precision": 0,
        "entity_category": None
    },
    "heating_circuit_a_active_mode": {
        "address": 498,
        "type": "input",
        "data_type": "uint16",
        "name": "Heizkreis A aktive Betriebsart",
        "icon": "mdi:radiator",
        "options": ACTIVE_HEATING_MODES,
        "entity_category": None,
        "device_class": None,
        "state_class": None,
        "unit": None,
        "precision": None
    },
    
    # Energiewerte (Input Registers - FLOAT)
    "heating_energy": {
        "address": 750,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "device_class": "energy",
        "state_class": "total_increasing",
        "name": "Wärmemenge Heizen",
        "icon": "mdi:fire"
    },
    "cooling_energy": {
        "address": 752,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "device_class": "energy", 
        "state_class": "total_increasing",
        "name": "Wärmemenge Kühlen",
        "icon": "mdi:snowflake"
    },
    "dhw_energy": {
        "address": 754,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "device_class": "energy",
        "state_class": "total_increasing", 
        "name": "Wärmemenge Warmwasser",
        "icon": "mdi:water-boiler"
    },
    "current_power": {
        "address": 790,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfPower.KILO_WATT,
        "device_class": "power",
        "state_class": "measurement",
        "name": "Momentanleistung",
        "icon": "mdi:lightning-bolt"
    },
    "power_consumption": {
        "address": 1122,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfPower.KILO_WATT,
        "device_class": "power",
        "state_class": "measurement",
        "name": "Leistungsaufnahme Wärmepumpe",
        "icon": "mdi:flash"
    },
    
    # PV Integration (Input Registers - FLOAT)
    "pv_excess_power": {
        "address": 74,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfPower.KILO_WATT,
        "device_class": "power",
        "state_class": "measurement",
        "name": "PV-Überschuss",
        "icon": "mdi:solar-power"
    },
    "pv_production": {
        "address": 78,
        "type": "input",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfPower.KILO_WATT,
        "device_class": "power",
        "state_class": "measurement",
        "name": "PV-Produktion",
        "icon": "mdi:solar-panel"
    },
    
    # Sollwerte und Einstellungen (Holding Registers)
    "system_operating_mode": {
        "address": 5,
        "type": "holding",
        "data_type": "uint16",
        "name": "System Betriebsart",
        "icon": "mdi:cog",
        "options": SYSTEM_MODES,
        "min": 0,
        "max": 5,
        "entity_type": "select"
    },
    "dhw_target_temperature": {
        "address": 32,
        "type": "holding",
        "data_type": "uint16",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "name": "Warmwasser Solltemperatur",
        "icon": "mdi:water-thermometer",
        "min": 35,
        "max": 95,
        "entity_type": "number"
    },
    "dhw_switch_on_temperature": {
        "address": 33,
        "type": "holding",
        "data_type": "uint16",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "name": "Warmwasser Einschalttemperatur",
        "icon": "mdi:water-thermometer",
        "min": 30,
        "max": 50,
        "entity_type": "number"
    },
    "dhw_switch_off_temperature": {
        "address": 34,
        "type": "holding",
        "data_type": "uint16",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "name": "Warmwasser Ausschalttemperatur",
        "icon": "mdi:water-thermometer",
        "min": 46,
        "max": 53,
        "entity_type": "number"
    },
    "heating_circuit_a_operating_mode": {
        "address": 393,
        "type": "holding",
        "data_type": "uint16",
        "name": "Heizkreis A Betriebsart",
        "icon": "mdi:radiator",
        "options": HEATING_CIRCUIT_MODES,
        "min": 0,
        "max": 5,
        "entity_type": "select"
    },
    "heating_circuit_a_room_setpoint_normal": {
        "address": 401,
        "type": "holding",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "name": "Heizkreis A Raumsolltemperatur Normal",
        "icon": "mdi:home-thermometer",
        "min": 15,
        "max": 30,
        "step": 0.5,
        "entity_type": "number"
    },
    "heating_circuit_a_room_setpoint_eco": {
        "address": 415,
        "type": "holding",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "name": "Heizkreis A Raumsolltemperatur Eco",
        "icon": "mdi:home-thermometer",
        "min": 10,
        "max": 25,
        "step": 0.5,
        "entity_type": "number"
    },
    "heating_circuit_a_heating_curve": {
        "address": 429,
        "type": "holding",
        "data_type": "float32",
        "swap": "word",
        "name": "Heizkreis A Heizkurve",
        "icon": "mdi:chart-line",
        "min": 0.1,
        "max": 3.5,
        "step": 0.1,
        "entity_type": "number"
    },
    "heating_circuit_a_heating_limit": {
        "address": 442,
        "type": "holding",
        "data_type": "uint16",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "name": "Heizkreis A Heizgrenze",
        "icon": "mdi:thermometer",
        "min": 0,
        "max": 50,
        "entity_type": "number"
    },
    "heating_circuit_a_constant_supply_temperature": {
        "address": 449,
        "type": "holding",
        "data_type": "uint16",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "name": "Heizkreis A Konstant-Vorlauftemperatur",
        "icon": "mdi:thermometer",
        "min": 20,
        "max": 90,
        "entity_type": "number"
    },
    
    # Externe Steuerung (Holding Registers)
    "external_room_temperature_hc_a": {
        "address": 650,
        "type": "holding",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "name": "Externe Raumtemperatur HK A",
        "icon": "mdi:thermometer",
        "min": 15,
        "max": 30,
        "step": 0.1,
        "entity_type": "number"
    },
    "external_outdoor_temperature": {
        "address": 690,
        "type": "holding",
        "data_type": "float32",
        "swap": "word",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "name": "Externe Außentemperatur",
        "icon": "mdi:thermometer",
        "min": -30,
        "max": 50,
        "step": 0.1,
        "entity_type": "number"
    },
    "external_humidity": {
        "address": 692,
        "type": "holding",
        "data_type": "float32",
        "swap": "word",
        "unit": PERCENTAGE,
        "device_class": "humidity",
        "name": "Externe Luftfeuchtigkeit",
        "icon": "mdi:water-percent",
        "min": 0,
        "max": 100,
        "step": 0.1,
        "entity_type": "number"
    },
    "external_heating_request_temperature": {
        "address": 694,
        "type": "holding",
        "data_type": "uint16",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "name": "Externe Heizanforderungstemperatur",
        "icon": "mdi:thermometer",
        "min": 20,
        "max": 65,
        "entity_type": "number"
    },
    "external_cooling_request_temperature": {
        "address": 695,
        "type": "holding",
        "data_type": "uint16",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "name": "Externe Kühlanforderungstemperatur",
        "icon": "mdi:thermometer",
        "min": 10,
        "max": 25,
        "entity_type": "number"
    },
    "heating_request": {
        "address": 710,
        "type": "holding",
        "data_type": "uint16",
        "name": "Heizanforderung",
        "icon": "mdi:fire",
        "entity_type": "switch"
    },
    "cooling_request": {
        "address": 711,
        "type": "holding",
        "data_type": "uint16",
        "name": "Kühlanforderung",
        "icon": "mdi:snowflake",
        "entity_type": "switch"
    },
    "dhw_request": {
        "address": 712,
        "type": "holding",
        "data_type": "uint16",
        "name": "Warmwasseranforderung",
        "icon": "mdi:water-boiler",
        "entity_type": "switch"
    }
}
DEFAULT_UNIT = 1
PLATFORMS = ["sensor", "number", "switch", "binary_sensor"]
SCAN_INTERVAL = 20
