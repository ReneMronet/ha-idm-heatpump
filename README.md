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

## iDM Navigator 2.0 Mock Server

Overview
The iDM Navigator 2.0 Mock Server simulates a real iDM heat pump for development and testing purposes. It implements the authentic Modbus TCP register layout based on the official iDM documentation (812170_Rev.7).
Installation
Prerequisites
bash# Python 3.8+ required
pip install pymodbus asyncio
Starting the Mock Server

Download the file:
bashwget https://raw.githubusercontent.com/ReneMronet/idm-heatpump-hacs/main/idm_modbus_mock.py
# or copy the file directly from this repository

Start the server:
bashpython3 idm_modbus_mock.py

Server output:
╔══════════════════════════════════════════════════════════════════════════╗
║                           iDM Navigator 2.0                              ║
║                       Heat Pump Mock Server                              ║
║                                                                          ║
║  Authentic iDM Modbus TCP Implementation based on 812170_Rev.7           ║
║  Features: Real Register Map | Authentic Values | PV Integration         ║
║           Multi-Zone Support | Smart Grid | Energy Monitoring            ║
╚══════════════════════════════════════════════════════════════════════════╝

iDM Navigator 2.0 Heat Pump Modbus TCP Mock Server
================================================================================
Navigator Version: 20.15-0
System ID: IDM-NAV2-MOCK
Server IP: 192.168.1.100:502
Modbus Unit ID: 1
Based on: 812170_Rev.7 - iDM Official Documentation


Testing the Mock Server
Using the Test Script
bash# Run test script
python3 test_idm_mock.py

# With specific IP address
python3 test_idm_mock.py 192.168.1.100
Manual Testing with Modbus Tools
bash# Install pymodbus console
pip install pymodbus[repl]

# Start Modbus console
pymodbus.console tcp --host 192.168.1.100 --port 502

# Example commands in console:
client.read_input_registers address=0 count=2 unit=1     # Outdoor temperature
client.read_input_registers address=6 count=1 unit=1     # Smart Grid status
client.read_input_registers address=90 count=1 unit=1    # Heat pump operating mode
Home Assistant Integration
Automatic Configuration

Add integration:

Settings → Devices & Services → Add Integration
Search for "iDM Navigator 2.0 Heat Pump"


Configuration:
Host IP Address: 192.168.1.100  (IP of mock server)
Port: 502
Modbus Unit ID: 1
Scan Interval: 30 seconds


Manual YAML Configuration (optional)
yaml# configuration.yaml
modbus:
  - name: idm_navigator2_mock
    type: tcp
    host: 192.168.1.100
    port: 502
    sensors:
      - name: "iDM Mock Outdoor Temperature"
        address: 0
        input_type: input
        data_type: float32
        swap: word
        unit_of_measurement: "°C"
        device_class: temperature
        
      - name: "iDM Mock Smart Grid Status"
        address: 6
        input_type: input
        data_type: uint16
        
      - name: "iDM Mock Heat Pump Operating Mode"
        address: 90
        input_type: input
        data_type: uint16
Simulated Features
Realistic Values

Outdoor temperature: Varies between -10°C and +5°C (24h cycle)
Compressor: Cyclic operation (4 min on, 1 min off)
Temperatures: React to compressor status
PV integration: Simulates sun hours (10-16 o'clock)
Smart Grid: Automatic status changes based on PV production

Supported Registers

Input Registers (30001+): Temperatures, status, energy values
Holding Registers (40001+): Setpoints, operating modes, external values
All important iDM registers: According to official documentation

Operating Mode Simulation
System SYSMODE: 0=Standby, 1=Auto, 2=Away, 4=DHW only, 5=Heating only
Heat Pump: 0=Off, 1=Heating, 2=Cooling, 4=DHW, 8=Defrost
Heating Circuit: 0=Off, 1=Schedule, 2=Normal, 3=Eco, 4=Manual Heat, 5=Manual Cool
Smart Grid: 0=Utility Lock+No PV, 1=Utility Power+No PV, 2=No Utility+PV Production, 4=Utility Lock+PV
Development & Debugging
Increase Log Level
bash# Mock server with debug output
python3 idm_modbus_mock.py --log-level DEBUG
Adding Custom Registers
python# In idm_modbus_mock.py - extend register_values dictionary
self.register_values = {
    # Existing registers...
    1500: 25.0,  # New custom register
}

# Add to register_map
input_register_map = {
    # Existing mappings...
    500: 1500,  # 30501: Custom register
}
Performance Monitoring

Update interval: 5 seconds (configurable)
Register count: ~80 simulated registers
Memory usage: ~50MB
CPU usage: Minimal (<1%)

Troubleshooting
Common Issues

Port already in use:
bash# Use different port
# Change in idm_modbus_mock.py: self.tcp_port = 5020

Firewall blocking:
bash# Ubuntu/Debian
sudo ufw allow 502

# Windows
# Windows Defender Firewall → Allow port 502

IP address not reachable:
bash# Check server IP
python3 -c "import socket; print(socket.gethostbyname(socket.gethostname()))"


Testing Connection
bash# Telnet test
telnet 192.168.1.100 502

# Ping test
ping 192.168.1.100

# Modbus-specific test
python3 test_idm_mock.py 192.168.1.100
Production Environment
⚠️ Important: The mock server is only intended for development and testing!
For production environments:

Use the real iDM Navigator 2.0 hardware
Configure the real IP address of the heat pump
Check network security and firewall rules

Additional Resources

iDM Documentation: 812170_Rev.7 - Navigator 2.0 Modbus Interface
Home Assistant Modbus: Official Documentation (https://www.home-assistant.io/integrations/modbus/)
Pymodbus Library: GitHub Repository (https://github.com/riptideio/pymodbus)



