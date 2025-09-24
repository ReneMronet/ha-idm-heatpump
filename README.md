# iDM Heat Pump Integration for Home Assistant

This integration allows you to monitor and control your iDM heat pump with Navigator 10.0 controller in Home Assistant via Modbus TCP.

## Features

- Read sensor values (temperatures, humidity, energy counters)
- Control system and heating circuit operation modes
- Set temperature setpoints
- Monitor system status and error codes
- Request heating, cooling and hot water
- PV surplus integration

## Requirements

- iDM heat pump with Navigator 10.0 controller
- Modbus TCP enabled on the Navigator controller
- The heat pump must be accessible on your network

## Installation

### HACS (recommended)

1. Open HACS in your Home Assistant instance
2. Go to Integrations
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add the URL of this repository and select "Integration" as category
https://github.com/ReneMronet/ha-idm-heatpump/
5. Click "Add"
6. Search for "iDM Heat Pump" and install it
7. Restart Home Assistant

### Manual Installation

1. Download the latest release from GitHub
2. Extract the content to the `custom_components` folder in your Home Assistant configuration directory
3. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "iDM Heat Pump"
4. Enter the configuration details:
   - Name: A name for your heat pump
   - IP Address: The IP address of your heat pump
   - Port: The Modbus TCP port (default: 502)
   - Unit ID: The Modbus Unit ID (default: 1)
   - Scan Interval: How often to query the heat pump (default: 60 seconds)

## Prepare your iDM Heat Pump

Before using this integration, you need to enable Modbus TCP on your Navigator 2.0 controller:

1. On the Navigator controller, go to "Settings" → "Building Management"
2. Set "Modbus TCP" to "On"
3. For using external temperature and humidity values from Home Assistant:
   - Set "BMS Outdoor Temperature" to "Yes"
   - Set "BMS Humidity Value" to "Yes"
4. Go to "General Settings" → "Network Settings"
5. Set a static IP address for the heat pump (recommended)

## Available Entities

After setup, you'll get the following entities:

### Sensors
Unterstützt werden Temperaturfühler, Energiemengen, Leistungen, PV-/Batteriewerte sowie schreib- und wählbare Sollwerte und Betriebsarten.

### Sensors
| Entity-ID                              | Beschreibung                                | Quelle | Einheit |
|----------------------------------------|---------------------------------------------|--------|---------|
| `sensor.idm_aussentemperatur`          | Außentemperatur                             | B32    | °C      |
| `sensor.idm_aussentemperatur_gemittelt`| Gemittelte Außentemperatur                  | B32a   | °C      |
| `sensor.idm_wp_vorlauf`                | Wärmepumpenvorlauftemperatur                | B33    | °C      |
| `sensor.idm_ruecklauf`                 | Rücklauftemperatur                          | B34    | °C      |
| `sensor.idm_ladefuehler`               | Ladefühler                                  | B45    | °C      |
| `sensor.idm_durchfluss`                | Durchfluss Heizung                          | B2     | l/min   |
| `sensor.idm_luftansaug`                | Luftansaugtemperatur                        | B37    | °C      |
| `sensor.idm_verdampferaustritt_1`      | Verdampferaustritt 1                        | B79    | °C      |
| `sensor.idm_fluessigkeitsleitung`      | Flüssigkeitsleitungstemperatur              | B87    | °C      |
| `sensor.idm_heissgas_1`                | Heißgastemperatur 1                         | B71    | °C      |
| `sensor.idm_waermespeicher`            | Wärmespeichertemperatur                     | B41    | °C      |
| `sensor.idm_ww_oben`                   | Warmwasser oben                             | B43    | °C      |
| `sensor.idm_ww_unten`                  | Warmwasser unten                            | B44    | °C      |
| `sensor.idm_ww_zapftemp`               | Warmwasser-Zapftemperatur                   | B46    | °C      |
| `sensor.idm_hka_vorlauf`               | Heizkreis A Vorlauftemperatur               | B49    | °C      |
| `sensor.idm_hka_soll_vorlauf`          | Heizkreis A Soll-Vorlauftemperatur          | B49s   | °C      |
| `sensor.idm_hkc_vorlauf`               | Heizkreis C Vorlauftemperatur               | B59    | °C      |
| `sensor.idm_hkc_soll_vorlauf`          | Heizkreis C Soll-Vorlauftemperatur          | B59s   | °C      |
| `sensor.idm_status_warmepumpe`         | Status Wärmepumpe (Bereit/Heizbetrieb)      | B19    | -       |
| `sensor.idm_hka_aktive_betriebsart`    | Aktive Betriebsart Heizkreis A              | B55    | -       |
| `sensor.idm_hkc_aktive_betriebsart`    | Aktive Betriebsart Heizkreis C              | B65    | -       |
| `sensor.idm_wp_power`                  | Elektrische Gesamtleistung Wärmepumpe       | 4122   | kW      |
| `sensor.idm_pv_ueberschuss`            | PV-Überschuss                               | 74   	| kW      |
| `sensor.idm_e_heizstab`                | Leistung E-Heizstab                         | 76   	| kW      |
| `sensor.idm_pv_produktion`             | PV-Produktion                               | 78   	| kW      |
| `sensor.idm_hausverbrauch`             | Hausverbrauch                               | 82   	| kW      |
| `sensor.idm_batterie_entladung`        | Batterieentladung                           | 84   	| kW      |
| `sensor.idm_batterie_fuellstand`       | Batteriefüllstand                           | 86   	| %       |
| `sensor.idm_en_heizen`                 | Wärmemenge Heizen                           | 1748   | kWh     |
| `sensor.idm_en_gesamt`                 | Wärmemenge Gesamt                           | 1750   | kWh     |
| `sensor.idm_en_kuehlen`                | Wärmemenge Kühlen                           | 1752   | kWh     |
| `sensor.idm_en_warmwasser`             | Wärmemenge Warmwasser                       | 1754   | kWh     |
| `sensor.idm_en_abtauung`               | Wärmemenge Abtauung                         | 1756   | kWh     |
| `sensor.idm_en_passivkuehlung`         | Wärmemenge Passive Kühlung                  | 1758   | kWh     |
| `sensor.idm_en_solar`                  | Wärmemenge Solar                            | 1760   | kWh     |
| `sensor.idm_en_eheizer`                | Wärmemenge Elektroheizeinsatz               | 1762   | kWh     |
| `sensor.idm_thermische_leistung`       | Thermische Momentanleistung                 | 1790   | kW      |
| `sensor.idm_solar_leistung`            | Momentanleistung Solar                      | 1792   | kW      |
| `sensor.idm_solar_kollektor`           | Solarkollektortemperatur                    | B73    | °C      |
| `sensor.idm_solar_ruecklauf`           | Solarkollektorrücklauftemperatur            | B75    | °C      |
| `sensor.idm_solar_ladetemp`            | Solar-Ladetemperatur                        | B74    | °C      |

### Switches (3)
| Entity-ID                     | Beschreibung              | Register | Einheit |
|--------------------------------|---------------------------|----------|---------|
| `switch.idm_heat_request`      | Heizungsanforderung       | 1710     | -       |
| `switch.idm_ww_request`        | Warmwasseranforderung     | 1712     | -       |
| `switch.idm_ww_onetime`        | Einmalige Warmwasserladung| 1713     | -       |

### Numbers (7)
| Entity-ID                     | Beschreibung                       | Register | Einheit |
|--------------------------------|------------------------------------|----------|---------|
| `number.idm_hka_temp_normal`   | HK A Solltemperatur Normal         | 1401     | °C      |
| `number.idm_hkc_temp_normal`   | HK C Solltemperatur Normal         | 1405     | °C      |
| `number.idm_hka_temp_eco`      | HK A Solltemperatur Eco            | 1415     | °C      |
| `number.idm_hkc_temp_eco`      | HK C Solltemperatur Eco            | 1419     | °C      |
| `number.idm_ww_target`         | WW-Solltemperatur                  | 1032     | °C      |
| `number.idm_ww_start`          | WW-Ladung Starttemperatur          | 1033     | °C      |
| `number.idm_ww_stop`           | WW-Ladung Stopp-Temperatur         | 1034     | °C      |

### Selects (4)
| Entity-ID                     | Beschreibung                 | Register | Einheit |
|--------------------------------|------------------------------|----------|---------|
| `select.idm_betriebsart`       | Betriebsart System           | 1005     | -       |
| `select.idm_hka_betriebsart`   | Betriebsart Heizkreis A      | 1393     | -       |
| `select.idm_hkc_betriebsart`   | Betriebsart Heizkreis C      | 1395     | -       |
| `select.idm_solar_betriebsart` | Betriebsart Solar            | 1856     | -       |

## Hinweise
- Energiemengen (`en_*`) sind als `state_class: total_increasing` definiert.  
- Sollwerte (`number.*`) werden nur bei Änderung an die Wärmepumpe geschrieben, um EEPROM-Zyklen zu schonen.  
- Übersetzungen sind in `translations/de.json` und `translations/en.json` enthalten.  
- Getestet mit Home Assistant 2025.x.

### Controls
- System operation mode (Standby, Auto, Away, etc.)
- Heating circuit modes
- Temperature setpoints
- Heating/Cooling/DHW requests

## Troubleshooting

If you encounter issues:

1. Check if the heat pump is reachable via the network
2. Verify that Modbus TCP is enabled in the Navigator controller
3. Check the Home Assistant logs for error messages
4. Try increasing the scan interval if you experience timeouts

Additional Resources

iDM Documentation: 812663_Rev.0 - Navigator 10.0 Modbus Interface
Home Assistant Modbus: Official Documentation (https://www.home-assistant.io/integrations/modbus/)
Pymodbus Library: GitHub Repository (https://github.com/riptideio/pymodbus)



