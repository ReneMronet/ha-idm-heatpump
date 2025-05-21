"""Constants for the iDM Heat Pump integration."""

DOMAIN = "idm_heatpump"
MANUFACTURER = "iDM Energiesysteme GmbH"

# Configuration
CONF_HOST = "host"
CONF_PORT = "port"
CONF_UNIT_ID = "unit_id"
CONF_SCAN_INTERVAL = "scan_interval"

# Defaults
DEFAULT_NAME = "iDM Heat Pump"
DEFAULT_PORT = 502
DEFAULT_UNIT_ID = 1
DEFAULT_SCAN_INTERVAL = 60

# Entity attributes
ATTR_MANUFACTURER = "manufacturer"
ATTR_MODEL = "model"

# Data types
DATA_TYPE_FLOAT = "float32"
DATA_TYPE_UINT8 = "uint8"
DATA_TYPE_UINT16 = "uint16"
DATA_TYPE_INT16 = "int16"

# System operation modes
SYSTEM_MODE_STANDBY = 0
SYSTEM_MODE_AUTO = 1
SYSTEM_MODE_AWAY = 2
SYSTEM_MODE_DHW_ONLY = 4
SYSTEM_MODE_HEATING_COOLING_ONLY = 5

SYSTEM_MODES = {
    SYSTEM_MODE_STANDBY: "Standby",
    SYSTEM_MODE_AUTO: "Auto",
    SYSTEM_MODE_AWAY: "Away",
    SYSTEM_MODE_DHW_ONLY: "Hot Water Only",
    SYSTEM_MODE_HEATING_COOLING_ONLY: "Heating/Cooling Only"
}

# Heat pump operation modes
HP_MODE_OFF = 0
HP_MODE_HEATING = 1
HP_MODE_COOLING = 2
HP_MODE_DHW = 4
HP_MODE_DEFROST = 8

HP_MODES = {
    HP_MODE_OFF: "Off",
    HP_MODE_HEATING: "Heating",
    HP_MODE_COOLING: "Cooling",
    HP_MODE_DHW: "Hot Water",
    HP_MODE_DEFROST: "Defrost"
}

# Heating circuit operation modes
HC_MODE_OFF = 0
HC_MODE_HEATING = 1
HC_MODE_COOLING = 2

HC_MODES = {
    HC_MODE_OFF: "Off",
    HC_MODE_HEATING: "Heating",
    HC_MODE_COOLING: "Cooling"
}

# Modbus register addresses
REGISTER_ADDRESSES = {
    # Temperatures
    "outdoor_temp": 1000,
    "avg_outdoor_temp": 1002,
    "heat_storage_temp": 1008,
    "cold_storage_temp": 1010,
    "dhw_bottom_temp": 1012,
    "dhw_top_temp": 1014,
    "dhw_tap_temp": 1030,
    "flow_temp": 1050,
    "return_temp": 1052,
    "source_input_temp": 1056,
    "source_output_temp": 1058,
    
    # Heating circuits (A to G for each one)
    "hc_a_flow_temp": 1350,
    "hc_b_flow_temp": 1352,
    "hc_c_flow_temp": 1354,
    "hc_d_flow_temp": 1356,
    "hc_e_flow_temp": 1358,
    "hc_f_flow_temp": 1360,
    "hc_g_flow_temp": 1362,
    
    "hc_a_room_temp": 1364,
    "hc_b_room_temp": 1366,
    "hc_c_room_temp": 1368,
    "hc_d_room_temp": 1370,
    "hc_e_room_temp": 1372,
    "hc_f_room_temp": 1374,
    "hc_g_room_temp": 1376,
    
    "hc_a_target_flow_temp": 1378,
    "hc_b_target_flow_temp": 1380,
    "hc_c_target_flow_temp": 1382,
    "hc_d_target_flow_temp": 1384,
    "hc_e_target_flow_temp": 1386,
    "hc_f_target_flow_temp": 1388,
    "hc_g_target_flow_temp": 1390,
    
    # Humidity
    "humidity_sensor": 1392,
    
    # Operational modes
    "error_number": 1004,
    "system_mode": 1005,
    "hp_mode": 1090,
    "hc_a_active_mode": 1498,
    "hc_b_active_mode": 1499,
    "hc_c_active_mode": 1500,
    "hc_d_active_mode": 1501,
    "hc_e_active_mode": 1502,
    "hc_f_active_mode": 1503,
    "hc_g_active_mode": 1504,
    
    # Status
    "error_sum": 1099,
    "compressor_1_status": 1100,
    "compressor_2_status": 1101,
    "compressor_3_status": 1102,
    "compressor_4_status": 1103,
    
    # Setpoints
    "dhw_target_temp": 1032,
    "dhw_load_on_temp": 1033,
    "dhw_load_off_temp": 1034,
    
    "hc_a_mode": 1393,
    "hc_b_mode": 1394,
    "hc_c_mode": 1395,
    "hc_d_mode": 1396,
    "hc_e_mode": 1397,
    "hc_f_mode": 1398,
    "hc_g_mode": 1399,
    
    "hc_a_target_room_temp_normal": 1401,
    "hc_b_target_room_temp_normal": 1403,
    "hc_c_target_room_temp_normal": 1405,
    "hc_d_target_room_temp_normal": 1407,
    "hc_e_target_room_temp_normal": 1409,
    "hc_f_target_room_temp_normal": 1411,
    "hc_g_target_room_temp_normal": 1413,
    
    "hc_a_target_room_temp_eco": 1415,
    "hc_b_target_room_temp_eco": 1417,
    "hc_c_target_room_temp_eco": 1419,
    "hc_d_target_room_temp_eco": 1421,
    "hc_e_target_room_temp_eco": 1423,
    "hc_f_target_room_temp_eco": 1425,
    "hc_g_target_room_temp_eco": 1427,
    
    # Energy
    "power_consumption": 1790,
    "heating_energy": 1750,
    "cooling_energy": 1752,
    "dhw_energy": 1754,
    "defrost_energy": 1756,
    "passive_cooling_energy": 1758,
    
    # Switches
    "heating_request": 1710,
    "cooling_request": 1711,
    "dhw_request": 1712,
    
    # External values that can be set
    "external_room_temp_hc_a": 1650,
    "external_room_temp_hc_b": 1652,
    "external_room_temp_hc_c": 1654,
    "external_room_temp_hc_d": 1656,
    "external_room_temp_hc_e": 1658,
    "external_room_temp_hc_f": 1660,
    "external_room_temp_hc_g": 1662,
    "external_outdoor_temp": 1690,
    "external_humidity": 1692,
    
    # PV integration
    "pv_surplus": 74,
    "pv_production": 78,
    "current_power_consumption": 4122
}

# Entity descriptions
SENSOR_ENTITIES = [
    # Temperatures
    {"key": "outdoor_temp", "name": "Outdoor temperature", "device_class": "temperature", "unit": "°C", "precision": 1},
    {"key": "avg_outdoor_temp", "name": "Average outdoor temperature", "device_class": "temperature", "unit": "°C", "precision": 1},
    {"key": "heat_storage_temp", "name": "Heat storage temperature", "device_class": "temperature", "unit": "°C", "precision": 1},
    {"key": "cold_storage_temp", "name": "Cold storage temperature", "device_class": "temperature", "unit": "°C", "precision": 1},
    {"key": "dhw_bottom_temp", "name": "DHW bottom temperature", "device_class": "temperature", "unit": "°C", "precision": 1},
    {"key": "dhw_top_temp", "name": "DHW top temperature", "device_class": "temperature", "unit": "°C", "precision": 1},
    {"key": "dhw_tap_temp", "name": "DHW tap temperature", "device_class": "temperature", "unit": "°C", "precision": 1},
    {"key": "flow_temp", "name": "Flow temperature", "device_class": "temperature", "unit": "°C", "precision": 1},
    {"key": "return_temp", "name": "Return temperature", "device_class": "temperature", "unit": "°C", "precision": 1},
    {"key": "source_input_temp", "name": "Source input temperature", "device_class": "temperature", "unit": "°C", "precision": 1},
    {"key": "source_output_temp", "name": "Source output temperature", "device_class": "temperature", "unit": "°C", "precision": 1},
    
    # Heating circuits
    {"key": "hc_a_flow_temp", "name": "Heating circuit A flow temperature", "device_class": "temperature", "unit": "°C", "precision": 1},
    {"key": "hc_a_room_temp", "name": "Heating circuit A room temperature", "device_class": "temperature", "unit": "°C", "precision": 1},
    {"key": "hc_a_target_flow_temp", "name": "Heating circuit A target flow temperature", "device_class": "temperature", "unit": "°C", "precision": 1},
    
    # You can add more heating circuits as needed
    
    # Humidity
    {"key": "humidity_sensor", "name": "Humidity", "device_class": "humidity", "unit": "%", "precision": 0},
    
    # Status
    {"key": "error_number", "name": "Error number", "device_class": None, "unit": None, "precision": 0},
    {"key": "hp_mode", "name": "Heat pump mode", "device_class": None, "unit": None, "precision": 0, "value_map": HP_MODES},
    {"key": "hc_a_active_mode", "name": "Heating circuit A active mode", "device_class": None, "unit": None, "precision": 0, "value_map": HC_MODES},
    
    # Energy & Power
    {"key": "power_consumption", "name": "Current power", "device_class": "power", "unit": "kW", "precision": 2, "state_class": "measurement"},
    {"key": "heating_energy", "name": "Heating energy", "device_class": "energy", "unit": "kWh", "precision": 0, "state_class": "total_increasing"},
    {"key": "cooling_energy", "name": "Cooling energy", "device_class": "energy", "unit": "kWh", "precision": 0, "state_class": "total_increasing"},
    {"key": "dhw_energy", "name": "DHW energy", "device_class": "energy", "unit": "kWh", "precision": 0, "state_class": "total_increasing"},
    
    # PV integration
    {"key": "pv_surplus", "name": "PV surplus", "device_class": "power", "unit": "kW", "precision": 2, "state_class": "measurement"},
    {"key": "pv_production", "name": "PV production", "device_class": "power", "unit": "kW", "precision": 2, "state_class": "measurement"},
    {"key": "current_power_consumption", "name": "Heat pump power consumption", "device_class": "power", "unit": "kW", "precision": 2, "state_class": "measurement"}
]

SWITCH_ENTITIES = [
    {"key": "heating_request", "name": "Heating request", "icon": "mdi:radiator"},
    {"key": "cooling_request", "name": "Cooling request", "icon": "mdi:snowflake"},
    {"key": "dhw_request", "name": "DHW request", "icon": "mdi:water-boiler"}
]

# System operation mode options for select entity
SYSTEM_MODE_OPTIONS = [
    {"value": str(SYSTEM_MODE_STANDBY), "label": SYSTEM_MODES[SYSTEM_MODE_STANDBY]},
    {"value": str(SYSTEM_MODE_AUTO), "label": SYSTEM_MODES[SYSTEM_MODE_AUTO]},
    {"value": str(SYSTEM_MODE_AWAY), "label": SYSTEM_MODES[SYSTEM_MODE_AWAY]},
    {"value": str(SYSTEM_MODE_DHW_ONLY), "label": SYSTEM_MODES[SYSTEM_MODE_DHW_ONLY]},
    {"value": str(SYSTEM_MODE_HEATING_COOLING_ONLY), "label": SYSTEM_MODES[SYSTEM_MODE_HEATING_COOLING_ONLY]}
]

# Heating circuit mode options for select entity
HC_MODE_OPTIONS = [
    {"value": "0", "label": "Off"},
    {"value": "1", "label": "Time program"},
    {"value": "2", "label": "Normal"},
    {"value": "3", "label": "Eco"},
    {"value": "4", "label": "Manual heating"},
    {"value": "5", "label": "Manual cooling"}
]

SELECT_ENTITIES = [
    {"key": "system_mode", "name": "System operation mode", "options": SYSTEM_MODE_OPTIONS, "icon": "mdi:thermostat"},
    {"key": "hc_a_mode", "name": "Heating circuit A mode", "options": HC_MODE_OPTIONS, "icon": "mdi:radiator"}
]

NUMBER_ENTITIES = [
    {"key": "dhw_target_temp", "name": "DHW target temperature", "min": 35, "max": 95, "step": 1, "unit": "°C", "icon": "mdi:water-thermometer"},
    {"key": "hc_a_target_room_temp_normal", "name": "HC A normal temperature", "min": 15, "max": 30, "step": 0.5, "unit": "°C", "icon": "mdi:thermostat"},
    {"key": "hc_a_target_room_temp_eco", "name": "HC A eco temperature", "min": 10, "max": 25, "step": 0.5, "unit": "°C", "icon": "mdi:thermostat-eco"}
]