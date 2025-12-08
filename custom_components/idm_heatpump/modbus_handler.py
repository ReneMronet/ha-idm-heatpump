# Datei: modbus_handler.py
"""
iDM Wärmepumpe (Modbus TCP)
Version: v3.1
Stand: 2025-12-08

Änderungen gegenüber v3.0:
- read_uchar(): Fehler beim Lesen nur noch als DEBUG geloggt, um Log-Spam bei
  nicht vorhandenen Registern (z. B. 1073) zu vermeiden.

Änderungen gegenüber v2.9:
- read_float(): kein künstliches Clamping mehr (Energiezähler >1000 kWh wären sonst 0.0)
- read_float(): Kommentar zur Wortreihenfolge ergänzt
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
        _LOGGER.info(
            "iDM Modbus TCP Client für %s:%s (Unit ID %s) erstellt",
            host,
            port,
            unit_id,
        )

    async def connect(self):
        await self._client.connect()
        _LOGGER.info(
            "iDM Modbus TCP verbunden mit %s:%s (Unit %s)",
            self._host,
            self._port,
            self._unit_id,
        )

    async def close(self):
        await self._client.close()

    # ------------------------------------------------------------------
    # Lesen
    # ------------------------------------------------------------------

    async def read_float(self, address: int):
        """
        Liest einen 32-bit FLOAT-Wert (2 Register).
        iDM gibt laut Doku 32-bit Float als zwei 16-bit Register aus.
        Reihenfolge: Low-Word zuerst, dann High-Word.
        Für RO-Werte werden normalerweise Input-Register (FC4) gelesen.
        Fallback: Holding Register (FC3), falls Input nicht verfügbar ist.
        """
        try:
            rr = await self._client.read_input_registers(address=address, count=2)
            if rr is None or rr.isError():
                rr = await self._client.read_holding_registers(address=address, count=2)
            if rr is None or rr.isError():
                _LOGGER.error("Fehler beim Lesen von FLOAT Reg %s", address)
                return None

            regs = rr.registers  # Erwartet: [low_word, high_word]
            # Wandlung little-endian (Low-Word zuerst) in IEEE754 float
            raw = struct.pack("<HH", regs[0], regs[1])
            value = struct.unpack("<f", raw)[0]

            # kein künstliches Limit mehr (wichtig für kWh-Zähler >>1000)
            return round(value, 2)

        except Exception as e:
            _LOGGER.error("Exception FLOAT Reg %s: %s", address, e)
            return None

    async def read_word(self, address: int):
        """
        Liest ein 16-bit WORD (z. B. Prozentwerte oder State-of-Charge).
        Wird via Holding Register gelesen.
        """
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
        """
        Liest ein 8-bit Unsigned Integer (Low-Byte eines WORD).
        Wird via Holding Register gelesen und dann auf Low-Byte gemaskt.
        """
        try:
            rr = await self._client.read_holding_registers(address=address, count=1)
            if rr is None or rr.isError():
                # Nur Debug, da einige Register (z. B. 1073) nicht auf allen Anlagen existieren
                _LOGGER.debug("Fehler beim Lesen von UCHAR Reg %s", address)
                return None
            return rr.registers[0] & 0xFF
        except Exception as e:
            # Ebenfalls nur Debug, um kein Log-Spam zu erzeugen
            _LOGGER.debug("Exception UCHAR Reg %s: %s", address, e)
            return None

    # ------------------------------------------------------------------
    # Schreiben
    # ------------------------------------------------------------------

    async def write_float(self, address: int, value: float):
        """
        Schreibt einen 32-bit FLOAT-Wert (2 Register).
        Zerlegt den IEEE754-Float in zwei 16-bit Register (Low-Word / High-Word).
        Verwendet write_registers (entspricht FC16 / Preset Multiple Register).
        """
        try:
            raw = struct.pack("<f", float(value))
            regs = struct.unpack("<HH", raw)
            await self._client.write_registers(address=address, values=list(regs))
            _LOGGER.debug("Wrote FLOAT %.2f to Reg %s", value, address)
        except Exception as e:
            _LOGGER.error("Exception WRITE FLOAT Reg %s: %s", address, e)

    async def write_word(self, address: int, value: int):
        """
        Schreibt ein 16-bit WORD.
        """
        try:
            await self._client.write_register(address=address, value=int(value))
            _LOGGER.debug("Wrote WORD %d to Reg %s", value, address)
        except Exception as e:
            _LOGGER.error("Exception WRITE WORD Reg %s: %s", address, e)

    async def write_uchar(self, address: int, value: int):
        """
        Schreibt ein 8-bit Unsigned Integer als WORD (nur Low-Byte wird genutzt).
        """
        try:
            await self._client.write_register(address=address, value=int(value) & 0xFF)
            _LOGGER.debug("Wrote UCHAR %d to Reg %s", value, address)
        except Exception as e:
            _LOGGER.error("Exception WRITE UCHAR Reg %s: %s", address, e)
