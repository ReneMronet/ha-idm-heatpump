import asyncio
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
import logging

_LOGGER = logging.getLogger(__name__)

class ModbusHandler:
    def __init__(self, host, port=502, unit=1):
        self.host = host
        self.port = port
        self.unit = unit
        self._client = None

    def connect(self):
        if self._client is None:
            self._client = ModbusTcpClient(host=self.host, port=self.port)
            self._client.connect()
        return self._client

    def close(self):
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

    def read_float(self, address):
        # read 2 registers (32bit float)
        try:
            rr = self._client.read_holding_registers(address, 2, unit=self.unit)
            if not rr or rr.isError():
                return None
            decoder = BinaryPayloadDecoder.fromRegisters(rr.registers, byteorder=Endian.Big, wordorder=Endian.Big)
            return round(decoder.decode_32bit_float(), 2)
        except Exception as e:
            _LOGGER.debug("read_float error %s", e)
            return None

    def read_int(self, address):
        try:
            rr = self._client.read_holding_registers(address, 1, unit=self.unit)
            if not rr or rr.isError():
                return None
            return rr.registers[0]
        except Exception as e:
            _LOGGER.debug("read_int error %s", e)
            return None

    def write_int(self, address, value):
        try:
            rr = self._client.write_register(address, int(value), unit=self.unit)
            return not rr.isError()
        except Exception as e:
            _LOGGER.debug("write_int error %s", e)
            return False
