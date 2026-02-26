"""
iDM Wärmepumpe (Modbus TCP)
Version: v4.0
Stand: 2026-02-26

Änderungen v4.0 (Refactoring Schritt 1):
- Neue Methode read_all(): Liest alle Register aus einer Map in einem Durchlauf
- ensure_connected(): Automatische Reconnection bei Verbindungsverlust
- is_connected Property
- Bestehende Einzelmethoden (read_float, read_uchar, etc.) bleiben erhalten
"""

import logging
import struct
from pymodbus.client import AsyncModbusTcpClient
from .const import DEFAULT_PORT, DEFAULT_UNIT_ID, REG_TYPE_FLOAT, REG_TYPE_UCHAR, REG_TYPE_WORD

_LOGGER = logging.getLogger(__name__)


class IDMModbusHandler:
    def __init__(self, host: str, port: int = DEFAULT_PORT, unit_id: int = DEFAULT_UNIT_ID):
        self._host = host
        self._port = port
        self._unit_id = unit_id
        self._client = AsyncModbusTcpClient(host, port=port)
        _LOGGER.info(
            "iDM Modbus TCP Client für %s:%s (Unit ID %s) erstellt",
            host, port, unit_id,
        )

    @property
    def is_connected(self) -> bool:
        return self._client.connected

    async def connect(self):
        await self._client.connect()
        _LOGGER.info(
            "iDM Modbus TCP verbunden mit %s:%s (Unit %s)",
            self._host, self._port, self._unit_id,
        )

    async def ensure_connected(self):
        """Stellt die Verbindung her, falls nicht verbunden."""
        if not self._client.connected:
            _LOGGER.info("iDM Modbus: Verbindung verloren, versuche Reconnect...")
            try:
                await self._client.connect()
                _LOGGER.info("iDM Modbus: Reconnect erfolgreich")
            except Exception as e:
                _LOGGER.error("iDM Modbus: Reconnect fehlgeschlagen: %s", e)
                raise

    async def close(self):
        self._client.close()

    # ------------------------------------------------------------------
    # Batch-Lesen (für DataUpdateCoordinator)
    # ------------------------------------------------------------------

    async def read_all(self, register_map: dict[int, str]) -> dict[int, any]:
        """Liest alle Register aus der Map und gibt {adresse: wert} zurück.

        Fehlgeschlagene Reads werden als None eingetragen, aber stoppen
        nicht den Rest. So bleiben einzelne defekte/nicht vorhandene
        Register toleriert.
        """
        await self.ensure_connected()
        data = {}
        for address, reg_type in register_map.items():
            try:
                if reg_type == REG_TYPE_FLOAT:
                    data[address] = await self._read_float_raw(address)
                elif reg_type == REG_TYPE_UCHAR:
                    data[address] = await self._read_uchar_raw(address)
                elif reg_type == REG_TYPE_WORD:
                    data[address] = await self._read_word_raw(address)
                else:
                    _LOGGER.warning("Unbekannter Register-Typ %s für Adresse %s", reg_type, address)
                    data[address] = None
            except Exception as e:
                _LOGGER.debug("Fehler beim Lesen von Register %s (%s): %s", address, reg_type, e)
                data[address] = None
        return data

    # ------------------------------------------------------------------
    # Interne Read-Methoden (ohne Exception-Fang, für read_all)
    # ------------------------------------------------------------------

    async def _read_float_raw(self, address: int):
        """Liest einen 32-bit FLOAT. Gibt None bei Fehler zurück."""
        rr = await self._client.read_input_registers(address=address, count=2)
        if rr is None or rr.isError():
            rr = await self._client.read_holding_registers(address=address, count=2)
        if rr is None or rr.isError():
            return None
        raw = struct.pack("<HH", rr.registers[0], rr.registers[1])
        return round(struct.unpack("<f", raw)[0], 2)

    async def _read_uchar_raw(self, address: int):
        """Liest ein 8-bit UCHAR. Gibt None bei Fehler zurück."""
        rr = await self._client.read_holding_registers(address=address, count=1)
        if rr is None or rr.isError():
            return None
        return rr.registers[0] & 0xFF

    async def _read_word_raw(self, address: int):
        """Liest ein 16-bit WORD. Gibt None bei Fehler zurück."""
        rr = await self._client.read_holding_registers(address=address, count=1)
        if rr is None or rr.isError():
            return None
        return rr.registers[0]

    # ------------------------------------------------------------------
    # Öffentliche Einzelmethoden (Kompatibilität + Schreibzugriffe)
    # ------------------------------------------------------------------

    async def read_float(self, address: int):
        """Liest einen 32-bit FLOAT-Wert (2 Register)."""
        try:
            await self.ensure_connected()
            return await self._read_float_raw(address)
        except Exception as e:
            _LOGGER.error("Exception FLOAT Reg %s: %s", address, e)
            return None

    async def read_word(self, address: int):
        """Liest ein 16-bit WORD."""
        try:
            await self.ensure_connected()
            return await self._read_word_raw(address)
        except Exception as e:
            _LOGGER.error("Exception WORD Reg %s: %s", address, e)
            return None

    async def read_uchar(self, address: int):
        """Liest ein 8-bit Unsigned Integer (Low-Byte eines WORD)."""
        try:
            await self.ensure_connected()
            return await self._read_uchar_raw(address)
        except Exception as e:
            _LOGGER.debug("Exception UCHAR Reg %s: %s", address, e)
            return None

    # ------------------------------------------------------------------
    # Schreiben
    # ------------------------------------------------------------------

    async def write_float(self, address: int, value: float):
        """Schreibt einen 32-bit FLOAT-Wert (2 Register)."""
        try:
            await self.ensure_connected()
            raw = struct.pack("<f", float(value))
            regs = struct.unpack("<HH", raw)
            await self._client.write_registers(address=address, values=list(regs))
            _LOGGER.debug("Wrote FLOAT %.2f to Reg %s", value, address)
        except Exception as e:
            _LOGGER.error("Exception WRITE FLOAT Reg %s: %s", address, e)

    async def write_word(self, address: int, value: int):
        """Schreibt ein 16-bit WORD."""
        try:
            await self.ensure_connected()
            await self._client.write_register(address=address, value=int(value))
            _LOGGER.debug("Wrote WORD %d to Reg %s", value, address)
        except Exception as e:
            _LOGGER.error("Exception WRITE WORD Reg %s: %s", address, e)

    async def write_uchar(self, address: int, value: int):
        """Schreibt ein 8-bit Unsigned Integer als WORD (nur Low-Byte)."""
        try:
            await self.ensure_connected()
            await self._client.write_register(address=address, value=int(value) & 0xFF)
            _LOGGER.debug("Wrote UCHAR %d to Reg %s", value, address)
        except Exception as e:
            _LOGGER.error("Exception WRITE UCHAR Reg %s: %s", address, e)
