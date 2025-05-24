# custom_components/idm_heatpump/coordinator.py
"""Data update coordinator for iDM Heat Pump."""

import logging
import struct
from datetime import timedelta
from typing import Any, Dict

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, MODBUS_REGISTERS, CONF_UNIT_ID

_LOGGER = logging.getLogger(__name__)


class IDMDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from iDM Heat Pump."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.entry = entry
        self.host = entry.data[CONF_HOST]
        self.port = entry.data[CONF_PORT]
        self.unit_id = entry.data[CONF_UNIT_ID]
        
        # Use scan interval from options if available, otherwise from data
        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL, 
            entry.data[CONF_SCAN_INTERVAL]
        )
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        
        self.client = ModbusTcpClient(
            host=self.host,
            port=self.port,
            timeout=10,
            retries=3
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via Modbus."""
        try:
            # Connect to Modbus device
            connection_successful = await self.hass.async_add_executor_job(self.client.connect)
            if not connection_successful:
                raise UpdateFailed("Could not connect to Modbus device")

            data = {}
            failed_registers = 0
            total_registers = len(MODBUS_REGISTERS)
            failed_register_names = []  # Liste der Register, die nicht gelesen werden konnten
            
            # Read all registers defined in MODBUS_REGISTERS
            for register_name, config in MODBUS_REGISTERS.items():
                try:
                    value = await self._read_register(config)
                    if value is not None:
                        data[register_name] = value
                        _LOGGER.debug("Successfully read register %s (address %s): %s", 
                                     register_name, config["address"], value)
                    else:
                        failed_registers += 1
                        failed_register_names.append(f"{register_name} (addr: {config['address']})")
                        _LOGGER.warning("Failed to read register %s (address %s): Returned None", 
                                       register_name, config["address"])
                        
                except Exception as exc:
                    failed_registers += 1
                    failed_register_names.append(f"{register_name} (addr: {config['address']})")
                    _LOGGER.warning(
                        "Failed to read register %s (address %s): %s",
                        register_name,
                        config["address"],
                        exc
                    )
                    # Continue with other registers even if one fails
                    continue

            # Close connection
            await self.hass.async_add_executor_job(self.client.close)
            
            if not data:
                raise UpdateFailed("No data received from device")
            
            # Log warning if too many registers failed
            success_rate = (total_registers - failed_registers) / total_registers
            if failed_registers > 0:
                _LOGGER.warning(
                    "Some registers failed to read: %d/%d successful (%.1f%%). Failed registers: %s",
                    total_registers - failed_registers,
                    total_registers,
                    success_rate * 100,
                    ", ".join(failed_register_names[:20]) + ("..." if len(failed_register_names) > 20 else "")
                )
            else:
                _LOGGER.debug(
                    "Successfully updated all %d registers",
                    total_registers
                )
            
            # Debug: Spezielle Status-Register loggen
            status_registers = ["smart_grid_status", "heatpump_operating_mode", "current_error_number", "heating_circuit_a_active_mode"]
            for reg_name in status_registers:
                if reg_name in data:
                    value = data[reg_name]
                    config = MODBUS_REGISTERS.get(reg_name, {})
                    options = config.get("options", {})
                    if options:
                        text_value = options.get(value, f"Unknown ({value})")
                        _LOGGER.debug(
                            "Status register %s: raw_value=%s, text_value='%s'",
                            reg_name, value, text_value
                        )
                    else:
                        _LOGGER.debug(
                            "Status register %s: value=%s (no options mapping)",
                            reg_name, value
                        )
            
            # Debug: Log some key values
            _LOGGER.debug(
                "Key values - Outdoor: %s, Supply: %s, Mode: %s, Smart Grid: %s",
                data.get('outdoor_temperature', 'N/A'),
                data.get('heatpump_supply_temperature', 'N/A'), 
                data.get('heatpump_operating_mode', 'N/A'),
                data.get('smart_grid_status', 'N/A')
            )
            
            # Log total number of available entities
            _LOGGER.info("Total available entities: %d", len(data))
            
            return data

        except Exception as exc:
            # Ensure connection is closed on error
            try:
                await self.hass.async_add_executor_job(self.client.close)
            except:
                pass
            raise UpdateFailed(f"Error communicating with device: {exc}")

    async def _read_register(self, config: Dict[str, Any]) -> Any:
        """Read a single register based on its configuration."""
        address = config["address"]
        register_type = config["type"]
        data_type = config["data_type"]
        
        try:
            # Determine how many registers to read
            register_count = 2 if data_type == "float32" else 1
            
            # Read the appropriate register type with updated API
            if register_type == "input":
                result = await self.hass.async_add_executor_job(
                    lambda: self.client.read_input_registers(
                        address=address,
                        count=register_count,
                        slave=self.unit_id
                    )
                )
            elif register_type == "holding":
                result = await self.hass.async_add_executor_job(
                    lambda: self.client.read_holding_registers(
                        address=address,
                        count=register_count,
                        slave=self.unit_id
                    )
                )
            else:
                _LOGGER.error("Unknown register type: %s", register_type)
                return None

            if result.isError():
                _LOGGER.warning("Modbus error reading address %s: %s", address, result)
                return None

            # Convert register values to proper data type
            return self._convert_register_value(result.registers, data_type, config.get("swap"))

        except ModbusException as exc:
            _LOGGER.warning("Modbus exception reading address %s: %s", address, exc)
            return None
        except Exception as exc:
            _LOGGER.error("Unexpected error reading address %s: %s", address, exc)
            return None

    def _convert_register_value(self, registers, data_type: str, swap: str = None) -> Any:
        """Convert raw register values to the appropriate data type."""
        try:
            if data_type == "uint16":
                return registers[0]
            
            elif data_type == "int16":
                # Convert unsigned to signed
                value = registers[0]
                return value if value < 32768 else value - 65536
            
            elif data_type == "float32":
                if len(registers) < 2:
                    _LOGGER.error("Not enough registers for float32")
                    return None
                
                # Handle word swapping for float32
                if swap == "word":
                    # iDM uses word-swapped floats: [low_word, high_word]
                    high_word = registers[1]
                    low_word = registers[0]
                    _LOGGER.debug("Word-swapped float: [%s, %s]", low_word, high_word)
                else:
                    # Standard order: [high_word, low_word]
                    high_word = registers[0]
                    low_word = registers[1]
                    _LOGGER.debug("Standard float: [%s, %s]", high_word, low_word)
                
                # Pack as big-endian 32-bit float
                packed = struct.pack('>HH', high_word, low_word)
                value = struct.unpack('>f', packed)[0]
                _LOGGER.debug("Converted float value: %s", value)
                return value
            
            else:
                _LOGGER.error("Unknown data type: %s", data_type)
                return None
                
        except (struct.error, IndexError) as exc:
            _LOGGER.error("Error converting register value: %s", exc)
            return None

    async def async_write_register(self, register_name: str, value: Any) -> bool:
        """Write a value to a holding register."""
        if register_name not in MODBUS_REGISTERS:
            _LOGGER.error("Unknown register: %s", register_name)
            return False
        
        config = MODBUS_REGISTERS[register_name]
        
        if config["type"] != "holding":
            _LOGGER.error("Register %s is not writable", register_name)
            return False
        
        try:
            connection_successful = await self.hass.async_add_executor_job(self.client.connect)
            if not connection_successful:
                _LOGGER.error("Could not connect to write register")
                return False
            
            address = config["address"]
            data_type = config["data_type"]
            
            # Convert value to register format
            if data_type == "uint16":
                result = await self.hass.async_add_executor_job(
                    lambda: self.client.write_register(
                        address=address,
                        value=int(value),
                        slave=self.unit_id
                    )
                )
            elif data_type == "float32":
                # Convert float to two registers with word swap
                packed = struct.pack('>f', float(value))
                high_word, low_word = struct.unpack('>HH', packed)
                
                # Write with word swap for iDM
                if config.get("swap") == "word":
                    registers = [low_word, high_word]
                else:
                    registers = [high_word, low_word]
                
                result = await self.hass.async_add_executor_job(
                    lambda: self.client.write_registers(
                        address=address,
                        values=registers,
                        slave=self.unit_id
                    )
                )
            else:
                _LOGGER.error("Unsupported data type for writing: %s", data_type)
                return False
            
            # Close connection
            await self.hass.async_add_executor_job(self.client.close)
            
            if result.isError():
                _LOGGER.error("Error writing register %s: %s", register_name, result)
                return False
            
            # Trigger an immediate update to reflect the change
            await self.async_request_refresh()
            return True
            
        except Exception as exc:
            # Ensure connection is closed on error
            try:
                await self.hass.async_add_executor_job(self.client.close)
            except:
                pass
            _LOGGER.error("Exception writing register %s: %s", register_name, exc)
            return False