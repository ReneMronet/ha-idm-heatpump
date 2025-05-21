"""DataUpdateCoordinator for iDM Heat Pump."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.exceptions import ConnectionException, ModbusException
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    CONF_UNIT_ID,
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_UNIT_ID,
    DEFAULT_SCAN_INTERVAL,
    REGISTER_ADDRESSES,
    DATA_TYPE_FLOAT,
    DATA_TYPE_UINT8,
    DATA_TYPE_UINT16,
    DATA_TYPE_INT16,
)

_LOGGER = logging.getLogger(__name__)


class IdmDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the iDM Heat Pump."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize."""
        self.host = entry.data[CONF_HOST]
        self.port = entry.data.get(CONF_PORT, DEFAULT_PORT)
        self.unit_id = entry.data.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)
        self.scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        self.client = ModbusTcpClient(self.host, port=self.port)
        self.client.connect()

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self.scan_interval),
        )

    def _decode_value(self, response, data_type):
        """Decode register values based on data type."""
        decoder = BinaryPayloadDecoder.fromRegisters(
            response.registers, byteorder=Endian.Big, wordorder=Endian.Little
        )

        if data_type == DATA_TYPE_FLOAT:
            return decoder.decode_32bit_float()
        elif data_type == DATA_TYPE_UINT8:
            return decoder.decode_8bit_uint()
        elif data_type == DATA_TYPE_UINT16:
            return decoder.decode_16bit_uint()
        elif data_type == DATA_TYPE_INT16:
            return decoder.decode_16bit_int()
        else:
            return None

    async def _async_update_data(self):
        """Update data via Modbus."""
        data = {}
        
        if not self.client.is_socket_open():
            try:
                await self.hass.async_add_executor_job(self.client.connect)
            except ConnectionException as exc:
                raise UpdateFailed(f"Error connecting to iDM heat pump: {exc}") from exc
        
        # Read all known register addresses
        for key, address in REGISTER_ADDRESSES.items():
            try:
                # Determine how many registers to read based on data type
                count = 2 if key in ["outdoor_temp", "avg_outdoor_temp", "heat_storage_temp", 
                                    "cold_storage_temp", "dhw_bottom_temp", "dhw_top_temp", 
                                    "dhw_tap_temp", "flow_temp", "return_temp", 
                                    "source_input_temp", "source_output_temp", 
                                    "hc_a_flow_temp", "hc_a_room_temp", "hc_a_target_flow_temp",
                                    "humidity_sensor", "power_consumption", "heating_energy",
                                    "cooling_energy", "dhw_energy", "pv_surplus", 
                                    "pv_production", "current_power_consumption"] else 1
                
                # Read the register(s)
                response = await self.hass.async_add_executor_job(
                    self.client.read_holding_registers, address, count, self.unit_id
                )
                
                if response.isError():
                    _LOGGER.warning(f"Error reading register {address}: {response}")
                    continue
                
                # Decode the value based on data type
                if count == 2:  # Float value
                    value = self._decode_value(response, DATA_TYPE_FLOAT)
                else:  # Single register value
                    value = response.registers[0]
                
                data[key] = value
                
            except (ConnectionException, ModbusException) as exc:
                _LOGGER.warning(f"Error reading register {address}: {exc}")
        
        return data

    async def async_write_register(self, address, value, data_type=None):
        """Write to a register."""
        try:
            if not self.client.is_socket_open():
                await self.hass.async_add_executor_job(self.client.connect)
            
            if data_type == DATA_TYPE_FLOAT:
                # For float values, we need to convert it to two 16-bit registers
                import struct
                payload = struct.pack(">f", value)
                registers = [int.from_bytes(payload[0:2], byteorder="big"),
                             int.from_bytes(payload[2:4], byteorder="big")]
                
                result = await self.hass.async_add_executor_job(
                    self.client.write_registers, address, registers, self.unit_id
                )
            else:
                # For other values, just write the single register
                result = await self.hass.async_add_executor_job(
                    self.client.write_register, address, value, self.unit_id
                )
            
            if result.isError():
                _LOGGER.error(f"Error writing to register {address}: {result}")
                return False
            
            # Trigger an update to read the new value
            await self.async_request_refresh()
            return True
            
        except (ConnectionException, ModbusException) as exc:
            _LOGGER.error(f"Error writing to register {address}: {exc}")
            return False

    async def async_write_coil(self, address, value):
        """Write to a coil."""
        try:
            if not self.client.is_socket_open():
                await self.hass.async_add_executor_job(self.client.connect)
            
            result = await self.hass.async_add_executor_job(
                self.client.write_coil, address, value, self.unit_id
            )
            
            if result.isError():
                _LOGGER.error(f"Error writing to coil {address}: {result}")
                return False
            
            # Trigger an update to read the new value
            await self.async_request_refresh()
            return True
            
        except (ConnectionException, ModbusException) as exc:
            _LOGGER.error(f"Error writing to coil {address}: {exc}")
            return False