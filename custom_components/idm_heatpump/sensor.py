from datetime import timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.const import TEMP_CELSIUS, POWER_KILO_WATT, PERCENTAGE
from .const import DOMAIN, SCAN_INTERVAL
from .modbus_handler import ModbusHandler

SENSORS = [
    # name, address, unit, type ('float' or 'int')
    ("idm_aussentemperatur", 1000, TEMP_CELSIUS, 'float'),
    ("idm_wp_vorlauf", 1050, TEMP_CELSIUS, 'float'),
    ("idm_wp_ruecklauf", 1052, TEMP_CELSIUS, 'float'),
    ("idm_ww_oben", 1014, TEMP_CELSIUS, 'float'),
    ("idm_ww_unten", 1012, TEMP_CELSIUS, 'float'),
    ("idm_hk_a_vorlauf", 1350, TEMP_CELSIUS, 'float'),
    ("idm_hk_a_raumtemperatur", 1364, TEMP_CELSIUS, 'float'),
    ("idm_hk_c_vorlauf", 1354, TEMP_CELSIUS, 'float'),
    ("idm_hk_c_raumtemperatur", 1368, TEMP_CELSIUS, 'float'),
    ("idm_pv_ueberschuss", 74, POWER_KILO_WATT, 'float'),
    ("idm_pv_produktion", 78, POWER_KILO_WATT, 'float'),
    ("idm_hausverbrauch", 82, POWER_KILO_WATT, 'float'),
    ("idm_batterie_entladung", 84, POWER_KILO_WATT, 'float'),
    ("idm_batterie_fuellstand", 86, PERCENTAGE, 'int'),
    ("idm_thermische_momentanleistung", 1790, POWER_KILO_WATT, 'float'),
]

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    handler = ModbusHandler(data['host'], data['port'], data['unit'])
    handler.connect()
    entities = []
    for name, address, unit, dtype in SENSORS:
        entities.append(IdmSensor(handler, name, address, unit, dtype))
    async_add_entities(entities, True)

class IdmSensor(Entity):
    def __init__(self, handler, name, address, unit, dtype):
        self._handler = handler
        self._name = name
        self._address = address
        self._unit = unit
        self._dtype = dtype
        self._state = None

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return f"{self._name}"

    @property
    def unit_of_measurement(self):
        return self._unit

    @property
    def state(self):
        return self._state

    async def async_update(self):
        try:
            if self._dtype == 'float':
                val = self._handler.read_float(self._address)
            else:
                val = self._handler.read_int(self._address)
            self._state = val
        except Exception:
            self._state = None
