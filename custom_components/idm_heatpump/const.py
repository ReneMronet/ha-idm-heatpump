"""
iDM Wärmepumpe (Modbus TCP)
Version: v5.0
Stand: 2026-02-26

Änderungen v5.0 (Schritt 2 – Neue Features):
- Sensor-Gruppen (solar, pv_battery, cooling, diagnostic, room_control, extended_temps)
- ~48 neue Register (hohe + mittlere Priorität + Kühlung pro HK)
- Kühl-Register in HC_REGISTERS: cool_normal, cool_eco, cool_limit, cool_vl
- Raumtemperatur pro HK in HC_REGISTERS: room_temp
- build_register_map() berücksichtigt sensor_groups
- Auto-Detect: INVALID_FLOAT, INVALID_UCHAR Konstanten
- Alle bisherigen Konstanten bleiben erhalten (Abwärtskompatibilität)
"""

DOMAIN = "idm_heatpump"

DEFAULT_PORT = 502
CONF_UPDATE_INTERVAL = "update_interval"
DEFAULT_UPDATE_INTERVAL = 30

CONF_UNIT_ID = "unit_id"
DEFAULT_UNIT_ID = 1

CONF_HEATING_CIRCUITS = "heating_circuits"
DEFAULT_HEATING_CIRCUITS = ["A", "C"]
ALL_HEATING_CIRCUITS = ["A", "B", "C", "D", "E", "F", "G"]

# -------------------------------------------------------------------
# Sensor-Gruppen Konfiguration
# -------------------------------------------------------------------
CONF_SENSOR_GROUPS = "sensor_groups"
DEFAULT_SENSOR_GROUPS = ["solar", "pv_battery"]

ALL_SENSOR_GROUPS = [
    "solar",
    "pv_battery",
    "cooling",
    "diagnostic",
    "room_control",
    "extended_temps",
]

# -------------------------------------------------------------------
# Register-Datentypen
# -------------------------------------------------------------------
REG_TYPE_FLOAT = "float"   # 32-bit IEEE754, 2 Register
REG_TYPE_UCHAR = "uchar"   # 8-bit unsigned (Low-Byte eines WORD)
REG_TYPE_WORD = "word"      # 16-bit unsigned

# -------------------------------------------------------------------
# Auto-Detect: Ungültige Werte für nicht verbaute Sensoren
# -------------------------------------------------------------------
INVALID_FLOAT = -1.0
INVALID_UCHAR = 255
AUTO_DETECT_THRESHOLD = 3

# -------------------------------------------------------------------
# Heizkreis-Register-Mapping (Navigator 10)
# Index: A=0, B=1, C=2, D=3, E=4, F=5, G=6
# -------------------------------------------------------------------
HC_INDEX = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5, "G": 6}

HC_REGISTERS = {
    # --- Heizen (bestehend) ---
    "vl":          lambda i: 1350 + i * 2,
    "vl_soll":     lambda i: 1378 + i * 2,
    "active_mode": lambda i: 1498 + i,
    "mode":        lambda i: 1393 + i,
    "temp_normal": lambda i: 1401 + i * 2,
    "temp_eco":    lambda i: 1415 + i * 2,
    "curve":       lambda i: 1429 + i * 2,
    "heat_limit":  lambda i: 1442 + i,
    "parallel":    lambda i: 1505 + i,
    # --- Kühlung (NEU) ---
    "cool_normal": lambda i: 1457 + i * 2,
    "cool_eco":    lambda i: 1471 + i * 2,
    "cool_limit":  lambda i: 1484 + i,
    "cool_vl":     lambda i: 1491 + i,
    # --- Einzelraumregelung (NEU) ---
    "room_temp":   lambda i: 1364 + i * 2,
}

HC_REGISTER_TYPES = {
    "vl":          REG_TYPE_FLOAT,
    "vl_soll":     REG_TYPE_FLOAT,
    "active_mode": REG_TYPE_UCHAR,
    "mode":        REG_TYPE_UCHAR,
    "temp_normal": REG_TYPE_FLOAT,
    "temp_eco":    REG_TYPE_FLOAT,
    "curve":       REG_TYPE_FLOAT,
    "heat_limit":  REG_TYPE_UCHAR,
    "parallel":    REG_TYPE_UCHAR,
    "cool_normal": REG_TYPE_FLOAT,
    "cool_eco":    REG_TYPE_FLOAT,
    "cool_limit":  REG_TYPE_UCHAR,
    "cool_vl":     REG_TYPE_UCHAR,
    "room_temp":   REG_TYPE_FLOAT,
}

# Welche HC-Register gehören zu welcher Sensor-Gruppe?
HC_REGISTER_GROUPS = {
    "cool_normal": "cooling",
    "cool_eco":    "cooling",
    "cool_limit":  "cooling",
    "cool_vl":     "cooling",
    "room_temp":   "room_control",
}


def hc_reg(circuit: str, register_name: str) -> int:
    """Berechnet die Register-Adresse für einen Heizkreis."""
    return HC_REGISTERS[register_name](HC_INDEX[circuit])


# -------------------------------------------------------------------
# Register-Adressen – Einzelkonstanten
# -------------------------------------------------------------------

# System (Basis)
REG_INTERNAL_MESSAGE = 1004
REG_SYSTEM_MODE = 1005
REG_WP_MODE = 1090
REG_WP_STATUS = 1091

# Temperaturen (Basis)
REG_OUTDOOR_TEMP = 1000
REG_OUTDOOR_TEMP_AVG = 1002
REG_HEATBUFFER_TEMP = 1008
REG_WW_BOTTOM_TEMP = 1012
REG_WW_TOP_TEMP = 1014
REG_WW_TAP_TEMP = 1030
REG_AIR_INLET_TEMP = 1060
REG_AIR_INLET_TEMP_2 = 1064

# Wärmepumpe (Basis)
REG_WP_VL_TEMP = 1050
REG_RETURN_TEMP = 1052
REG_LOAD_TEMP = 1066
REG_FLOW_SENSOR = 1073

# Warmwasser Sollwerte (Basis)
REG_WW_TARGET = 1032
REG_WW_START  = 1033
REG_WW_STOP   = 1034

# Warmwasser / Heizen Anforderung (Basis)
REG_WW_REQUEST = 1712
REG_WW_ONETIME = 1713
REG_HEAT_REQUEST = 1710

# Energiemengen (Basis) [kWh]
REG_EN_HEATING      = 1748
REG_EN_TOTAL        = 1750
REG_EN_COOLING      = 1752
REG_EN_DHW          = 1754
REG_EN_DEFROST      = 1756
REG_EN_PASSIVE_COOL = 1758
REG_EN_SOLAR        = 1760
REG_EN_EHEATER      = 1762

# Leistungen (Basis)
REG_THERMAL_POWER = 1790
REG_WP_POWER = 4122

# Solar-Gruppe
REG_SOLAR_COLLECTOR_TEMP = 1850
REG_SOLAR_RETURN_TEMP    = 1852
REG_SOLAR_CHARGE_TEMP    = 1854
REG_SOLAR_MODE           = 1856
REG_SOLAR_POWER          = 1792

# PV / Batterie-Gruppe
REG_PV_SURPLUS           = 74
REG_EHEIZSTAB            = 76
REG_PV_PRODUKTION        = 78
REG_HAUSVERBRAUCH        = 82
REG_BATTERIE_ENTLADUNG   = 84
REG_BATTERIE_FUELLSTAND  = 86
REG_SMARTGRID_STATUS     = 90
REG_PV_TARGET            = 88
REG_CURRENT_ELEC_PRICE   = 1048

# Kühlungs-Gruppe
REG_COOLING_REQUEST_WP   = 1092
REG_WW_REQUEST_WP        = 1093
REG_COOL_REQUEST         = 1711

# Diagnose-Gruppe
REG_FAULT_SUMMARY        = 1099
REG_EVU_LOCK             = 1098
REG_COMPRESSOR_1         = 1100
REG_CHARGE_PUMP          = 1104
REG_VARIABLE_INPUT       = 1006
REG_SWITCH_VALVE_HC      = 1110
REG_CIRC_PUMP            = 1118
REG_POWER_LIMIT          = 4108

# Einzelraumregelung-Gruppe
REG_HUMIDITY_SENSOR      = 1392

# Erweiterte Temperaturen-Gruppe
REG_HEAT_EXCHANGER_TEMP  = 1062
REG_HEATSINK_RETURN      = 1068
REG_HEATSINK_SUPPLY      = 1070
REG_COLD_STORAGE_TEMP    = 1010


# -------------------------------------------------------------------
# Register-Maps pro Gruppe
# -------------------------------------------------------------------

BASE_REGISTERS = {
    REG_OUTDOOR_TEMP:        REG_TYPE_FLOAT,
    REG_OUTDOOR_TEMP_AVG:    REG_TYPE_FLOAT,
    REG_WP_VL_TEMP:          REG_TYPE_FLOAT,
    REG_RETURN_TEMP:         REG_TYPE_FLOAT,
    REG_LOAD_TEMP:           REG_TYPE_FLOAT,
    REG_HEATBUFFER_TEMP:     REG_TYPE_FLOAT,
    REG_WW_TOP_TEMP:         REG_TYPE_FLOAT,
    REG_WW_BOTTOM_TEMP:      REG_TYPE_FLOAT,
    REG_WW_TAP_TEMP:         REG_TYPE_FLOAT,
    REG_AIR_INLET_TEMP:      REG_TYPE_FLOAT,
    REG_AIR_INLET_TEMP_2:    REG_TYPE_FLOAT,
    REG_EN_HEATING:          REG_TYPE_FLOAT,
    REG_EN_TOTAL:            REG_TYPE_FLOAT,
    REG_EN_COOLING:          REG_TYPE_FLOAT,
    REG_EN_DHW:              REG_TYPE_FLOAT,
    REG_EN_DEFROST:          REG_TYPE_FLOAT,
    REG_EN_PASSIVE_COOL:     REG_TYPE_FLOAT,
    REG_EN_SOLAR:            REG_TYPE_FLOAT,
    REG_EN_EHEATER:          REG_TYPE_FLOAT,
    REG_THERMAL_POWER:       REG_TYPE_FLOAT,
    REG_WP_POWER:            REG_TYPE_FLOAT,
    REG_INTERNAL_MESSAGE:    REG_TYPE_UCHAR,
    REG_WP_MODE:             REG_TYPE_UCHAR,
    REG_WP_STATUS:           REG_TYPE_UCHAR,
    REG_SYSTEM_MODE:         REG_TYPE_UCHAR,
    REG_FLOW_SENSOR:         REG_TYPE_UCHAR,
    REG_WW_TARGET:           REG_TYPE_UCHAR,
    REG_WW_START:            REG_TYPE_UCHAR,
    REG_WW_STOP:             REG_TYPE_UCHAR,
    REG_HEAT_REQUEST:        REG_TYPE_UCHAR,
    REG_WW_REQUEST:          REG_TYPE_UCHAR,
    REG_WW_ONETIME:          REG_TYPE_UCHAR,
}

GROUP_REGISTERS = {
    "solar": {
        REG_SOLAR_COLLECTOR_TEMP: REG_TYPE_FLOAT,
        REG_SOLAR_RETURN_TEMP:    REG_TYPE_FLOAT,
        REG_SOLAR_CHARGE_TEMP:    REG_TYPE_FLOAT,
        REG_SOLAR_POWER:          REG_TYPE_FLOAT,
        REG_SOLAR_MODE:           REG_TYPE_UCHAR,
    },
    "pv_battery": {
        REG_PV_SURPLUS:          REG_TYPE_FLOAT,
        REG_EHEIZSTAB:           REG_TYPE_FLOAT,
        REG_PV_PRODUKTION:       REG_TYPE_FLOAT,
        REG_HAUSVERBRAUCH:       REG_TYPE_FLOAT,
        REG_BATTERIE_ENTLADUNG:  REG_TYPE_FLOAT,
        REG_BATTERIE_FUELLSTAND: REG_TYPE_WORD,
        REG_SMARTGRID_STATUS:    REG_TYPE_UCHAR,
        REG_PV_TARGET:           REG_TYPE_FLOAT,
        REG_CURRENT_ELEC_PRICE:  REG_TYPE_FLOAT,
    },
    "cooling": {
        REG_COOLING_REQUEST_WP:  REG_TYPE_UCHAR,
        REG_WW_REQUEST_WP:       REG_TYPE_UCHAR,
        REG_COOL_REQUEST:        REG_TYPE_UCHAR,
    },
    "diagnostic": {
        REG_FAULT_SUMMARY:       REG_TYPE_UCHAR,
        REG_EVU_LOCK:            REG_TYPE_UCHAR,
        REG_COMPRESSOR_1:        REG_TYPE_UCHAR,
        REG_CHARGE_PUMP:         REG_TYPE_WORD,
        REG_VARIABLE_INPUT:      REG_TYPE_UCHAR,
        REG_SWITCH_VALVE_HC:     REG_TYPE_WORD,
        REG_CIRC_PUMP:           REG_TYPE_WORD,
        REG_POWER_LIMIT:         REG_TYPE_FLOAT,
    },
    "room_control": {
        REG_HUMIDITY_SENSOR:     REG_TYPE_FLOAT,
    },
    "extended_temps": {
        REG_HEAT_EXCHANGER_TEMP: REG_TYPE_FLOAT,
        REG_HEATSINK_RETURN:     REG_TYPE_FLOAT,
        REG_HEATSINK_SUPPLY:     REG_TYPE_FLOAT,
        REG_COLD_STORAGE_TEMP:   REG_TYPE_FLOAT,
    },
}

# Abwärtskompatibilität
STATIC_REGISTERS = dict(BASE_REGISTERS)
for _grp_regs in GROUP_REGISTERS.values():
    STATIC_REGISTERS.update(_grp_regs)


def build_register_map(
    heating_circuits: list[str],
    sensor_groups: list[str] | None = None,
) -> dict[int, str]:
    """Baut vollständige Register-Map inkl. dynamischer Heizkreis-Register.

    Args:
        heating_circuits: Aktive Heizkreise (z.B. ["A", "C"])
        sensor_groups: Aktive Sensor-Gruppen. None = alle aktiv.

    Returns: {register_address: register_type}
    """
    if sensor_groups is None:
        sensor_groups = ALL_SENSOR_GROUPS

    registers = dict(BASE_REGISTERS)

    for group in sensor_groups:
        if group in GROUP_REGISTERS:
            registers.update(GROUP_REGISTERS[group])

    for hc in heating_circuits:
        idx = HC_INDEX[hc]
        for name, reg_type in HC_REGISTER_TYPES.items():
            group = HC_REGISTER_GROUPS.get(name)
            if group is not None and group not in sensor_groups:
                continue
            addr = HC_REGISTERS[name](idx)
            registers[addr] = reg_type

    return registers


def get_device_info(host: str) -> dict:
    """Zentrales device_info dict für alle Entities."""
    return {
        "identifiers": {("idm_heatpump", "idm_system")},
        "name": "iDM Wärmepumpe",
        "manufacturer": "iDM Energiesysteme",
        "model": "AERO ALM 4\u201312",
        "configuration_url": f"http://{host}",
    }
