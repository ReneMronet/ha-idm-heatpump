"""
const.py – v2.10 (2025-09-18)

Konstanten für iDM Wärmepumpen Integration
"""

DOMAIN = "idm_heatpump"

DEFAULT_PORT = 502
CONF_UPDATE_INTERVAL = "update_interval"
DEFAULT_UPDATE_INTERVAL = 30

# -------------------------------------------------------------------
# Register-Adressen
# -------------------------------------------------------------------

# System
REG_SYSTEM_MODE = 1005      # Betriebsart System (UCHAR RW) 0=Standby,1=Automatik,2=Abwesend,4=Nur WW,5=Nur Heizen/Kühlen
REG_WP_STATUS = 1091        # Heizanforderung Wärmepumpe (UCHAR RO) 0=Bereit,1=Heizbetrieb

# Temperaturen
REG_OUTDOOR_TEMP = 1000     # Außentemperatur (FLOAT RO) [°C]
REG_OUTDOOR_TEMP_AVG = 1002 # Gemittelte Außentemperatur (FLOAT RO) [°C]
REG_HEATBUFFER_TEMP = 1008  # Wärmespeichertemperatur (FLOAT RO) [°C]
REG_WW_BOTTOM_TEMP = 1012   # Warmwasser unten (FLOAT RO) [°C]
REG_WW_TOP_TEMP = 1014      # Warmwasser oben (FLOAT RO) [°C]
REG_WW_TAP_TEMP = 1030      # Warmwasser-Zapftemperatur (FLOAT RO) [°C]
REG_AIR_INLET_TEMP = 1060   # Luftansaugtemperatur (FLOAT RO) [°C]
REG_SOLAR_COLLECTOR_TEMP = 1850  # Solarkollektortemperatur (FLOAT RO) [°C]

# Heizkreise (Vorlauf & Soll-Vorlauf)
REG_HKA_VL = 1350           # Heizkreis A Vorlauftemperatur (FLOAT RO) [°C]
REG_HKA_VL_SOLL = 1378      # Heizkreis A Soll-Vorlauftemperatur (FLOAT RO) [°C]
REG_HKC_VL = 1354           # Heizkreis C Vorlauftemperatur (FLOAT RO) [°C]
REG_HKC_VL_SOLL = 1382      # Heizkreis C Soll-Vorlauftemperatur (FLOAT RO) [°C]

# Heizkreise (eingestellte Betriebsarten)
REG_HKA_MODE = 1393         # Betriebsart Heizkreis A (UCHAR RW)
REG_HKC_MODE = 1395         # Betriebsart Heizkreis C (UCHAR RW)

# Heizkreise (aktive Betriebsarten)
REG_HKA_ACTIVE_MODE = 1498  # Aktive Betriebsart Heizkreis A (UCHAR RO)
REG_HKC_ACTIVE_MODE = 1500  # Aktive Betriebsart Heizkreis C (UCHAR RO)

# Warmwasser
REG_WW_REQUEST = 1712       # Anforderung Warmwasserladung (BOOL RW) 0=Aus,1=Ein
REG_WW_ONETIME = 1713       # Einmalige Warmwasserladung (BOOL RW) 0=Aus,1=Ein

# Heizen
REG_HEAT_REQUEST = 1710     # Anforderung Heizen (BOOL RW) 0=Aus,1=Ein

# Leistung Wärmepumpe
REG_WP_POWER = 4122         # Elektrische Gesamtleistung Wärmepumpe (FLOAT RO) [kW]

# PV / Batterie
REG_PV_SURPLUS = 74         # Aktueller PV-Überschuss (FLOAT RW/RO) [kW]
REG_EHEIZSTAB = 76          # Leistung E-Heizstab (FLOAT RW/RO) [kW]
REG_PV_PRODUKTION = 78      # Aktuelle PV-Produktion (FLOAT RW/RO) [kW]
REG_HAUSVERBRAUCH = 82      # Hausverbrauch (FLOAT RW/RO) [kW]
REG_BATTERIE_ENTLADUNG = 84 # Batterieentladung (FLOAT RW/RO) [kW]
REG_BATTERIE_FUELLSTAND = 86# Batteriefüllstand (WORD RW/RO) [%]
