# custom_components/idm_heatpump/switch.py
"""Switch platform for iDM Heat Pump."""

import logging
from typing import Any, Dict, Optional

from homeassistant.components.switch import SwitchEntity
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
    """Set up iDM Heat Pump switch entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    skipped_entities = []  # Liste der übersprungenen Entitäten
    
    # Create switch entities for registers with entity_type = "switch"
    for register_name, config in MODBUS_REGISTERS.items():
        if config.get("entity_type") == "switch":
            entities.append(IDMSwitch(coordinator, register_name, config))
        elif config.get("entity_type") == "switch":
            skipped_entities.append(register_name)
    
    # Log information about entity creation
    _LOGGER.info("Created %d switch entities", len(entities))
    if skipped_entities:
        _LOGGER.debug("Skipped switch entities: %s", ", ".join(skipped_entities))
    
    async_add_entities(entities, True)


class IDMSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of an iDM Heat Pump switch entity."""

    def __init__(
        self,
        coordinator: IDMDataUpdateCoordinator,
        register_name: str,
        config: Dict[str, Any],
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        
        self._register_name = register_name
        self._config = config
        self._attr_name = f"iDM {config['name']}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{register_name}"
        self._attr_icon = config.get("icon")
        self._attr_entity_category = config.get("entity_category")
        
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
    def is_on(self) -> Optional[bool]:
        """Return true if switch is on."""
        value = self.coordinator.data.get(self._register_name)
        
        if value is None:
            return None
        
        # Convert register value to boolean
        return bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        success = await self.coordinator.async_write_register(self._register_name, 1)
        
        if not success:
            _LOGGER.error("Failed to turn on %s", self._register_name)
        else:
            _LOGGER.debug("Successfully turned on %s", self._register_name)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        success = await self.coordinator.async_write_register(self._register_name, 0)
        
        if not success:
            _LOGGER.error("Failed to turn off %s", self._register_name)
        else:
            _LOGGER.debug("Successfully turned off %s", self._register_name)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._register_name in self.coordinator.data
        )