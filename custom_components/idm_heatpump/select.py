"""Select platform for iDM Heat Pump."""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SELECT_ENTITIES, REGISTER_ADDRESSES
from .coordinator import IdmDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up iDM Heat Pump select based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    for select_config in SELECT_ENTITIES:
        entities.append(IdmSelect(coordinator, select_config))
    
    async_add_entities(entities)


class IdmSelect(CoordinatorEntity, SelectEntity):
    """Representation of an iDM Heat Pump select entity."""

    def __init__(self, coordinator: IdmDataUpdateCoordinator, config):
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._key = config["key"]
        self._name = config["name"]
        self._options_config = config["options"]
        self._icon = config.get("icon")
        self._attr_unique_id = f"{coordinator.host}_{self._key}"
        
        # Create mappings for options
        self._options = [opt["label"] for opt in self._options_config]
        self._values = {opt["label"]: opt["value"] for opt in self._options_config}
        self._val_to_label = {opt["value"]: opt["label"] for opt in self._options_config}
    
    @property
    def name(self):
        """Return the name of the select entity."""
        return f"iDM {self._name}"
    
    @property
    def icon(self):
        """Return the icon to use for the entity."""
        return self._icon
    
    @property
    def options(self):
        """Return the options for the entity."""
        return self._options
    
    @property
    def current_option(self):
        """Return the current selected option."""
        if self.coordinator.data is None or self._key not in self.coordinator.data:
            return None
        
        value = str(self.coordinator.data[self._key])
        return self._val_to_label.get(value, None)
    
    async def async_select_option(self, option):
        """Change the selected option."""
        if option not in self._values:
            _LOGGER.error(f"Invalid option: {option}")
            return
        
        value = int(self._values[option])
        address = REGISTER_ADDRESSES[self._key]
        await self.coordinator.async_write_register(address, value)
    
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