from homeassistant.components.switch import SwitchEntity
from .modbus_handler import ModbusHandler
from .const import DOMAIN

SWITCHES = [
    ("idm_system_betriebsart_automatik", 1005, 1, 0),  # writes 1/0 to set automatik on/off
    ("idm_ww_ladung_start", 1712, 1, 0),  # use 1712 (BOOL RW Anforderung Warmwasserladung) for control
]

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    handler = ModbusHandler(data['host'], data['port'], data['unit'])
    handler.connect()
    entities = []
    for name, address, on_val, off_val in SWITCHES:
        entities.append(IdmSwitch(handler, name, address, on_val, off_val))
    async_add_entities(entities, True)

class IdmSwitch(SwitchEntity):
    def __init__(self, handler, name, address, on_val, off_val):
        self._handler = handler
        self._name = name
        self._address = address
        self._on = on_val
        self._off = off_val
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
        self._state = bool(val)

    async def async_turn_on(self, **kwargs):
        self._handler.write_int(self._address, self._on)
        self._state = True

    async def async_turn_off(self, **kwargs):
        self._handler.write_int(self._address, self._off)
        self._state = False
