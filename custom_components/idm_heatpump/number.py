"""Number platform for iDM Heat Pump."""
import logging

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NUMBER_ENTITIES, REGISTER_ADDRESSES, DATA_TYPE_FLOAT
from .coordinator import IdmDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up iDM Heat Pump number based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    for number_config in NUMBER_ENTITIES:
        entities.append(IdmNumber(coordinator, number_config))
    
    async_add_entities(entities)


class IdmNumber(CoordinatorEntity, NumberEntity):
    """Representation of an iDM Heat Pump number entity."""

    def __init__(self, coordinator: IdmDataUpdateCoordinator, config):
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._key = config["key"]
        self._name = config["name"]
        self._min_value = config["min"]
        self._max_value = config["max"]
        self._step = config["step"]
        self._unit = config.get("unit")
        self._icon = config.get("icon")
        self._attr_unique_id = f"{coordinator.host}_{self._key}"
    
    @property
    def name(self):
        """Return the name of the number entity."""
        return f"iDM {self._name}"
    
    @property
    def icon(self):
        """Return the icon to use for the entity."""
        return self._icon
    
    @property
    def min_value(self):
        """Return the minimum value."""
        return self._min_value
    
    @property
    def max_value(self):
        """Return the maximum value."""
        return self._max_value
    
    @property
    def step(self):
        """Return the increment/decrement step."""
        return self._step
    
    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit
    
    @property
    def value(self):
        """Return the current value."""
        if self.coordinator.data is None or self._key not in self.coordinator.data:
            return None
        
        return self.coordinator.data[self._key]
    
    async def async_set_value(self, value):
        """Update the current value."""
        address = REGISTER_ADDRESSES[self._key]
        
        # Check if it's a float value or needs special handling
        if self._step < 1:
            # For values like temperatures with 0.5 steps
            await self.coordinator.async_write_register(address, value, DATA_TYPE_FLOAT)
        else:
            # For integer values
            await self.coordinator.async_write_register(address, int(value))
    
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