# Datei: const.py
"""
iDM Wärmepumpe (Modbus TCP)
Version: v1.6 (Dokumentations-Update)
Stand: 2025-09-24
"""

DOMAIN = "idm_heatpump"

DEFAULT_PORT = 502
CONF_UPDATE_INTERVAL = "update_interval"
DEFAULT_UPDATE_INTERVAL = 30

CONF_UNIT_ID = "unit_id"
DEFAULT_UNIT_ID = 1

# -------------------------------------------------------------------
# Register-Adressen (Navigator 10)
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

# Wärmepumpe direkt
REG_WP_VL_TEMP = 1050       # (B33) Wärmepumpenvorlauftemperatur [°C]
REG_RETURN_TEMP = 1052      # (B34) Rücklauftemperatur [°C]
REG_LOAD_TEMP = 1066        # (B45) Ladefühler [°C]
REG_FLOW_SENSOR = 1072      # (B2) Durchfluss Heizung [l/min]

# Zusätzliche WP-Sensoren

# Heizkreise
REG_HKA_VL = 1350           # (B49) Heizkreis A Vorlauftemperatur [°C]
REG_HKA_VL_SOLL = 1378      # (B49s) Heizkreis A Soll-Vorlauftemperatur [°C]
REG_HKC_VL = 1354           # (B59) Heizkreis C Vorlauftemperatur [°C]
REG_HKC_VL_SOLL = 1382      # (B59s) Heizkreis C Soll-Vorlauftemperatur [°C]
REG_HKA_MODE = 1393         # (HKAMODE) Betriebsart Heizkreis A (UCHAR RW)
REG_HKC_MODE = 1395         # (HKCMODE) Betriebsart Heizkreis C (UCHAR RW)
REG_HKA_ACTIVE_MODE = 1498  # (B55) Aktive Betriebsart Heizkreis A (UCHAR RO)
REG_HKC_ACTIVE_MODE = 1500  # (B65) Aktive Betriebsart Heizkreis C (UCHAR RO)

# Warmwasser Sollwerte (UCHAR RW)
REG_WW_TARGET = 1032        # (FW030) Warmwasser-Solltemperatur [°C]
REG_WW_START  = 1033        # (FW027) WW-Ladung Einschalttemperatur [°C]
REG_WW_STOP   = 1034        # (FW028) WW-Ladung Ausschalttemperatur [°C]

# Warmwasser Anforderung
REG_WW_REQUEST = 1712       # (WWREQ) Anforderung Warmwasserladung (BOOL RW)
REG_WW_ONETIME = 1713       # (WWONCE) Einmalige Warmwasserladung (BOOL RW)

# Heizen
REG_HEAT_REQUEST = 1710     # (HEATREQ) Anforderung Heizen (BOOL RW)

# Energiemengen (FLOAT RO) [kWh]
REG_EN_HEATING        = 1748  # Wärmemenge Heizen
REG_EN_TOTAL          = 1750  # Wärmemenge Gesamt
REG_EN_COOLING        = 1752  # Wärmemenge Kühlen
REG_EN_DHW            = 1754  # Wärmemenge Warmwasser
REG_EN_DEFROST        = 1756  # Wärmemenge Abtauung
REG_EN_PASSIVE_COOL   = 1758  # Wärmemenge Passive Kühlung
REG_EN_SOLAR          = 1760  # Wärmemenge Solar
REG_EN_EHEATER        = 1762  # Wärmemenge Elektroheizeinsatz

# Leistungen (FLOAT RO)
REG_THERMAL_POWER     = 1790  # Thermische Momentanleistung [kW]
REG_SOLAR_POWER       = 1792  # Momentanleistung Solar [kW]

# Solar (Temperaturen und Modus)
REG_SOLAR_COLLECTOR_TEMP = 1850  # (B73) Solar Kollektortemperatur [°C]
REG_SOLAR_RETURN_TEMP    = 1852  # (B75) Solar Kollektorrücklauftemperatur [°C]
REG_SOLAR_CHARGE_TEMP    = 1854  # (B74) Solar Ladetemperatur [°C]
REG_SOLAR_MODE           = 1856  # (SC002) Betriebsart Solar (UCHAR RW)

# Leistung WP (elektrisch)
REG_WP_POWER = 4122         # (B90) Elektrische Gesamtleistung Wärmepumpe [kW]

# PV / Batterie (hersteller-spezifisch)
REG_PV_SURPLUS = 74         # (PV74) Aktueller PV-Überschuss [kW]
REG_EHEIZSTAB = 76          # (PV76) Leistung E-Heizstab [kW]
REG_PV_PRODUKTION = 78      # (PV78) Aktuelle PV-Produktion [kW]
REG_HAUSVERBRAUCH = 82      # (PV82) Hausverbrauch [kW]
REG_BATTERIE_ENTLADUNG = 84 # (PV84) Batterieentladung [kW]
REG_BATTERIE_FUELLSTAND = 86# (PV86) Batteriefüllstand [%]