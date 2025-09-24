# Datei: modbus_handler.py
"""
iDM Wärmepumpe (Modbus TCP)
Version: v2.9 (Dokumentations-Update)
Stand: 2025-09-24
"""

import logging
import struct
from pymodbus.client import AsyncModbusTcpClient
from .const import DEFAULT_PORT, DEFAULT_UNIT_ID

_LOGGER = logging.getLogger(__name__)


class IDMModbusHandler:
    def __init__(self, host: str, port: int = DEFAULT_PORT, unit_id: int = DEFAULT_UNIT_ID):
        self._host = host
        self._port = port
        self._unit_id = unit_id
        self._client = AsyncModbusTcpClient(host, port=port)
        _LOGGER.info("iDM Modbus TCP Client für %s:%s (Unit ID %s) erstellt", host, port, unit_id)

    async def connect(self):
        await self._client.connect()
        _LOGGER.info("iDM Modbus TCP verbunden mit %s:%s (Unit %s)", self._host, self._port, self._unit_id)

    async def close(self):
        await self._client.close()

    # ------------------------------------------------------------------
    # Lesen
    # ------------------------------------------------------------------

    async def read_float(self, address: int):
        """Liest einen 32-bit FLOAT-Wert (bestehend aus 2 Registern)."""
        try:
            rr = await self._client.read_input_registers(address=address, count=2)
            if rr is None or rr.isError():
                rr = await self._client.read_holding_registers(address=address, count=2)
            if rr is None or rr.isError():
                _LOGGER.error("Fehler beim Lesen von FLOAT Reg %s", address)
                return None
            regs = rr.registers
            raw = struct.pack("<HH", regs[0], regs[1])
            value = struct.unpack("<f", raw)[0]
            return round(value, 2) if -1000 < value < 1000 else 0.0
        except Exception as e:
            _LOGGER.error("Exception FLOAT Reg %s: %s", address, e)
            return None

    async def read_word(self, address: int):
        """Liest ein 16-bit WORD (z. B. Prozentwerte)."""
        try:
            rr = await self._client.read_holding_registers(address=address, count=1)
            if rr is None or rr.isError():
                _LOGGER.error("Fehler beim Lesen von WORD Reg %s", address)
                return None
            return rr.registers[0]
        except Exception as e:
            _LOGGER.error("Exception WORD Reg %s: %s", address, e)
            return None

    async def read_uchar(self, address: int):
        """Liest ein 8-bit Unsigned Integer (Low-Byte eines WORD)."""
        try:
            rr = await self._client.read_holding_registers(address=address, count=1)
            if rr is None or rr.isError():
                _LOGGER.error("Fehler beim Lesen von UCHAR Reg %s", address)
                return None
            return rr.registers[0] & 0xFF
        except Exception as e:
            _LOGGER.error("Exception UCHAR Reg %s: %s", address, e)
            return None

    # ------------------------------------------------------------------
    # Schreiben
    # ------------------------------------------------------------------

    async def write_float(self, address: int, value: float):
        """Schreibt einen 32-bit FLOAT-Wert (2 Register)."""
        try:
            raw = struct.pack("<f", float(value))
            regs = struct.unpack("<HH", raw)
            await self._client.write_registers(address=address, values=list(regs))
            _LOGGER.debug("Wrote FLOAT %.2f to Reg %s", value, address)
        except Exception as e:
            _LOGGER.error("Exception WRITE FLOAT Reg %s: %s", address, e)

    async def write_word(self, address: int, value: int):
        """Schreibt ein 16-bit WORD."""
        try:
            await self._client.write_register(address=address, value=int(value))
            _LOGGER.debug("Wrote WORD %d to Reg %s", value, address)
        except Exception as e:
            _LOGGER.error("Exception WRITE WORD Reg %s: %s", address, e)

    async def write_uchar(self, address: int, value: int):
        """Schreibt ein 8-bit Unsigned Integer (als WORD)."""
        try:
            await self._client.write_register(address=address, value=int(value) & 0xFF)
            _LOGGER.debug("Wrote UCHAR %d to Reg %s", value, address)
        except Exception as e:
            _LOGGER.error("Exception WRITE UCHAR Reg %s: %s", address, e)
