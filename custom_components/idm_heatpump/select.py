# custom_components/idm_heatpump/select.py
"""Select platform for iDM Heat Pump."""

import logging
from typing import Any, Dict, Optional

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODBUS_REGISTERS
from .coordinator import IDMDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up iDM Heat Pump select entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    skipped_entities = []  # Liste der übersprungenen Entitäten
    
    # Create select entities for registers with entity_type = "select"
    for register_name, config in MODBUS_REGISTERS.items():
        if config.get("entity_type") == "select":
            entities.append(IDMSelect(coordinator, register_name, config))
        elif config.get("entity_type") == "select":
            skipped_entities.append(register_name)
    
    # Log information about entity creation
    _LOGGER.info("Created %d select entities", len(entities))
    if skipped_entities:
        _LOGGER.debug("Skipped select entities: %s", ", ".join(skipped_entities))
    
    async_add_entities(entities, True)


class IDMSelect(CoordinatorEntity, SelectEntity):
    """Representation of an iDM Heat Pump select entity."""

    def __init__(
        self,
        coordinator: IDMDataUpdateCoordinator,
        register_name: str,
        config: Dict[str, Any],
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        
        self._register_name = register_name
        self._config = config
        self._attr_name = f"iDM {config['name']}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{register_name}"
        self._attr_icon = config.get("icon")
        self._attr_entity_category = config.get("entity_category")
        
        # Set options from config
        options_dict = config.get("options", {})
        self._options_dict = options_dict
        self._attr_options = list(options_dict.values())
        
        # Set device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.entry.entry_id)},
            "name": "iDM Navigator 2.0 Heat Pump",
            "manufacturer": "iDM Energiesysteme GmbH",
            "model": "Navigator 2.0", 
            "sw_version": coordinator.entry.data.get("sw_version", "Unknown"),
            "configuration_url": f"http://{coordinator.host}",
        }

    @property
    def current_option(self) -> Optional[str]:
        """Return the current option."""
        value = self.coordinator.data.get(self._register_name)
        
        if value is None:
            return None
        
        return self._options_dict.get(value, None)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        # Find the numeric value for the selected option
        numeric_value = None
        for key, val in self._options_dict.items():
            if val == option:
                numeric_value = key
                break
        
        if numeric_value is None:
            _LOGGER.error("Invalid option selected: %s", option)
            return
        
        success = await self.coordinator.async_write_register(self._register_name, numeric_value)
        
        if not success:
            _LOGGER.error("Failed to set %s to %s (%s)", self._register_name, option, numeric_value)
        else:
            _LOGGER.debug("Successfully set %s to %s (%s)", self._register_name, option, numeric_value)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._register_name in self.coordinator.data
        )