"""Sensor platform for iDM Heat Pump."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_ENTITIES
from .coordinator import IdmDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up iDM Heat Pump sensor based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    # Add all sensor entities
    for sensor_config in SENSOR_ENTITIES:
        entities.append(IdmSensor(coordinator, sensor_config))
    
    async_add_entities(entities)


class IdmSensor(CoordinatorEntity, SensorEntity):
    """Representation of an iDM Heat Pump sensor."""

    def __init__(self, coordinator: IdmDataUpdateCoordinator, config):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = config["key"]
        self._name = config["name"]
        self._device_class = config.get("device_class")
        self._unit_of_measurement = config.get("unit")
        self._precision = config.get("precision", 0)
        self._value_map = config.get("value_map")
        self._state_class = config.get("state_class")
        
        # Set unique ID
        self._attr_unique_id = f"{coordinator.host}_{self._key}"
        
    @property
    def name(self):
        """Return the name of the sensor."""
        return f"iDM {self._name}"
    
    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._device_class
    
    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement
    
    @property
    def state_class(self):
        """Return the state class."""
        return self._state_class
    
    @property
    def state(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None or self._key not in self.coordinator.data:
            return None
        
        value = self.coordinator.data[self._key]
        
        # Apply value mapping if provided
        if self._value_map is not None and value in self._value_map:
            return self._value_map[value]
        
        # Apply precision for numeric values
        if isinstance(value, (int, float)) and self._precision is not None:
            return round(value, self._precision)
        
        return value
    
    @property
    def device_info(self):
        """Return device information about this entity."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.host)},
            "name": "iDM Heat Pump",
            "manufacturer": "iDM Energiesysteme GmbH",
            "model": "iDM Navigator 2.0",
            "sw_version": "2.0",
        }