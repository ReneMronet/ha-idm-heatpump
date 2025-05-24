#!/usr/bin/env python3
"""
iDM Navigator 2.0 Heat Pump Modbus TCP Mock Server
Basierend auf der offiziellen iDM Dokumentation (812170_Rev.7)
Simuliert eine iDM Wärmepumpe mit Navigator 2.0 für Home Assistant Integration Tests
"""

import asyncio
import logging
import random
import time
import socket
import struct
from pymodbus.server.async_io import StartAsyncTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadBuilder, BinaryPayloadDecoder

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IDMNavigator2Mock:
    def __init__(self):
        self.running = True
        self.start_time = time.time()
        
        # Navigator 2.0 System Info
        self.navigator_version = "20.15-0"
        self.system_id = "IDM-NAV2-MOCK"
        self.unit_id = 1
        self.tcp_port = 502  # Offizieller Modbus TCP Port
        
        # Authentische iDM Register-Werte basierend auf Dokumentation
        self.register_values = {
            # Basis Temperaturen (FLOAT Werte)
            1000: -5.0,    # Außentemperatur (B31) [°C]
            1002: -4.8,    # Gemittelte Außentemperatur [°C]
            1008: 45.2,    # Wärmespeichertemperatur (B38) [°C]
            1010: 12.5,    # Kältespeichertemperatur (B40) [°C]
            1012: 48.3,    # Trinkwassererwärmertemp. unten (B41) [°C]
            1014: 52.7,    # Trinkwassererwärmertemp. oben (B48) [°C]
            1030: 51.2,    # Warmwasserzapftemperatur (B42) [°C]
            1050: 42.5,    # Wärmepumpen Vorlauftemperatur (B33) [°C]
            1052: 38.2,    # Wärmepumpen Rücklauftemperatur (B34) [°C]
            1054: 41.8,    # HGL Vorlauftemperatur (B35) [°C]
            1056: 8.5,     # Wärmequelleneintrittstemperatur (B43) [°C]
            1058: 3.2,     # Wärmequellenaustrittstemperatur (B36) [°C]
            1060: -3.8,    # Luftansaugtemperatur (B37) [°C]
            1062: -2.1,    # Luftwärmetauschertemperatur (B72) [°C]
            1064: -4.2,    # Luftansaugtemperatur 2 (B46) [°C]
            
            # Heizkreis Temperaturen
            1350: 42.3,    # Heizkreis A Vorlauftemperatur (B51) [°C]
            1352: 38.1,    # Heizkreis B Vorlauftemperatur (B52) [°C]
            1364: 21.5,    # Heizkreis A Raumtemperatur (B61) [°C]
            1366: 20.8,    # Heizkreis B Raumtemperatur (B62) [°C]
            1378: 43.0,    # Heizkreis A Sollvorlauftemperatur [°C]
            1380: 40.0,    # Heizkreis B Sollvorlauftemperatur [°C]
            1392: 45.2,    # Feuchtesensor [%rF]
            
            # Status Register (UCHAR/WORD Werte)
            1004: 0,       # Aktuelle Störungsnummer
            1005: 1,       # Betriebsart System SYSMODE (0-5)
            1006: 1,       # Smart Grid Status (0-4)
            1032: 46,      # Warmwasser-Solltemperatur [°C]
            1033: 46,      # Warmwasserladung Einschalttemperatur [°C]
            1034: 50,      # Warmwasserladung Ausschalttemperatur [°C]
            
            # Wärmepumpe Status
            1090: 1,       # Betriebsart Wärmepumpe (0-8)
            1099: 0,       # Summenstörung Wärmepumpe (0-1)
            1100: 1,       # Status Verdichter 1 (0-1)
            1101: 0,       # Status Verdichter 2 (0-1)
            1102: 0,       # Status Verdichter 3 (0-1)
            1103: 0,       # Status Verdichter 4 (0-1)
            1104: 75,      # Status Ladepumpe (M73) [%]
            1105: 85,      # Status Sole/Zwischenkreispumpe (M16)
            1106: 90,      # Status Wärmequellen/Grundwasserpumpe (M15)
            
            # Heizkreis Betriebsarten und Sollwerte
            1393: 1,       # Betriebsart Heizkreis A (0-5)
            1394: 1,       # Betriebsart Heizkreis B (0-5)
            1401: 22.0,    # Raumsolltemperatur Heizen Normal HK A [°C]
            1403: 22.0,    # Raumsolltemperatur Heizen Normal HK B [°C]
            1415: 18.0,    # Raumsolltemperatur Heizen Eco HK A [°C]
            1417: 18.0,    # Raumsolltemperatur Heizen Eco HK B [°C]
            1429: 1.2,     # Heizkurve HK A
            1431: 1.2,     # Heizkurve HK B
            1442: 15,      # Heizgrenze HK A [°C]
            1443: 15,      # Heizgrenze HK B [°C]
            1449: 45,      # Sollvorlauftemperatur HK A (Konstant-HK) [°C]
            1450: 45,      # Sollvorlauftemperatur HK B (Konstant-HK) [°C]
            
            # Aktive Betriebsarten (Read-Only)
            1498: 1,       # Aktive Betriebsart Heizkreis A (0-2)
            1499: 1,       # Aktive Betriebsart Heizkreis B (0-2)
            
            # Externe Werte (Write)
            1650: 0.0,     # Externe Raumtemperatur HK A [°C]
            1652: 0.0,     # Externe Raumtemperatur HK B [°C]
            1690: 0.0,     # Externe Außentemperatur [°C]
            1692: 0.0,     # Externe Feuchte [%rF]
            1694: 40,      # Externe Anforderungstemperatur Heizen [°C]
            1695: 18,      # Externe Anforderungstemperatur Kühlen [°C]
            1710: 0,       # Anforderung Heizen (0-1)
            1711: 0,       # Anforderung Kühlen (0-1)
            1712: 0,       # Anforderung Warmwasserladung (0-1)
            
            # Energiewerte (FLOAT - nur bei entsprechenden Geräten)
            1750: 1250.5,  # Wärmemenge Heizen [kWh]
            1752: 125.2,   # Wärmemenge Kühlen [kWh]
            1754: 380.7,   # Wärmemenge Warmwasser [kWh]
            1790: 8.5,     # Momentanleistung [kW]
            
            # PV Integration
            74: 0.0,       # Aktueller PV-Überschuss [kW]
            78: 0.0,       # Aktuelle PV Produktion [kW]
            4122: 2.5,     # Aktuelle Leistungsaufnahme Wärmepumpe [kW]
            
            # Störmeldungen quittieren
            1999: 0,       # Störmeldungen quittieren (Write)
        }
        
        # TCP Connection Tracking
        self.tcp_connections = 0
        self.last_connection_time = time.time()

    def simulate_realistic_values(self):
        """Simuliert realistische, sich ändernde Werte basierend auf iDM Spezifikation"""
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # Zyklische Schwankungen
        cycle_10min = (elapsed % 600) / 600  # 10-Minuten-Zyklus
        cycle_1h = (elapsed % 3600) / 3600   # 1-Stunden-Zyklus
        cycle_24h = (elapsed % 86400) / 86400 # 24-Stunden-Zyklus
        
        # Außentemperatur variiert langsam (-10°C bis +5°C)
        outdoor_temp = -5.0 + 8.0 * (0.5 + 0.5 * cycle_24h) + 2.0 * random.uniform(-0.5, 0.5)
        self.register_values[1000] = outdoor_temp
        self.register_values[1002] = outdoor_temp + random.uniform(-0.5, 0.5)  # Gemittelt
        
        # Kompressor Status simulieren (zyklisch ein/aus)
        compressor_on = elapsed % 300 < 240  # 4 Min an, 1 Min aus
        self.register_values[1100] = 1 if compressor_on else 0
        
        # Betriebsart Wärmepumpe je nach Kompressor
        if compressor_on:
            self.register_values[1090] = 1  # Heizbetrieb
        else:
            self.register_values[1090] = 0  # Aus
        
        # Temperaturen abhängig vom Kompressor-Status
        if compressor_on:
            # Vorlauftemperatur steigt
            base_supply = 40.0 + 8.0 * cycle_10min
            self.register_values[1050] = base_supply + random.uniform(-1.0, 1.0)
            self.register_values[1052] = self.register_values[1050] - 4.0  # Rücklauf
            self.register_values[1054] = self.register_values[1050] - 1.0  # HGL
            
            # Heizkreis Temperaturen
            self.register_values[1350] = base_supply + random.uniform(-2.0, 2.0)
            self.register_values[1378] = base_supply + 1.0  # Sollwert
            
            # Pumpen laufen
            self.register_values[1104] = int(70 + 20 * cycle_10min)  # Ladepumpe %
            self.register_values[1105] = int(80 + 15 * cycle_10min)  # Solepumpe
            self.register_values[1106] = int(85 + 10 * cycle_10min)  # Grundwasserpumpe
        else:
            # Temperaturen sinken langsam
            self.register_values[1050] = max(25.0, self.register_values[1050] - 0.5)
            self.register_values[1052] = max(22.0, self.register_values[1052] - 0.3)
            self.register_values[1350] = max(20.0, self.register_values[1350] - 0.4)
            
            # Pumpen aus oder reduziert
            self.register_values[1104] = 0   # Ladepumpe aus
            self.register_values[1105] = 30  # Solepumpe reduziert
            self.register_values[1106] = 0   # Grundwasserpumpe aus
        
        # Warmwasser Temperaturen
        self.register_values[1008] = 44.0 + 6.0 * cycle_1h + random.uniform(-1.0, 1.0)
        self.register_values[1012] = 46.0 + 4.0 * cycle_1h + random.uniform(-0.5, 0.5)
        self.register_values[1014] = self.register_values[1012] + 4.0
        self.register_values[1030] = self.register_values[1014] - 1.0
        
        # Raumtemperaturen (langsame Änderung)
        target_room_temp = 21.5
        room_variation = 1.0 * cycle_1h
        self.register_values[1364] = target_room_temp + room_variation + random.uniform(-0.2, 0.2)
        self.register_values[1366] = target_room_temp + room_variation + random.uniform(-0.2, 0.2)
        
        # Wärmequellen Temperaturen
        source_temp_in = outdoor_temp + 8.0 + 2.0 * cycle_10min
        self.register_values[1056] = source_temp_in + random.uniform(-0.5, 0.5)
        self.register_values[1058] = source_temp_in - 5.0 + random.uniform(-0.5, 0.5)
        
        # Lufttemperaturen
        self.register_values[1060] = outdoor_temp + random.uniform(-1.0, 1.0)
        self.register_values[1062] = outdoor_temp + 2.0 + random.uniform(-0.5, 0.5)
        self.register_values[1064] = outdoor_temp - 0.5 + random.uniform(-0.5, 0.5)
        
        # Feuchte Sensor
        base_humidity = 45.0
        humidity_variation = 10.0 * cycle_24h
        self.register_values[1392] = base_humidity + humidity_variation + random.uniform(-2.0, 2.0)
        
        # Smart Grid Status (simuliert PV-Zeiten)
        hour_of_day = (elapsed % 86400) / 3600
        if 10 <= hour_of_day <= 16:  # Sonnenstunden
            # PV Überschuss simulieren
            pv_factor = 1.0 - abs(13 - hour_of_day) / 3  # Peak um 13 Uhr
            pv_production = 5000 * pv_factor * random.uniform(0.7, 1.0)
            current_consumption = self.register_values[4122] * 1000  # kW zu W
            pv_excess = max(0, pv_production - current_consumption)
            
            self.register_values[78] = pv_production / 1000  # PV Produktion [kW]
            self.register_values[74] = pv_excess / 1000      # PV Überschuss [kW]
            
            # Smart Grid Status setzen
            if pv_excess > 1500:
                self.register_values[1006] = 2  # Kein EVU-Bezug u. PV-Ertrag
            elif pv_production > 500:
                self.register_values[1006] = 1  # EVU-Bezug u. kein PV-Ertrag
            else:
                self.register_values[1006] = 0  # EVU-Sperre u. kein PV-Ertrag
        else:
            self.register_values[78] = 0.0   # Keine PV Produktion
            self.register_values[74] = 0.0   # Kein PV Überschuss
            self.register_values[1006] = 1   # EVU-Bezug u. kein PV-Ertrag
        
        # Leistungsaufnahme Wärmepumpe
        if compressor_on:
            power_base = 2.5 + 1.5 * cycle_10min
            self.register_values[4122] = power_base + random.uniform(-0.3, 0.3)
        else:
            self.register_values[4122] = 0.15 + random.uniform(-0.05, 0.05)  # Standby
        
        # Momentanleistung (Wärmeleistung)
        if compressor_on:
            heating_power = self.register_values[4122] * 3.2  # COP ~3.2
            self.register_values[1790] = heating_power + random.uniform(-0.5, 0.5)
        else:
            self.register_values[1790] = 0.0
        
        # Energiezähler kontinuierlich erhöhen
        if compressor_on and elapsed % 60 == 0:  # Jede Minute
            self.register_values[1750] += 0.02  # Heizenergie
            if self.register_values[1008] < 50:  # Warmwasser laden
                self.register_values[1754] += 0.01  # Warmwasserenergie
        
        # Aktive Betriebsarten Heizkreise
        if compressor_on:
            self.register_values[1498] = 1  # Heizen
            self.register_values[1499] = 1  # Heizen
        else:
            self.register_values[1498] = 0  # Aus
            self.register_values[1499] = 0  # Aus
        
        # Gelegentliche Abtauung (alle 2 Stunden für 2 Minuten)
        if elapsed % 7200 < 120 and outdoor_temp < 2.0:
            self.register_values[1090] = 8  # Abtauung
        
        # Störungen simulieren (sehr selten)
        if random.random() < 0.0001:  # 0.01% Chance
            self.register_values[1004] = random.choice([101, 205, 301])  # Beispiel Störcodes
            self.register_values[1099] = 1  # Summenstörung
        else:
            if self.register_values[1004] != 0 and random.random() < 0.1:  # 10% Chance Störung zu löschen
                self.register_values[1004] = 0
                self.register_values[1099] = 0

    def create_modbus_context(self):
        """Erstellt den Modbus Kontext basierend auf iDM Navigator 2.0 Spezifikation"""
        
        # Holding Registers (Read/Write) - 40001+
        holding_registers = [0] * 5000
        
        # Input Registers (Read Only) - 30001+
        input_registers = [0] * 5000
        
        # Register mapping basierend auf iDM Dokumentation
        # Die meisten Register sind Input Register (Read-Only)
        input_register_map = {
            # Temperaturen (FLOAT - 2 Register je Wert)
            0: 1000,    # 30001-30002: Außentemperatur
            2: 1002,    # 30003-30004: Gemittelte Außentemperatur
            8: 1008,    # 30009-30010: Wärmespeichertemperatur
            10: 1010,   # 30011-30012: Kältespeichertemperatur
            12: 1012,   # 30013-30014: Trinkwassererwärmertemp. unten
            14: 1014,   # 30015-30016: Trinkwassererwärmertemp. oben
            30: 1030,   # 30031-30032: Warmwasserzapftemperatur
            50: 1050,   # 30051-30052: Wärmepumpen Vorlauftemperatur
            52: 1052,   # 30053-30054: Wärmepumpen Rücklauftemperatur
            54: 1054,   # 30055-30056: HGL Vorlauftemperatur
            56: 1056,   # 30057-30058: Wärmequelleneintrittstemperatur
            58: 1058,   # 30059-30060: Wärmequellenaustrittstemperatur
            60: 1060,   # 30061-30062: Luftansaugtemperatur
            62: 1062,   # 30063-30064: Luftwärmetauschertemperatur
            64: 1064,   # 30065-30066: Luftansaugtemperatur 2
            
            # Status Register (UCHAR/WORD - 1 Register je Wert)
            4: 1004,    # 30005: Aktuelle Störungsnummer
            6: 1006,    # 30007: Smart Grid Status
            90: 1090,   # 30091: Betriebsart Wärmepumpe
            99: 1099,   # 30100: Summenstörung Wärmepumpe
            100: 1100,  # 30101: Status Verdichter 1
            101: 1101,  # 30102: Status Verdichter 2
            102: 1102,  # 30103: Status Verdichter 3
            103: 1103,  # 30104: Status Verdichter 4
            104: 1104,  # 30105: Status Ladepumpe
            105: 1105,  # 30106: Status Sole/Zwischenkreispumpe
            106: 1106,  # 30107: Status Wärmequellen/Grundwasserpumpe
            
            # Heizkreis Temperaturen (FLOAT)
            350: 1350,  # 30351-30352: Heizkreis A Vorlauftemperatur
            352: 1352,  # 30353-30354: Heizkreis B Vorlauftemperatur
            364: 1364,  # 30365-30366: Heizkreis A Raumtemperatur
            366: 1366,  # 30367-30368: Heizkreis B Raumtemperatur
            378: 1378,  # 30379-30380: Heizkreis A Sollvorlauftemperatur
            380: 1380,  # 30381-30382: Heizkreis B Sollvorlauftemperatur
            392: 1392,  # 30393-30394: Feuchtesensor
            
            # Aktive Betriebsarten
            498: 1498,  # 30499: Aktive Betriebsart Heizkreis A
            499: 1499,  # 30500: Aktive Betriebsart Heizkreis B
            
            # Energiewerte (FLOAT)
            750: 1750,  # 30751-30752: Wärmemenge Heizen
            752: 1752,  # 30753-30754: Wärmemenge Kühlen
            754: 1754,  # 30755-30756: Wärmemenge Warmwasser
            790: 1790,  # 30791-30792: Momentanleistung
            
            # PV Werte (FLOAT)
            74: 74,     # 30075-30076: PV-Überschuss
            78: 78,     # 30079-30080: PV Produktion
            1122: 4122, # 31123-31124: Leistungsaufnahme Wärmepumpe
        }
        
        # Holding Registers (Read/Write)
        holding_register_map = {
            # System Betriebsart
            5: 1005,    # 40006: Betriebsart System SYSMODE
            
            # Solltemperaturen
            32: 1032,   # 40033: Warmwasser-Solltemperatur
            33: 1033,   # 40034: Warmwasserladung Einschalttemperatur  
            34: 1034,   # 40035: Warmwasserladung Ausschalttemperatur
            
            # Heizkreis Betriebsarten und Sollwerte
            393: 1393,  # 40394: Betriebsart Heizkreis A
            394: 1394,  # 40395: Betriebsart Heizkreis B
            401: 1401,  # 40402: Raumsolltemperatur Heizen Normal HK A
            403: 1403,  # 40404: Raumsolltemperatur Heizen Normal HK B
            415: 1415,  # 40416: Raumsolltemperatur Heizen Eco HK A
            417: 1417,  # 40418: Raumsolltemperatur Heizen Eco HK B
            429: 1429,  # 40430: Heizkurve HK A
            431: 1431,  # 40432: Heizkurve HK B
            442: 1442,  # 40443: Heizgrenze HK A
            443: 1443,  # 40444: Heizgrenze HK B
            449: 1449,  # 40450: Sollvorlauftemperatur HK A
            450: 1450,  # 40451: Sollvorlauftemperatur HK B
            
            # Externe Werte (Write)
            650: 1650,  # 40651: Externe Raumtemperatur HK A
            652: 1652,  # 40653: Externe Raumtemperatur HK B
            690: 1690,  # 40691: Externe Außentemperatur
            692: 1692,  # 40693: Externe Feuchte
            694: 1694,  # 40695: Externe Anforderungstemperatur Heizen
            695: 1695,  # 40696: Externe Anforderungstemperatur Kühlen
            710: 1710,  # 40711: Anforderung Heizen
            711: 1711,  # 40712: Anforderung Kühlen
            712: 1712,  # 40713: Anforderung Warmwasserladung
            
            # Service
            1999: 1999, # 42000: Störmeldungen quittieren
        }
        
        # Register mit Werten füllen
        self._fill_registers(input_registers, input_register_map)
        self._fill_registers(holding_registers, holding_register_map)
        
        # Datastore erstellen
        store = ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, [0] * 100),     # Discrete Inputs
            co=ModbusSequentialDataBlock(0, [0] * 100),     # Coils  
            hr=ModbusSequentialDataBlock(0, holding_registers), # Holding Registers
            ir=ModbusSequentialDataBlock(0, input_registers)    # Input Registers
        )
        
        context = ModbusServerContext(slaves=store, single=True)
        return context, input_register_map, holding_register_map

    def _fill_registers(self, registers, register_map):
        """Füllt Register-Array mit Werten"""
        for reg_addr, value_key in register_map.items():
            if reg_addr < len(registers) - 1:
                value = self.register_values.get(value_key, 0)
                
                # FLOAT Werte (32-bit) in 2 Register aufteilen
                if isinstance(value, float):
                    # IEEE 754 Float to 2x16-bit Register
                    packed = struct.pack('>f', value)  # Big-endian float
                    reg_high, reg_low = struct.unpack('>HH', packed)
                    registers[reg_addr] = reg_low      # Low Register first
                    registers[reg_addr + 1] = reg_high # High Register second
                else:
                    # Integer/UCHAR Werte direkt
                    registers[reg_addr] = int(value)


def get_local_ip():
    """Ermittelt die lokale IP-Adresse"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception:
            return "192.168.1.100"


async def update_values(context, mock, input_map, holding_map):
    """Aktualisiert die Modbus Register kontinuierlich"""
    while mock.running:
        try:
            # Simulierte Werte aktualisieren
            mock.simulate_realistic_values()
            
            # Input Register aktualisieren
            slave_context = context[0]
            
            # Alle Input Register durchgehen und aktualisieren
            for reg_addr, value_key in input_map.items():
                if value_key in mock.register_values:
                    value = mock.register_values[value_key]
                    
                    try:
                        if isinstance(value, float):
                            # Float32 mit Word-Swap für iDM
                            packed = struct.pack('>f', value)
                            high_word, low_word = struct.unpack('>HH', packed)
                            # iDM Format: Low Word zuerst, dann High Word
                            slave_context.setValues(4, reg_addr, [low_word, high_word])
                        else:
                            # Integer Werte
                            slave_context.setValues(4, reg_addr, [int(value)])
                    except Exception as e:
                        logger.error(f"Error updating register {reg_addr} (value_key: {value_key}): {e}")
            
            # Holding Register aktualisieren
            for reg_addr, value_key in holding_map.items():
                if value_key in mock.register_values:
                    value = mock.register_values[value_key]
                    
                    try:
                        if isinstance(value, float):
                            # Float32 mit Word-Swap für iDM
                            packed = struct.pack('>f', value)
                            high_word, low_word = struct.unpack('>HH', packed)
                            # iDM Format: Low Word zuerst, dann High Word
                            slave_context.setValues(3, reg_addr, [low_word, high_word])
                        else:
                            # Integer Werte
                            slave_context.setValues(3, reg_addr, [int(value)])
                    except Exception as e:
                        logger.error(f"Error updating holding register {reg_addr} (value_key: {value_key}): {e}")
            
            # Holding Register von außen lesen und in Mock übernehmen
            for reg_addr, value_key in holding_map.items():
                try:
                    if isinstance(mock.register_values.get(value_key, 0), float):
                        # FLOAT Werte aus 2 Registern lesen
                        reg_values = slave_context.getValues(3, reg_addr, 2)
                        if len(reg_values) == 2:
                            # iDM Format: Low Word zuerst, dann High Word
                            packed = struct.pack('>HH', reg_values[1], reg_values[0])
                            value = struct.unpack('>f', packed)[0]
                            mock.register_values[value_key] = value
                    else:
                        # Integer Werte
                        reg_value = slave_context.getValues(3, reg_addr, 1)[0]
                        mock.register_values[value_key] = reg_value
                except:
                    pass  # Fehler beim Lesen ignorieren
            
            # Debug: Wichtige Werte ausgeben
            logger.info(f"iDM Navigator 2.0 Status: "
                       f"Outdoor: {mock.register_values.get(1000, 'N/A'):.1f}°C, "
                       f"Supply: {mock.register_values.get(1050, 'N/A'):.1f}°C, "
                       f"Room A: {mock.register_values.get(1364, 'N/A'):.1f}°C, "
                       f"Power: {mock.register_values.get(4122, 'N/A'):.1f}kW, "
                       f"Compressor: {'ON' if mock.register_values.get(1100, 0) else 'OFF'}, "
                       f"Mode: {mock.register_values.get(1090, 'N/A')}, "
                       f"PV: {mock.register_values.get(74, 'N/A'):.1f}kW")
            
            # Zusätzliches Debug für kritische Register
            if logger.isEnabledFor(logging.DEBUG):
                # Prüfe ob Außentemperatur korrekt gesetzt ist
                outdoor_regs = slave_context.getValues(4, 0, 2)
                if outdoor_regs:
                    packed = struct.pack('>HH', outdoor_regs[1], outdoor_regs[0])
                    outdoor_temp = struct.unpack('>f', packed)[0]
                    logger.debug(f"Register 0-1 (Outdoor Temp): {outdoor_regs} = {outdoor_temp:.2f}°C")
            
        except Exception as e:
            logger.error(f"Error updating values: {e}", exc_info=True)
        
        await asyncio.sleep(5)  # Update alle 5 Sekunden


async def main():
    # Mock Objekt erstellen
    mock = IDMNavigator2Mock()
    
    # Modbus Kontext erstellen
    context, input_map, holding_map = mock.create_modbus_context()
    
    # Lokale IP ermitteln
    local_ip = get_local_ip()
    
    # Server Identifikation für Navigator 2.0
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'iDM Energiesysteme GmbH'
    identity.ProductCode = 'NAV2-HEATPUMP'
    identity.VendorUrl = 'https://www.idm-energie.at'
    identity.ProductName = 'iDM Navigator 2.0 Heat Pump'
    identity.ModelName = 'Navigator-2.0'
    identity.MajorMinorRevision = mock.navigator_version
    
    logger.info("=" * 80)
    logger.info("iDM Navigator 2.0 Heat Pump Modbus TCP Mock Server")
    logger.info("=" * 80)
    logger.info(f"Navigator Version: {mock.navigator_version}")
    logger.info(f"System ID: {mock.system_id}")
    logger.info(f"Server IP: {local_ip}:{mock.tcp_port}")
    logger.info(f"Modbus Unit ID: {mock.unit_id}")
    logger.info(f"Based on: 812170_Rev.7 - iDM Official Documentation")
    logger.info("=" * 80)
    
    logger.info("\niDM Navigator 2.0 Authentic Register Map:")
    logger.info("-" * 50)
    logger.info("Key Input Registers (30001+):")
    logger.info("  30001-30002: Außentemperatur (B31)")
    logger.info("  30005: Aktuelle Störungsnummer")
    logger.info("  30007: Smart Grid Status")
    logger.info("  30051-30052: Wärmepumpen Vorlauftemperatur (B33)")
    logger.info("  30053-30054: Wärmepumpen Rücklauftemperatur (B34)")
    logger.info("  30091: Betriebsart Wärmepumpe")
    logger.info("  30101: Status Verdichter 1")
    logger.info("  30351-30352: Heizkreis A Vorlauftemperatur (B51)")
    logger.info("  30365-30366: Heizkreis A Raumtemperatur (B61)")
    logger.info("  30393-30394: Feuchtesensor")
    logger.info("  30499: Aktive Betriebsart Heizkreis A")
    logger.info("  30751-30752: Wärmemenge Heizen")
    logger.info("  31123-31124: Aktuelle Leistungsaufnahme Wärmepumpe")
    
    logger.info("\nKey Holding Registers (40001+):")
    logger.info("  40006: Betriebsart System SYSMODE")
    logger.info("  40033: Warmwasser-Solltemperatur")
    logger.info("  40394: Betriebsart Heizkreis A")
    logger.info("  40402: Raumsolltemperatur Heizen Normal HK A")
    logger.info("  40651: Externe Raumtemperatur HK A")
    logger.info("  40691: Externe Außentemperatur")
    logger.info("  40711: Anforderung Heizen")
    logger.info("  40712: Anforderung Kühlen")
    
    logger.info("\niDM Betriebsarten:")
    logger.info("  System SYSMODE: 0=Standby, 1=Automatik, 2=Abwesend, 4=Nur Warmwasser, 5=Nur Heizung")
    logger.info("  Wärmepumpe: 0=Aus, 1=Heizbetrieb, 2=Kühlbetrieb, 4=Warmwasser, 8=Abtauung")
    logger.info("  Heizkreis: 0=Aus, 1=Zeitprogramm, 2=Normal, 3=Eco, 4=Manuell Heizen, 5=Manuell Kühlen")
    logger.info("  Smart Grid: 0=EVU-Sperre+kein PV, 1=EVU-Bezug+kein PV, 2=Kein EVU+PV-Ertrag, 4=EVU-Sperre+PV")
    
    logger.info("\nHome Assistant Configuration Example:")
    logger.info("-" * 40)
    logger.info("modbus:")
    logger.info("  - name: idm_navigator2")
    logger.info("    type: tcp")
    logger.info(f"    host: {local_ip}")
    logger.info(f"    port: {mock.tcp_port}")
    logger.info("    sensors:")
    logger.info("      - name: 'iDM Außentemperatur'")
    logger.info("        address: 0")
    logger.info("        input_type: input")
    logger.info("        data_type: float32")
    logger.info("        swap: word")
    logger.info("        unit_of_measurement: '°C'")
    logger.info("      - name: 'iDM Vorlauftemperatur'")
    logger.info("        address: 50")
    logger.info("        input_type: input")
    logger.info("        data_type: float32")
    logger.info("        swap: word")
    logger.info("        unit_of_measurement: '°C'")
    logger.info("      - name: 'iDM Verdichter Status'")
    logger.info("        address: 100")
    logger.info("        input_type: input")
    logger.info("        data_type: uint16")
    logger.info("      - name: 'iDM Betriebsart'")
    logger.info("        address: 90")
    logger.info("        input_type: input")
    logger.info("        data_type: uint16")
    logger.info("      - name: 'iDM Raumtemperatur HK A'")
    logger.info("        address: 364")
    logger.info("        input_type: input")
    logger.info("        data_type: float32")
    logger.info("        swap: word")
    logger.info("        unit_of_measurement: '°C'")
    logger.info("      - name: 'iDM Leistungsaufnahme'")
    logger.info("        address: 1122")
    logger.info("        input_type: input")
    logger.info("        data_type: float32")
    logger.info("        swap: word")
    logger.info("        unit_of_measurement: 'kW'")
    
    logger.info("\nStarting iDM Navigator 2.0 TCP Modbus Server...")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 80)
    
    # Update Task starten
    update_task = asyncio.create_task(
        update_values(context, mock, input_map, holding_map)
    )
    
    try:
        # TCP Server mit Navigator 2.0 Support starten
        await StartAsyncTcpServer(
            context=context,
            identity=identity,
            address=(local_ip, mock.tcp_port),
            custom_functions=[]
        )
    except KeyboardInterrupt:
        logger.info("\nShutting down iDM Navigator 2.0 Mock Server...")
        mock.running = False
        update_task.cancel()
        try:
            await update_task
        except asyncio.CancelledError:
            pass
        logger.info("Server stopped.")


if __name__ == "__main__":
    # Abhängigkeiten prüfen
    try:
        import pymodbus
        logger.info(f"Using pymodbus version: {pymodbus.__version__}")
        
        # Prüfe ob TCP Support verfügbar ist
        from pymodbus.server.async_io import StartAsyncTcpServer
        logger.info("TCP Modbus support: Available")
        
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error("Install with: pip install pymodbus")
        exit(1)
    
    # Navigator 2.0 Banner
    print("""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                           iDM Navigator 2.0                              ║
    ║                       Heat Pump Mock Server                              ║
    ║                                                                          ║
    ║  Authentic iDM Modbus TCP Implementation based on 812170_Rev.7           ║
    ║  Features: Real Register Map | Authentic Values | PV Integration         ║
    ║           Multi-Zone Support | Smart Grid | Energy Monitoring            ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())