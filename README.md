# iDM Heat Pump Integration for Home Assistant

This integration allows you to monitor and control your iDM heat pump with Navigator 10.0 controller in Home Assistant via Modbus TCP.

## Features

* Read sensor values (temperatures, humidity, energy counters)
* Control system and heating circuit operation modes
* Set temperature setpoints
* Monitor system status and error codes
* Request heating, cooling and hot water
* PV surplus integration
* **7 heating circuits** (A–G) dynamically configurable
* **6 sensor groups**: Solar, PV/Battery, Cooling, Diagnostic, Room Control, Extended Temps
* **Room temperature forwarding**: External sensors (e.g. Shelly H&T) → heat pump via Modbus
* **Temperature offset** per heating circuit for fine-tuning (NEW in v0.7.0)
* **Seasonal automation** with master switch
* **EEPROM protection**: Write operations only on actual value changes
* **Auto-detect**: Sensors not physically installed are automatically hidden
* **Entity cleanup**: Orphaned entities are removed on config change
* **Fully translated** (German / English)

## Requirements

* iDM heat pump with Navigator 10.0 controller
* Modbus TCP enabled on the Navigator controller
* The heat pump must be accessible on your network

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

### Initial Setup (4 Steps)

1. Go to Settings → Devices & Services → "Add Integration" → search "iDM Heat Pump"
2. **Connection**: IP address, Port (502), Unit ID (1), Update interval (30s)
3. **Heating circuits & sensor groups**: Select active heating circuits (A–G) and sensor groups
4. **Room temperature forwarding**: Assign external temperature sensors per heating circuit, choose write interval, enable seasonal automation
5. **Season period** (only if seasonal automation is enabled): Start/end month and day

### Reconfiguration

Settings → Integrations → iDM Wärmepumpe → ⚙️ Configure

## Prepare your iDM Heat Pump

Before using this integration, you need to enable Modbus TCP on your Navigator 10.0 controller:

1. On the Navigator controller, go to "Settings" → "Building Management"
2. Set "Modbus TCP" to "On"
3. For using external temperature and humidity values from Home Assistant:
   * Set "BMS Outdoor Temperature" to "Yes"
   * Set "BMS Humidity Value" to "Yes"
4. Go to "General Settings" → "Network Settings"
5. Set a static IP address for the heat pump (recommended)

## Sensor Groups

Configurable in Config/Options Flow. Each group enables additional registers.

| Group | Registers | Description |
|-------|-----------|-------------|
| `solar` | 5 | Collector, return, charge temp, power, mode |
| `pv_battery` | 9 | PV surplus, E-heater, production, consumption, battery, SmartGrid, electricity price |
| `cooling` | 3 + 4×HC | Cooling request WP/DHW + cooling parameters per HC |
| `diagnostic` | 8 | Faults, EVU lock, compressor, pumps, valves |
| `room_control` | 1 + 1×HC | Humidity sensor + room temperature per HC |
| `extended_temps` | 4 | Heat exchanger, heat sink, cold storage |

Default: `solar`, `pv_battery`

## Available Entities

After setup, you'll get the following entities (75+ depending on configuration):

### Sensors

Unterstützt werden Temperaturfühler, Energiemengen, Leistungen, PV-/Batteriewerte sowie schreib- und wählbare Sollwerte und Betriebsarten.

| Entity-ID | Beschreibung | Quelle | Einheit |
| --- | --- | --- | --- |
| `sensor.idm_aussentemperatur` | Außentemperatur | B32 | °C |
| `sensor.idm_aussentemperatur_gemittelt` | Gemittelte Außentemperatur | B32a | °C |
| `sensor.idm_wp_vorlauf` | Wärmepumpenvorlauftemperatur | B33 | °C |
| `sensor.idm_ruecklauf` | Rücklauftemperatur | B34 | °C |
| `sensor.idm_ladefuehler` | Ladefühler | B45 | °C |
| `sensor.idm_durchfluss` | Durchfluss Heizung | B2 | l/min |
| `sensor.idm_luftansaug` | Luftansaugtemperatur | B37 | °C |
| `sensor.idm_waermespeicher` | Wärmespeichertemperatur | B41 | °C |
| `sensor.idm_ww_oben` | Warmwasser oben | B43 | °C |
| `sensor.idm_ww_unten` | Warmwasser unten | B44 | °C |
| `sensor.idm_ww_zapftemp` | Warmwasser-Zapftemperatur | B46 | °C |
| `sensor.idm_hkX_vorlauf` | Heizkreis X Vorlauftemperatur | B49+ | °C |
| `sensor.idm_hkX_soll_vorlauf` | Heizkreis X Soll-Vorlauftemperatur | B49s+ | °C |
| `sensor.idm_status_warmepumpe` | Status Wärmepumpe (Bereit/Heizbetrieb) | B19 | - |
| `sensor.idm_hkX_aktive_betriebsart` | Aktive Betriebsart Heizkreis X | B55+ | - |
| `sensor.idm_wp_power` | Elektrische Gesamtleistung Wärmepumpe | 4122 | kW |
| `sensor.idm_thermische_leistung` | Thermische Momentanleistung | 1790 | kW |
| `sensor.idm_en_heizen` | Wärmemenge Heizen | 1748 | kWh |
| `sensor.idm_en_gesamt` | Wärmemenge Gesamt | 1750 | kWh |
| `sensor.idm_en_kuehlen` | Wärmemenge Kühlen | 1752 | kWh |
| `sensor.idm_en_warmwasser` | Wärmemenge Warmwasser | 1754 | kWh |
| `sensor.idm_en_abtauung` | Wärmemenge Abtauung | 1756 | kWh |
| `sensor.idm_en_passivkuehlung` | Wärmemenge Passive Kühlung | 1758 | kWh |
| `sensor.idm_en_solar` | Wärmemenge Solar | 1760 | kWh |
| `sensor.idm_en_eheizer` | Wärmemenge Elektroheizeinsatz | 1762 | kWh |

*Plus additional sensors per active sensor group (Solar, PV/Battery, Cooling, Diagnostic, Room Control, Extended Temps)*

### Switches

| Entity-ID | Beschreibung | Register |
| --- | --- | --- |
| `switch.idm_heat_request` | Heizungsanforderung | 1710 |
| `switch.idm_ww_request` | Warmwasseranforderung | 1712 |
| `switch.idm_ww_onetime` | Einmalige Warmwasserladung | 1713 |
| `switch.idm_cool_request` | Kühlanforderung (Cooling group) | 1711 |
| `switch.idm_room_temp_master` | Raumtemperatur-Übernahme Master | – |

### Numbers (per heating circuit)

| Entity-ID | Beschreibung | Register | Range | Step |
| --- | --- | --- | --- | --- |
| `number.idm_hkX_temp_normal` | Raumsolltemp Normal | 1401+i×2 | 15–30 °C | 0.5 |
| `number.idm_hkX_temp_eco` | Raumsolltemp Eco | 1415+i×2 | 10–25 °C | 0.5 |
| `number.idm_hkX_curve` | Heizkurve | 1429+i×2 | 0.1–3.5 | 0.1 |
| `number.idm_hkX_parallel` | Parallelverschiebung | 1505+i | 0–30 | 1 |
| `number.idm_hkX_heat_limit` | Heizgrenze | 1442+i | 0–50 °C | 1 |
| `number.idm_hkX_room_temp_offset` | Raumtemp. Offset (v0.7.0) | – | ±5.0 °C | 0.5 |
| `number.idm_ww_target` | WW-Solltemperatur | 1032 | 30–60 °C | 1 |
| `number.idm_ww_start` | WW-Ladung Starttemperatur | 1033 | 30–50 °C | 1 |
| `number.idm_ww_stop` | WW-Ladung Stopp-Temperatur | 1034 | 46–67 °C | 1 |

*Plus cooling numbers (cool_normal, cool_eco, cool_limit, cool_vl) when Cooling group is active*

### Selects

| Entity-ID | Beschreibung | Register |
| --- | --- | --- |
| `select.idm_betriebsart` | Betriebsart System | 1005 |
| `select.idm_hkX_betriebsart` | Betriebsart Heizkreis X | 1393+i |
| `select.idm_solar_betriebsart` | Betriebsart Solar | 1856 |

## Room Temperature Forwarding (v0.6.0+)

Forwards room temperatures from HA sensors to the heat pump (registers 1650+). The heat pump uses these values for heating curve adjustment.

### Write Interval

| Option | Description |
|--------|-------------|
| **Disabled** (default) | Sensors configured but no writing |
| On Change | Writes immediately on sensor state change |
| 5–60 Minutes | Timer-based writing |

### Master Switch

`switch.idm_room_temp_master` – Manual on/off for forwarding. OFF overrides seasonal automation.

### Seasonal Automation

Optional time period (e.g. October 1 – April 30) during which forwarding is automatically active. Daily check at midnight. Handles year-wrap correctly (e.g. Oct–Apr).

## Temperature Offset (NEW in v0.7.0)

A **temperature offset** per heating circuit can be configured. The offset is added to the sensor value **before** writing to the heat pump.

### How it works

| Offset | Example | Effect |
|--------|---------|--------|
| **-2.0°C** | Sensor: 22°C → HP receives: 20°C | HP thinks it's **colder** → heats **more** |
| **0.0°C** | Sensor: 22°C → HP receives: 22°C | No effect (default) |
| **+2.0°C** | Sensor: 22°C → HP receives: 24°C | HP thinks it's **warmer** → heats **less** |

### Parameters

* Range: -5.0 to +5.0 °C, Step: 0.5 °C, Default: 0.0 °C
* Persists across HA restarts (RestoreEntity)
* Takes effect immediately on change
* Found under Devices → iDM Wärmepumpe → Configuration

### Background

The iDM Navigator Modbus TCP protocol does not expose a register for "room influence weighting" via Modbus. The temperature offset is the solution recommended by the iDM technician: the heat pump receives a manipulated room temperature value, which influences the internal heating curve calculation.

## Hinweise

* Energiemengen (`en_*`) sind als `state_class: total_increasing` definiert.
* Sollwerte (`number.*`) werden nur bei Änderung an die Wärmepumpe geschrieben, um EEPROM-Zyklen zu schonen.
* Übersetzungen sind in `translations/de.json` und `translations/en.json` enthalten.
* Getestet mit Home Assistant 2026.2.x.

## Troubleshooting

If you encounter issues:

1. Check if the heat pump is reachable via the network
2. Verify that Modbus TCP is enabled in the Navigator controller
3. Check the Home Assistant logs for error messages
4. Try increasing the scan interval if you experience timeouts

## Changelog

### v0.7.0 (2026-02-26)

**Temperature Offset & Write Interval "Disabled"**

* **NEW:** Temperature offset per heating circuit (`number.idm_hkX_room_temp_offset`)
  * Range: ±5.0°C, step: 0.5°C
  * Added to sensor value before writing to heat pump
  * Persists across HA restarts (RestoreEntity)
  * Immediate re-write on offset change
  * Entity category: Configuration
* **NEW:** Write interval option "Disabled" as default
  * Sensors can be pre-configured without writing immediately
  * Safer default for new installations
* **FIX:** Missing season translations in `translations/de.json` and `translations/en.json`
* **Migration:** v4 → v5 (automatic)

### v0.6.0 (2026-02-26)

**Room Temperature Forwarding**

* RoomTempForwarder: External sensors → HP registers 1650+
* Master switch with manual override
* Seasonal automation (configurable, year-wrap support)
* EEPROM protection: only write on change >0.1°C
* Write modes: On change / Timer (5–60 min)
* Migration: v3 → v4

### v0.5.0

**PDF Verification & Entity Cleanup**

* Register fixes (flow sensor 1072, heating curve min 0.1)
* Automatic removal of orphaned entities
* Translation prefix: HC first for better readability
* strings.json as primary translation source

### v0.4.0

**Sensor Groups**

* 6 configurable sensor groups (~48 new registers)
* Solar, PV/Battery, Cooling, Diagnostic, Room Control, Extended Temps
* Migration: v2 → v3

### v0.3.3 and earlier

* Dynamic heating circuits A–G with `hc_reg()` mapping
* Config migrations v1 → v2
* Base sensors, numbers, selects for heating circuits

## Additional Resources

* iDM Documentation: 812663_Rev.0 - Navigator 10.0 Modbus Interface
* Home Assistant Modbus: [Official Documentation](https://www.home-assistant.io/integrations/modbus/)
* Pymodbus Library: [GitHub Repository](https://github.com/riptideio/pymodbus)

## License

MIT License
