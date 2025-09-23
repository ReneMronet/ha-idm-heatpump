"""
const.py – v2.13 (2025-09-23)

Konstanten für iDM Wärmepumpen Integration
"""

DOMAIN = "idm_heatpump"

DEFAULT_PORT = 502
CONF_UPDATE_INTERVAL = "update_interval"
DEFAULT_UPDATE_INTERVAL = 30

CONF_UNIT_ID = "unit_id"
DEFAULT_UNIT_ID = 1

# -------------------------------------------------------------------
# Register-Adressen (mit Navigator 10 B-Codes)
# -------------------------------------------------------------------

# System
REG_SYSTEM_MODE = 1005      # (SYSMODE) Betriebsart System (UCHAR RW)
REG_WP_STATUS = 1091        # (B19) Heizanforderung Wärmepumpe (UCHAR RO) 0=Bereit,1=Heizbetrieb

# Temperaturen
REG_OUTDOOR_TEMP = 1000     # (B32) Außentemperatur [°C]
REG_OUTDOOR_TEMP_AVG = 1002 # (B32a) Gemittelte Außentemperatur [°C]
REG_HEATBUFFER_TEMP = 1008  # (B41) Wärmespeichertemperatur [°C]
REG_WW_BOTTOM_TEMP = 1012   # (B44) Warmwasser unten [°C]
REG_WW_TOP_TEMP = 1014      # (B43) Warmwasser oben [°C]
REG_WW_TAP_TEMP = 1030      # (B46) Warmwasser-Zapftemperatur [°C]
REG_AIR_INLET_TEMP = 1060   # (B37) Luftansaugtemperatur [°C]
REG_SOLAR_COLLECTOR_TEMP = 1850  # (B61) Solarkollektortemperatur [°C]

# Wärmepumpe direkt
REG_WP_VL_TEMP = 1050       # (B33) Wärmepumpenvorlauftemperatur [°C]
REG_RETURN_TEMP = 1052      # (B34) Rücklauftemperatur [°C]
REG_LOAD_TEMP = 1066        # (B45) Ladefühler [°C]
REG_FLOW_SENSOR = 1072      # (B2) Durchfluss Heizung [l/min]

# >>> Neue Sensoren <<<
REG_EVAP_OUT_TEMP = 1058    # (B79) Verdampferaustritt 1 [°C]
REG_FLUID_LINE_TEMP = 1054  # (B87) Flüssigkeitsleitungstemperatur [°C]
REG_HOT_GAS_TEMP = 1062     # (B71) Heißgastemperatur 1 [°C]

# Heizkreise
REG_HKA_VL = 1350           # (B49) Heizkreis A Vorlauftemperatur [°C]
REG_HKA_VL_SOLL = 1378      # (B49s) Heizkreis A Soll-Vorlauftemperatur [°C]
REG_HKC_VL = 1354           # (B59) Heizkreis C Vorlauftemperatur [°C]
REG_HKC_VL_SOLL = 1382      # (B59s) Heizkreis C Soll-Vorlauftemperatur [°C]
REG_HKA_MODE = 1393         # (HKAMODE) Betriebsart Heizkreis A (UCHAR RW)
REG_HKC_MODE = 1395         # (HKCMODE) Betriebsart Heizkreis C (UCHAR RW)
REG_HKA_ACTIVE_MODE = 1498  # (B55) Aktive Betriebsart Heizkreis A (UCHAR RO)
REG_HKC_ACTIVE_MODE = 1500  # (B65) Aktive Betriebsart Heizkreis C (UCHAR RO)

# Warmwasser
REG_WW_REQUEST = 1712       # (WWREQ) Anforderung Warmwasserladung (BOOL RW)
REG_WW_ONETIME = 1713       # (WWONCE) Einmalige Warmwasserladung (BOOL RW)

# Heizen
REG_HEAT_REQUEST = 1710     # (HEATREQ) Anforderung Heizen (BOOL RW)

# Leistung Wärmepumpe
REG_WP_POWER = 4122         # (B90) Elektrische Gesamtleistung Wärmepumpe [kW]

# PV / Batterie
REG_PV_SURPLUS = 74         # (PV74) Aktueller PV-Überschuss [kW]
REG_EHEIZSTAB = 76          # (PV76) Leistung E-Heizstab [kW]
REG_PV_PRODUKTION = 78      # (PV78) Aktuelle PV-Produktion [kW]
REG_HAUSVERBRAUCH = 82      # (PV82) Hausverbrauch [kW]
REG_BATTERIE_ENTLADUNG = 84 # (PV84) Batterieentladung [kW]
REG_BATTERIE_FUELLSTAND = 86# (PV86) Batteriefüllstand [%]
