"""
iDM Wärmepumpe (Modbus TCP)
Version: v3.0
Stand: 2026-02-26

Änderungen v3.0:
- Heizkreise A–G dynamisch konfigurierbar
- Zentrales Register-Mapping HC_REGISTERS / HC_INDEX
- Alle Einzel-Konstanten bleiben für Abwärtskompatibilität erhalten
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
# Zentrales Heizkreis-Register-Mapping (Navigator 10)
# Index: A=0, B=1, C=2, D=3, E=4, F=5, G=6
# -------------------------------------------------------------------
HC_INDEX = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5, "G": 6}

HC_REGISTERS = {
    # Sensoren (RO)
    "vl":          lambda i: 1350 + i * 2,   # Vorlauftemperatur (FLOAT RO)
    "vl_soll":     lambda i: 1378 + i * 2,   # Soll-Vorlauftemperatur (FLOAT RO)
    "active_mode": lambda i: 1498 + i,        # Aktive Betriebsart (UCHAR RO)
    # Selects (RW)
    "mode":        lambda i: 1393 + i,        # Betriebsart (UCHAR RW)
    # Numbers (RW)
    "temp_normal": lambda i: 1401 + i * 2,    # Raumsolltemp Normal (FLOAT RW)
    "temp_eco":    lambda i: 1415 + i * 2,    # Raumsolltemp Eco (FLOAT RW)
    "curve":       lambda i: 1429 + i * 2,    # Heizkurve (FLOAT RW)
    "heat_limit":  lambda i: 1442 + i,        # Heizgrenze (UCHAR RW)
    "parallel":    lambda i: 1505 + i,        # Parallelverschiebung (UCHAR RW)
}


def hc_reg(circuit: str, register_name: str) -> int:
    """Berechnet die Register-Adresse für einen Heizkreis."""
    return HC_REGISTERS[register_name](HC_INDEX[circuit])


# -------------------------------------------------------------------
# Register-Adressen (Navigator 10) – Einzelkonstanten
# -------------------------------------------------------------------

# System
REG_INTERNAL_MESSAGE = 1004
REG_SYSTEM_MODE = 1005
REG_WP_MODE = 1090
REG_WP_STATUS = 1091

# Temperaturen
REG_OUTDOOR_TEMP = 1000
REG_OUTDOOR_TEMP_AVG = 1002
REG_HEATBUFFER_TEMP = 1008
REG_WW_BOTTOM_TEMP = 1012
REG_WW_TOP_TEMP = 1014
REG_WW_TAP_TEMP = 1030
REG_AIR_INLET_TEMP = 1060
REG_AIR_INLET_TEMP_2 = 1064

# Wärmepumpe direkt
REG_WP_VL_TEMP = 1050
REG_RETURN_TEMP = 1052
REG_LOAD_TEMP = 1066
REG_FLOW_SENSOR = 1073

# Warmwasser Sollwerte (UCHAR RW)
REG_WW_TARGET = 1032
REG_WW_START  = 1033
REG_WW_STOP   = 1034

# Warmwasser / Heizen Anforderung
REG_WW_REQUEST = 1712
REG_WW_ONETIME = 1713
REG_HEAT_REQUEST = 1710

# Energiemengen (FLOAT RO) [kWh]
REG_EN_HEATING      = 1748
REG_EN_TOTAL        = 1750
REG_EN_COOLING      = 1752
REG_EN_DHW          = 1754
REG_EN_DEFROST      = 1756
REG_EN_PASSIVE_COOL = 1758
REG_EN_SOLAR        = 1760
REG_EN_EHEATER      = 1762

# Leistungen (FLOAT RO)
REG_THERMAL_POWER = 1790
REG_SOLAR_POWER   = 1792

# Solar
REG_SOLAR_COLLECTOR_TEMP = 1850
REG_SOLAR_RETURN_TEMP    = 1852
REG_SOLAR_CHARGE_TEMP    = 1854
REG_SOLAR_MODE           = 1856

# Leistung WP (elektrisch)
REG_WP_POWER = 4122

# PV / Batterie
REG_PV_SURPLUS = 74
REG_EHEIZSTAB = 76
REG_PV_PRODUKTION = 78
REG_HAUSVERBRAUCH = 82
REG_BATTERIE_ENTLADUNG = 84
REG_BATTERIE_FUELLSTAND = 86
