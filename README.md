# iDM Heat Pump Integration for Home Assistant

This integration allows you to monitor and control your iDM heat pump with Navigator 2.0 controller in Home Assistant via Modbus TCP.

## Features

- Read sensor values (temperatures, humidity, energy counters)
- Control system and heating circuit operation modes
- Set temperature setpoints
- Monitor system status and error codes
- Request heating, cooling and hot water
- PV surplus integration

## Requirements

- iDM heat pump with Navigator 2.0 controller
- Modbus TCP enabled on the Navigator controller
- The heat pump must be accessible on your network

## Installation

### HACS (recommended)

1. Open HACS in your Home Assistant instance
2. Go to Integrations
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add the URL of this repository and select "Integration" as category
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
- Temperatures (outdoor, heat storage, DHW, flow/return, etc.)
- Power and energy values
- Status information
- Humidity

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