# iDM Heat Pump Integration for Home Assistant

This integration allows you to monitor and control your iDM heat pump with Navigator 10.0 controller in Home Assistant via Modbus TCP.

## Features

- **Single shared Modbus connection** with automatic reconnect
- **DataUpdateCoordinator** – all registers read once per cycle for optimal performance
- **7 heating circuits** (A–G) – dynamically configurable
- **6 sensor groups** – enable only what your system has
- **Auto-detection** of missing sensors (automatically marked unavailable)
- **Diagnostic entities** disabled by default (enable in UI when needed)
- Full German and English translations

## Requirements

- iDM heat pump with Navigator 10.0 controller
- Modbus TCP enabled on the Navigator controller
- The heat pump must be accessible on your network

## Installation

### HACS (recommended)

1. Open HACS in your Home Assistant instance
2. Go to Integrations
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add the URL of this repository and select "Integration" as category:
   `https://github.com/ReneMronet/ha-idm-heatpump/`
5. Click "Add"
6. Search for "iDM Heat Pump" and install it
7. Restart Home Assistant

### Manual Installation

1. Download the latest release from GitHub
2. Extract the content to the `custom_components/idm_heatpump` folder in your Home Assistant configuration directory
3. Restart Home Assistant

## Configuration

### Step 1: Connection

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "iDM Wärmepumpe"
4. Enter the connection details:
   - **IP Address**: The IP address of your heat pump
   - **TCP Port**: The Modbus TCP port (default: 502)
   - **Unit ID**: The Modbus Unit ID (default: 1)
   - **Update Interval**: How often to poll registers in seconds (default: 30)

### Step 2: Heating Circuits & Sensor Groups

Select your active heating circuits (A–G) and the sensor groups matching your system:

| Sensor Group | Description |
|---|---|
| ☀️ **Solar** | Collector, return & charge temperature, solar power, operating mode |
| 🔋 **PV / Battery** | PV surplus, production, house consumption, battery, SmartGrid, electricity price, PV target |
| ❄️ **Cooling** | Cooling request, cooling setpoints per heating circuit (normal, eco, limit, supply) |
| 🔧 **Diagnostics** | Compressor, utility lock, charge pump, changeover valve, circulation pump, power limit |
| 🌡️ **Room Control** | Room temperature per heating circuit, humidity sensor |
| 📊 **Extended Temperatures** | Heat sink supply/return, air heat exchanger, cold storage |

Default groups: **Solar** and **PV / Battery**. You can change these anytime in the integration options.

## Prepare your iDM Heat Pump

Before using this integration, you need to enable Modbus TCP on your Navigator 10.0 controller:

1. On the Navigator controller, go to "Settings" → "Building Management"
2. Set "Modbus TCP" to "On"
3. For using external temperature and humidity values from Home Assistant:
   - Set "BMS Outdoor Temperature" to "Yes"
   - Set "BMS Humidity Value" to "Yes"
4. Go to "General Settings" → "Network Settings"
5. Set a static IP address for the heat pump (recommended)

## Available Entities

### Base Sensors (always active)

| Entity | Description | Register | Unit |
|---|---|---|---|
| `sensor.idm_aussentemperatur` | Outdoor temperature | 1000 (B32) | °C |
| `sensor.idm_aussentemperatur_gemittelt` | Average outdoor temperature | 1002 (B32a) | °C |
| `sensor.idm_wp_vorlauf` | Heat pump supply temperature | 1050 (B33) | °C |
| `sensor.idm_ruecklauf` | Return temperature | 1052 (B34) | °C |
| `sensor.idm_ladefuehler` | Charge sensor | 1066 (B45) | °C |
| `sensor.idm_durchfluss` | Flow rate heating | 1073 (B2) | l/min |
| `sensor.idm_luftansaug` | Air inlet temperature | 1060 (B37) | °C |
| `sensor.idm_luftansaug_2` | Air inlet temperature 2 | 1064 | °C |
| `sensor.idm_waermespeicher` | Heat buffer temperature | 1008 (B41) | °C |
| `sensor.idm_ww_oben` | Hot water top | 1014 (B43) | °C |
| `sensor.idm_ww_unten` | Hot water bottom | 1012 (B44) | °C |
| `sensor.idm_ww_zapftemp` | Hot water tap temperature | 1030 (B46) | °C |
| `sensor.idm_betriebsart_warmepumpe` | Heat pump operating mode | 1090 | – |
| `sensor.idm_status_warmepumpe` | Heat pump status | 1091 | – |
| `sensor.idm_interne_meldung` | Internal message code | 1004 | – |
| `sensor.idm_wp_power` | Heat pump electric power | 4122 | kW |
| `sensor.idm_thermische_leistung` | Thermal power | 1790 | kW |
| `sensor.idm_en_heizen` | Energy heating | 1748 | kWh |
| `sensor.idm_en_gesamt` | Energy total | 1750 | kWh |
| `sensor.idm_en_kuehlen` | Energy cooling | 1752 | kWh |
| `sensor.idm_en_warmwasser` | Energy hot water | 1754 | kWh |
| `sensor.idm_en_abtauung` | Energy defrost | 1756 | kWh |
| `sensor.idm_en_passivkuehlung` | Energy passive cooling | 1758 | kWh |
| `sensor.idm_en_solar` | Energy solar | 1760 | kWh |
| `sensor.idm_en_eheizer` | Energy electric heater | 1762 | kWh |

### Dynamic Heating Circuit Sensors (per active HC, always active)

For each active heating circuit (A–G), the following sensors are created:

| Entity Pattern | Description | Unit |
|---|---|---|
| `sensor.idm_hk{x}_vorlauftemperatur` | Supply temperature | °C |
| `sensor.idm_hk{x}_soll_vorlauf` | Target supply temperature | °C |
| `sensor.idm_hk{x}_aktive_betriebsart` | Active operating mode | – |

### ☀️ Solar Group

| Entity | Description | Register | Unit |
|---|---|---|---|
| `sensor.idm_solar_kollektor` | Solar collector temperature | 1850 (B73) | °C |
| `sensor.idm_solar_ruecklauf` | Solar collector return temperature | 1852 (B75) | °C |
| `sensor.idm_solar_ladetemp` | Solar charge temperature | 1854 (B74) | °C |
| `sensor.idm_solar_leistung` | Solar power | 1792 | kW |
| `select.idm_solar_betriebsart` | Solar operating mode | 1856 | – |

### 🔋 PV / Battery Group

| Entity | Description | Register | Unit |
|---|---|---|---|
| `sensor.idm_pv_ueberschuss` | PV surplus | 74 | kW |
| `sensor.idm_e_heizstab` | Electric heater power | 76 | kW |
| `sensor.idm_pv_produktion` | PV production | 78 | kW |
| `sensor.idm_hausverbrauch` | House consumption | 82 | kW |
| `sensor.idm_batterie_entladung` | Battery discharge | 84 | kW |
| `sensor.idm_batterie_fuellstand` | Battery state of charge | 86 | % |
| `sensor.idm_smartgrid_status` | SmartGrid status | 90 | – |
| `sensor.idm_strompreis` | Current electricity price | 1048 | ct/kWh |
| `number.idm_pv_zielwert` | PV target value | 88 | kW |

### ❄️ Cooling Group

| Entity | Description | Register | Unit |
|---|---|---|---|
| `sensor.idm_kuehlanforderung_wp` | Cooling request heat pump | 1092 | – |
| `sensor.idm_ww_anforderung_wp` | Hot water request heat pump | 1093 | – |
| `switch.idm_cool_request` | Cooling request switch | 1711 | – |

Per active heating circuit:

| Entity Pattern | Description | Unit |
|---|---|---|
| `number.idm_hk{x}_cool_normal` | Cooling target normal | °C |
| `number.idm_hk{x}_cool_eco` | Cooling target eco | °C |
| `number.idm_hk{x}_cool_limit` | Cooling limit | °C |
| `number.idm_hk{x}_cool_vl` | Cooling supply target | °C |

### 🔧 Diagnostics Group (disabled by default)

| Entity | Description | Register | Unit |
|---|---|---|---|
| `sensor.idm_summenstoerung` | Fault summary | 1099 | – |
| `sensor.idm_evu_sperre` | Utility lock contact | 1098 | – |
| `sensor.idm_verdichter_1` | Compressor 1 | 1100 | – |
| `sensor.idm_ladepumpe` | Charge pump | 1104 | % |
| `sensor.idm_variabler_eingang` | Variable input | 1006 | – |
| `sensor.idm_umschaltventil` | Changeover valve heat/cool | 1110 | % |
| `sensor.idm_zirkulationspumpe` | Circulation pump | 1118 | % |
| `number.idm_leistungsbegrenzung` | Power limit | 4108 | kW |

> **Note:** Diagnostic entities are disabled by default. Enable them in the HA entity settings if needed.

### 🌡️ Room Control Group (auto-detection)

| Entity Pattern | Description | Unit |
|---|---|---|
| `sensor.idm_hk{x}_raumtemperatur` | Room temperature per HC | °C |
| `sensor.idm_feuchtesensor` | Humidity sensor (B31) | % |

> **Note:** These sensors use auto-detection. If a sensor is not installed, it will automatically be marked as "Unavailable" after 3 consecutive invalid readings.

### 📊 Extended Temperatures Group (auto-detection)

| Entity | Description | Register | Unit |
|---|---|---|---|
| `sensor.idm_luftwaermetauscher` | Air heat exchanger (B72) | 1062 | °C |
| `sensor.idm_waermesenke_ruecklauf` | Heat sink return (B124) | 1068 | °C |
| `sensor.idm_waermesenke_vorlauf` | Heat sink supply (B125) | 1070 | °C |
| `sensor.idm_kaeltespeicher` | Cold storage (B40) | 1010 | °C |

### Base Switches

| Entity | Description | Register |
|---|---|---|
| `switch.idm_heat_request` | Heating request | 1710 |
| `switch.idm_ww_request` | Hot water request | 1712 |
| `switch.idm_ww_onetime` | One-time hot water charge | 1713 |

### Base Numbers (per active HC)

| Entity Pattern | Description | Range | Unit |
|---|---|---|---|
| `number.idm_hk{x}_temp_normal` | Target temperature normal | 15–30 | °C |
| `number.idm_hk{x}_temp_eco` | Target temperature eco | 10–25 | °C |
| `number.idm_hk{x}_curve` | Heating curve | 0.0–3.5 | – |
| `number.idm_hk{x}_parallel` | Parallel shift | 0–30 | °C |
| `number.idm_hk{x}_heat_limit` | Heating limit | 0–50 | °C |
| `number.idm_ww_target` | Hot water target temperature | 30–60 | °C |
| `number.idm_ww_start` | Hot water charge start | 30–50 | °C |
| `number.idm_ww_stop` | Hot water charge stop | 46–67 | °C |

### Base Selects (per active HC)

| Entity Pattern | Description | Register |
|---|---|---|
| `select.idm_betriebsart` | System operating mode | 1005 |
| `select.idm_hk{x}_betriebsart` | HC operating mode | 1393+ |

## Architecture

```
┌─────────────────────────────────────────┐
│            __init__.py                  │
│  ┌─────────────┐  ┌──────────────────┐  │
│  │ IDMModbus   │  │ DataUpdate       │  │
│  │ Handler     │──│ Coordinator      │  │
│  │ (1 TCP conn)│  │ (reads all regs) │  │
│  └─────────────┘  └──────┬───────────┘  │
└──────────────────────────┼──────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────┴──────┐  ┌─────┴──────┐  ┌─────┴──────┐
   │  sensor.py  │  │ number.py  │  │ select.py  │
   │  switch.py  │  │            │  │            │
   │ (read from  │  │ (read from │  │ (read from │
   │ coordinator)│  │ coord,     │  │ coord,     │
   │             │  │ write via  │  │ write via  │
   │             │  │ client)    │  │ client)    │
   └─────────────┘  └────────────┘  └────────────┘
```

## Notes

- Energy entities (`en_*`) use `state_class: total_increasing` for proper energy tracking
- Write operations (numbers, selects, switches) trigger an immediate coordinator refresh
- The internal message sensor fires `idm_internal_message_changed` events and creates persistent notifications on code changes
- Config version 3 with automatic migration from v1 and v2
- Tested with Home Assistant 2026.2

## Troubleshooting

If you encounter issues:

1. Check if the heat pump is reachable via the network
2. Verify that Modbus TCP is enabled in the Navigator controller
3. Check the Home Assistant logs for error messages (look for `iDM` prefix)
4. Try increasing the update interval if you experience timeouts
5. Check the logs for `iDM Coordinator: XX Register` to verify register count

## Additional Resources

- iDM Documentation: 812663_Rev.0 – Navigator 10.0 Modbus Interface
- [Home Assistant Modbus Documentation](https://www.home-assistant.io/integrations/modbus/)
- [PyModbus Library](https://github.com/riptideio/pymodbus)
