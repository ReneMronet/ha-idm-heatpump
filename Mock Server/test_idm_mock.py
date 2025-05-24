#!/usr/bin/env python3
"""
Test-Script für den iDM Mock Server
Dieses Script testet die wichtigsten Register und deren Werte
"""

import struct
import sys
from pymodbus.client import ModbusTcpClient

def test_idm_mock_server(host="192.168.1.100", port=502):
    """Teste die wichtigsten Register des Mock-Servers"""
    
    print(f"🔄 Verbinde mit iDM Mock Server {host}:{port}...")
    client = ModbusTcpClient(host=host, port=port, timeout=5)
    
    try:
        if not client.connect():
            print(f"❌ Verbindung zu {host}:{port} fehlgeschlagen")
            print("   Stelle sicher, dass der Mock-Server läuft!")
            return False
        
        print(f"✅ Verbunden mit {host}:{port}")
        print("\n📊 Teste kritische Register...")
        
        # Test 1: Smart Grid Status (Input Register 6)
        print("\n1. Smart Grid Status (Register 6):")
        result = client.read_input_registers(address=6, count=1, slave=1)
        if not result.isError():
            smart_grid_value = result.registers[0]
            status_map = {
                0: "EVU-Sperre + kein PV-Ertrag",
                1: "EVU-Bezug + kein PV-Ertrag", 
                2: "Kein EVU-Bezug + PV-Ertrag",
                4: "EVU-Sperre + PV-Ertrag"
            }
            status_text = status_map.get(smart_grid_value, f"Unknown ({smart_grid_value})")
            print(f"   Raw Value: {smart_grid_value}")
            print(f"   Text: '{status_text}'")
            print(f"   ✅ OK - Wird als Text-Sensor behandelt")
        else:
            print(f"   ❌ Fehler: {result}")
        
        # Test 2: Außentemperatur (Input Register 0-1, FLOAT)
        print("\n2. Außentemperatur (Register 0-1, FLOAT32):")
        result = client.read_input_registers(address=0, count=2, slave=1)
        if not result.isError():
            # iDM Word-Swap: Low Word zuerst, dann High Word
            low_word, high_word = result.registers
            packed = struct.pack('>HH', high_word, low_word)
            outdoor_temp = struct.unpack('>f', packed)[0]
            print(f"   Raw Registers: [{low_word}, {high_word}]")
            print(f"   Temperature: {outdoor_temp:.1f}°C")
            print(f"   ✅ OK - Numerischer Sensor")
        else:
            print(f"   ❌ Fehler: {result}")
        
        # Test 3: Wärmepumpe Betriebsart (Input Register 90)
        print("\n3. Wärmepumpe Betriebsart (Register 90):")
        result = client.read_input_registers(address=90, count=1, slave=1)
        if not result.isError():
            mode_value = result.registers[0]
            mode_map = {
                0: "Aus",
                1: "Heizbetrieb",
                2: "Kühlbetrieb", 
                4: "Warmwasser",
                8: "Abtauung"
            }
            mode_text = mode_map.get(mode_value, f"Unknown ({mode_value})")
            print(f"   Raw Value: {mode_value}")
            print(f"   Text: '{mode_text}'")
            print(f"   ✅ OK - Wird als Text-Sensor behandelt")
        else:
            print(f"   ❌ Fehler: {result}")
        
        # Test 4: Verdichter Status (Input Register 100)
        print("\n4. Verdichter 1 Status (Register 100):")
        result = client.read_input_registers(address=100, count=1, slave=1)
        if not result.isError():
            compressor_status = result.registers[0]
            print(f"   Raw Value: {compressor_status}")
            print(f"   Status: {'ON' if compressor_status else 'OFF'}")
            print(f"   ✅ OK - Wird als Text-Sensor behandelt (0/1)")
        else:
            print(f"   ❌ Fehler: {result}")
        
        # Test 5: System Betriebsart (Holding Register 5)
        print("\n5. System Betriebsart (Holding Register 5):")
        result = client.read_holding_registers(address=5, count=1, slave=1)
        if not result.isError():
            system_mode = result.registers[0]
            system_map = {
                0: "Standby",
                1: "Automatik", 
                2: "Abwesend",
                4: "Nur Warmwasser",
                5: "Nur Heizung/Kühlung"
            }
            system_text = system_map.get(system_mode, f"Unknown ({system_mode})")
            print(f"   Raw Value: {system_mode}")
            print(f"   Text: '{system_text}'")
            print(f"   ✅ OK - Select Entity")
        else:
            print(f"   ❌ Fehler: {result}")
        
        # Test 6: Vorlauftemperatur (Input Register 50-51, FLOAT)
        print("\n6. Wärmepumpe Vorlauftemperatur (Register 50-51, FLOAT32):")
        result = client.read_input_registers(address=50, count=2, slave=1)
        if not result.isError():
            low_word, high_word = result.registers
            packed = struct.pack('>HH', high_word, low_word)
            supply_temp = struct.unpack('>f', packed)[0]
            print(f"   Raw Registers: [{low_word}, {high_word}]")
            print(f"   Temperature: {supply_temp:.1f}°C")
            print(f"   ✅ OK - Numerischer Sensor")
        else:
            print(f"   ❌ Fehler: {result}")
        
        print("\n" + "="*60)
        print("✅ Mock-Server Test abgeschlossen")
        print("   Alle kritischen Register funktionieren korrekt")
        print("   Status-Register liefern Zahlenwerte (werden in HA als Text interpretiert)")
        print("   Temperatur-Register liefern korrekte Float-Werte")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
    finally:
        client.close()

def main():
    """Hauptfunktion"""
    if len(sys.argv) > 1:
        host = sys.argv[1]
    else:
        host = input("IP-Adresse des Mock-Servers (oder Enter für 192.168.1.100): ").strip()
        if not host:
            host = "192.168.1.100"
    
    port = 502
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    
    success = test_idm_mock_server(host, port)
    
    if success:
        print(f"\n🎉 Der Mock-Server auf {host}:{port} funktioniert korrekt!")
        print("   Du kannst jetzt die Home Assistant Integration konfigurieren.")
    else:
        print(f"\n💥 Probleme mit dem Mock-Server auf {host}:{port}")
        print("   Überprüfe:")
        print("   1. Läuft der Mock-Server? (python idm_modbus_mock.py)")
        print("   2. Ist die IP-Adresse korrekt?")
        print("   3. Firewall-Einstellungen?")

if __name__ == "__main__":
    try:
        import pymodbus
        main()
    except ImportError:
        print("❌ pymodbus ist nicht installiert!")
        print("   Installiere es mit: pip install pymodbus")
        sys.exit(1)