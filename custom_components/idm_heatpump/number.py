from homeassistant.components.number import NumberEntity
from .modbus_handler import ModbusHandler
from .const import DOMAIN
NUMBERS = [
    ("idm_ww_solltemp", 1032, 35, 95, 1),
    ("idm_hk_a_raumsoll_normal", 1401, 15, 30, 0.5),
    ("idm_hk_c_raumsoll_normal", 1405, 15, 30, 0.5),
    ("idm_hk_a_heizkurve", 1429, 0.1, 3.5, 0.1),
    ("idm_hk_c_heizkurve", 1433, 0.1, 3.5, 0.1),
    ("idm_hk_a_parallelverschiebung", 1505, 0, 30, 1),
    ("idm_hk_c_parallelverschiebung", 1507, 0, 30, 1),
    ("idm_hk_a_heizgrenze", 1442, 0, 50, 1),
    ("idm_hk_c_heizgrenze", 1444, 0, 50, 1),
]

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    handler = ModbusHandler(data['host'], data['port'], data['unit'])
    handler.connect()
    entities = []
    for name, address, minv, maxv, step in NUMBERS:
        entities.append(IdmNumber(handler, name, address, minv, maxv, step))
    async_add_entities(entities, True)

class IdmNumber(NumberEntity):
    def __init__(self, handler, name, address, minv, maxv, step):
        self._handler = handler
        self._name = name
        self._address = address
        self._min = minv
        self._max = maxv
        self._step = step
        self._value = None

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return f"{self._name}"

    @property
    def native_min_value(self):
        return self._min

    @property
    def native_max_value(self):
        return self._max

    @property
    def native_step(self):
        return self._step

    @property
    def native_value(self):
        return self._value

    async def async_update(self):
        val = self._handler.read_int(self._address)
        self._value = val

    async def async_set_native_value(self, value: float):
        ok = self._handler.write_int(self._address, int(value))
        if ok:
            self._value = value
