"""
iDM Wärmepumpe (Modbus TCP)
Version: v2.2
Stand: 2025-11-12

Änderungen v2.2:
- REG_WP_MODE (1090) Betriebsart Wärmepumpe (UCHAR RO) ergänzt

Änderung v2.1:
- REG_INTERNAL_MESSAGE (1004) Interne Meldung (UCHAR RO, 020–999) ergänzt

Änderung v2.0:
- REG_HKA_CURVE (1429) und REG_HKC_CURVE (1433) für Heizkurve HK A/C ergänzt

Änderung v1.9:
- REG_HKA_HEATLIMIT (1442) und REG_HKC_HEATLIMIT (1444) für Heizgrenze HK A/C ergänzt

Änderung v1.8:
- REG_HKA_PARALLEL (1505) und REG_HKC_PARALLEL (1507) für Parallelverschiebung HK A/C ergänzt
- Kommentare bereinigt
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
REG_INTERNAL_MESSAGE = 1004  # (Bxx) Interne Meldung (UCHAR RO), aktuelle Meldungsnummer 020–999 lt. NAVIGATOR
REG_SYSTEM_MODE = 1005       # (SYSMODE) Betriebsart System (UCHAR RW)
REG_WP_MODE = 1090           # (UCHAR RO) Betriebsart Wärmepumpe: 0=Bereit,1=Heizen,2=Kühlen,3=Abtauung,4=Warmwasser
REG_WP_STATUS = 1091         # (B19) Heizanforderung Wärmepumpe (UCHAR RO) 0=Bereit,1=Heizbetrieb

# Temperaturen
REG_OUTDOOR_TEMP = 1000      # (B32) Außentemperatur [°C]
REG_OUTDOOR_TEMP_AVG = 1002  # (B32a) Gemittelte Außentemperatur [°C]
REG_HEATBUFFER_TEMP = 1008   # (B41) Wärmespeichertemperatur [°C]
REG_WW_BOTTOM_TEMP = 1012    # (B44) Warmwasser unten [°C]
REG_WW_TOP_TEMP = 1014       # (B43) Warmwasser oben [°C]
REG_WW_TAP_TEMP = 1030       # (B46) Warmwasser-Zapftemperatur [°C] (kann je nach Anlage leer sein)
REG_AIR_INLET_TEMP = 1060    # (B37) Luftansaugtemperatur [°C]
REG_AIR_INLET_TEMP_2 = 1064  # (B46) Luftansaugtemperatur 2 [°C]

# Wärmepumpe direkt
REG_WP_VL_TEMP = 1050        # (B33) Wärmepumpenvorlauftemperatur [°C]
REG_RETURN_TEMP = 1052       # (B34) Rücklauftemperatur [°C]
REG_LOAD_TEMP = 1066         # (B45) Ladefühler [°C]
#REG_FLOW_SENSOR = 1072       # (B2) Durchfluss Heizung [l/min] (ohne Sensor ggf. -1)
REG_FLOW_SENSOR = 1073       # (B2) Durchfluss Heizung [l/min] (ohne Sensor ggf. -1)

# Heizkreise
REG_HKA_VL = 1350            # (B49) Heizkreis A Vorlauftemperatur [°C]
REG_HKA_VL_SOLL = 1378       # (B49s) Heizkreis A Soll-Vorlauftemperatur [°C]
REG_HKC_VL = 1354            # (B59) Heizkreis C Vorlauftemperatur [°C]
REG_HKC_VL_SOLL = 1382       # (B59s) Heizkreis C Soll-Vorlauftemperatur [°C]
REG_HKA_MODE = 1393          # (HKAMODE) Betriebsart Heizkreis A (UCHAR RW)
REG_HKC_MODE = 1395          # (HKCMODE) Betriebsart Heizkreis C (UCHAR RW)
REG_HKA_ACTIVE_MODE = 1498   # (B55) Aktive Betriebsart Heizkreis A (UCHAR RO)
REG_HKC_ACTIVE_MODE = 1500   # (B65) Aktive Betriebsart Heizkreis C (UCHAR RO)
REG_HKA_HEATLIMIT = 1442     # (HKA08) Heizgrenze HK A [°C] (UCHAR RW, 0..50)
REG_HKC_HEATLIMIT = 1444     # (HKC08) Heizgrenze HK C [°C] (UCHAR RW, 0..50)
REG_HKA_CURVE = 1429         # (HKA10) Heizkurve HK A (FLOAT RW, 0.0..3.5)
REG_HKC_CURVE = 1433         # (HKC10) Heizkurve HK C (FLOAT RW, 0.0..3.5)
REG_HKA_PARALLEL = 1505      # (HKA03) Parallelverschiebung HK A [°C] (UCHAR RW, 0..30)
REG_HKC_PARALLEL = 1507      # (HKC03) Parallelverschiebung HK C [°C] (UCHAR RW, 0..30)

# Warmwasser Sollwerte (UCHAR RW)
REG_WW_TARGET = 1032         # (FW030) Warmwasser-Solltemperatur [°C]
REG_WW_START  = 1033         # (FW027) WW-Ladung Einschalttemperatur [°C]
REG_WW_STOP   = 1034         # (FW028) WW-Ladung Ausschalttemperatur [°C]

# Warmwasser Anforderung
REG_WW_REQUEST = 1712        # (WWREQ) Anforderung Warmwasserladung (BOOL RW)
REG_WW_ONETIME = 1713        # (WWONCE) Einmalige Warmwasserladung (BOOL RW)

# Heizen
REG_HEAT_REQUEST = 1710      # (HEATREQ) Anforderung Heizen (BOOL RW)

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
REG_THERMAL_POWER = 1790     # Thermische Momentanleistung [kW]
REG_SOLAR_POWER   = 1792     # Momentanleistung Solar [kW]

# Solar (Temperaturen und Modus)
REG_SOLAR_COLLECTOR_TEMP = 1850  # (B73) Solarkollektortemperatur [°C]
REG_SOLAR_RETURN_TEMP    = 1852  # (B75) Solarkollektorrücklauftemperatur [°C]
REG_SOLAR_CHARGE_TEMP    = 1854  # (B74) Solar-Ladetemperatur [°C]
REG_SOLAR_MODE           = 1856  # (SC002) Betriebsart Solar (UCHAR RW)

# Leistung WP (elektrisch)
REG_WP_POWER = 4122             # Elektrische Gesamtleistung Wärmepumpe [kW]

# PV / Batterie (RW/RO)
REG_PV_SURPLUS = 74
REG_EHEIZSTAB = 76
REG_PV_PRODUKTION = 78
REG_HAUSVERBRAUCH = 82
REG_BATTERIE_ENTLADUNG = 84
REG_BATTERIE_FUELLSTAND = 86
