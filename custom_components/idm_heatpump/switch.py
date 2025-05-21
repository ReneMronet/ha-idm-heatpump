"""Switch platform for iDM Heat Pump."""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SWITCH_ENTITIES, REGISTER_ADDRESSES
from .coordinator import IdmDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up iDM Heat Pump switch based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    for switch_config in SWITCH_ENTITIES:
        entities.append(IdmSwitch(coordinator, switch_config))
    
    async_add_entities(entities)


class IdmSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of an iDM Heat Pump switch."""

    def __init__(self, coordinator: IdmDataUpdateCoordinator, config):
        """Initialize the switch."""
        super().__init__(coordinator)
        self._key = config["key"]
        self._name = config["name"]
        self._icon = config.get("icon")
        self._attr_unique_id = f"{coordinator.host}_{self._key}"
    
    @property
    def name(self):
        """Return the name of the switch."""
        return f"iDM {self._name}"
    
    @property
    def icon(self):
        """Return the icon to use for the switch."""
        return self._icon
    
    @property
    def is_on(self):
        """Return True if the switch is on."""
        if self.coordinator.data is None or self._key not in self.coordinator.data:
            return None
        return bool(self.coordinator.data[self._key])
    
    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        address = REGISTER_ADDRESSES[self._key]
        await self.coordinator.async_write_coil(address, True)
    
    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        address = REGISTER_ADDRESSES[self._key]
        await self.coordinator.async_write_coil(address, False)
    
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