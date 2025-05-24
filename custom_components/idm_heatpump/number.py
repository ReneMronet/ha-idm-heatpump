# custom_components/idm_heatpump/number.py
"""Number platform for iDM Heat Pump."""

import logging
from typing import Any, Dict, Optional

from homeassistant.components.number import NumberEntity
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
    """Set up iDM Heat Pump number entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    skipped_entities = []  # Liste der übersprungenen Entitäten
    
    # Create number entities for registers with entity_type = "number"
    for register_name, config in MODBUS_REGISTERS.items():
        if config.get("entity_type") == "number":
            entities.append(IDMNumber(coordinator, register_name, config))
        elif config.get("entity_type") == "number":
            skipped_entities.append(register_name)
    
    # Log information about entity creation
    _LOGGER.info("Created %d number entities", len(entities))
    if skipped_entities:
        _LOGGER.debug("Skipped number entities: %s", ", ".join(skipped_entities))
    
    async_add_entities(entities, True)


class IDMNumber(CoordinatorEntity, NumberEntity):
    """Representation of an iDM Heat Pump number entity."""

    def __init__(
        self,
        coordinator: IDMDataUpdateCoordinator,
        register_name: str,
        config: Dict[str, Any],
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        
        self._register_name = register_name
        self._config = config
        self._attr_name = f"iDM {config['name']}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{register_name}"
        
        # Set number attributes based on config
        self._attr_native_unit_of_measurement = config.get("unit")
        self._attr_device_class = config.get("device_class")
        self._attr_icon = config.get("icon")
        self._attr_native_min_value = config.get("min", 0)
        self._attr_native_max_value = config.get("max", 100)
        self._attr_native_step = config.get("step", 1)
        self._attr_mode = "box"  # Allow direct input
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
    def native_value(self) -> Optional[float]:
        """Return the current value."""
        value = self.coordinator.data.get(self._register_name)
        
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        success = await self.coordinator.async_write_register(self._register_name, value)
        
        if not success:
            _LOGGER.error("Failed to set %s to %s", self._register_name, value)
        else:
            _LOGGER.debug("Successfully set %s to %s", self._register_name, value)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._register_name in self.coordinator.data
        )