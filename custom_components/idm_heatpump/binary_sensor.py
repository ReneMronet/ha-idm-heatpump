from homeassistant.components.binary_sensor import BinarySensorEntity
from .modbus_handler import ModbusHandler
from .const import DOMAIN

BINARIES = [
    ("idm_kompressor_status", 1100),
    ("idm_heizstab_leistung", 76),
    ("idm_warmwasser_anforderung", 1093),
    ("idm_summenstoerung", 1099),
    ("idm_abtauung_aktiv", 1090),  # 3 indicates Abtauung according to doc; we'll treat non-zero as active
]

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    handler = ModbusHandler(data['host'], data['port'], data['unit'])
    handler.connect()
    entities = []
    for name, address in BINARIES:
        entities.append(IdmBinary(handler, name, address))
    async_add_entities(entities, True)

class IdmBinary(BinarySensorEntity):
    def __init__(self, handler, name, address):
        self._handler = handler
        self._name = name
        self._address = address
        self._state = False

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return f"{self._name}"

    @property
    def is_on(self):
        return self._state

    async def async_update(self):
        val = self._handler.read_int(self._address)
        # treat any non-zero as active/true
        self._state = bool(val and val != -1)
