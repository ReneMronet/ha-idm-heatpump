"""
modbus_handler.py – v2.5 (2025-09-17)

Funktionen für die Kommunikation mit der iDM Wärmepumpe über Modbus TCP.
- Unterstützt: FLOAT (32-bit, Little Endian), WORD (16-bit), UCHAR (Low-Byte)
- Nutzt pymodbus AsyncModbusTcpClient
"""

import logging
import struct
from pymodbus.client import AsyncModbusTcpClient
from .const import DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)


class IDMModbusHandler:
    """
    Kapselt die Modbus-Kommunikation.
    Bietet Methoden zum Lesen von FLOAT, WORD und UCHAR-Registern.
    """

    def __init__(self, host: str, port: int = DEFAULT_PORT):
        """
        Initialisiert den Modbus-Handler.
        :param host: IP-Adresse der Wärmepumpe
        :param port: TCP-Port (Standard: 502)
        """
        self._host = host
        self._port = port
        self._client = AsyncModbusTcpClient(host, port=port)
        _LOGGER.info("iDM Modbus TCP Client für %s:%s erstellt", host, port)

    async def connect(self):
        """Verbindet den Modbus-Client mit der Wärmepumpe."""
        await self._client.connect()
        _LOGGER.info("iDM Modbus TCP verbunden mit %s:%s", self._host, self._port)

    async def close(self):
        """Schließt die Modbus-Verbindung."""
        await self._client.close()

    async def read_float(self, address: int):
        """
        Liest einen 32-bit FLOAT-Wert (bestehend aus 2 Registern).
        Versucht zuerst Input Register, bei Fehlern Holding Register.
        Rückgabe: float oder None
        """
        try:
            rr = await self._client.read_input_registers(address=address, count=2)
            if rr is None or rr.isError():
                rr = await self._client.read_holding_registers(address=address, count=2)

            if rr is None or rr.isError():
                _LOGGER.error("Fehler beim Lesen von FLOAT Register %s", address)
                return None

            regs = rr.registers
            try:
                # Little Endian (Reg_L zuerst, dann Reg_H)
                raw = struct.pack("<HH", regs[0], regs[1])
                value = struct.unpack("<f", raw)[0]
                if -1000 < value < 1000:   # Plausibilitätsprüfung
                    return round(value, 2)
                else:
                    _LOGGER.warning("Unplausibler Wert bei FLOAT Reg %s: %s", address, value)
                    return 0.0
            except Exception as e:
                _LOGGER.error("Decode-Fehler FLOAT Reg %s: %s", address, e)
                return None

        except Exception as e:
            _LOGGER.error("Exception beim Lesen von FLOAT Register %s: %s", address, e)
            return None

    async def read_word(self, address: int):
        """
        Liest ein 16-bit WORD (z. B. Prozentwerte).
        Rückgabe: int oder None
        """
        try:
            rr = await self._client.read_holding_registers(address=address, count=1)
            if rr is None or rr.isError():
                _LOGGER.error("Fehler beim Lesen von WORD Register %s", address)
                return None
            return rr.registers[0]
        except Exception as e:
            _LOGGER.error("Exception beim Lesen von WORD Register %s: %s", address, e)
            return None

    async def read_uchar(self, address: int):
        """
        Liest ein 8-bit Unsigned Integer (Low-Byte eines WORD).
        Rückgabe: int oder None
        """
        try:
            rr = await self._client.read_holding_registers(address=address, count=1)
            if rr is None or rr.isError():
                _LOGGER.error("Fehler beim Lesen von UCHAR Register %s", address)
                return None
            return rr.registers[0] & 0xFF
        except Exception as e:
            _LOGGER.error("Exception beim Lesen von UCHAR Register %s: %s", address, e)
            return None
