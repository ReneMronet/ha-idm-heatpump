# custom_components/idm_heatpump/binary_sensor.py
"""Binary sensor platform for iDM Heat Pump."""

import logging
from typing import Any, Dict, Optional

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN, MODBUS_REGISTERS
from .coordinator import IDMDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Define which sensors should be binary sensors
BINARY_SENSOR_REGISTERS = {
    "compressor_1_status": {
        "device_class": BinarySensorDeviceClass.RUNNING,
        "name": "Verdichter 1",
        "icon": "mdi:engine",
        "entity_category": None,
    },
    "compressor_2_status": {
        "device_class": BinarySensorDeviceClass.RUNNING,
        "name": "Verdichter 2", 
        "icon": "mdi:engine",
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    "heatpump_malfunction_summary": {
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "name": "Wärmepumpe Störung",
        "icon": "mdi:alert",
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up iDM Heat Pump binary sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    # Create binary sensors for specific registers
    for register_name, config in BINARY_SENSOR_REGISTERS.items():
        if register_name in MODBUS_REGISTERS:
            entities.append(IDMBinarySensor(coordinator, register_name, config))
    
    # Log information about entity creation
    _LOGGER.info("Created %d binary sensor entities", len(entities))
    
    async_add_entities(entities, True)


class IDMBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of an iDM Heat Pump binary sensor."""

    def __init__(
        self,
        coordinator: IDMDataUpdateCoordinator,
        register_name: str,
        config: Dict[str, Any],
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        
        self._register_name = register_name
        self._config = config
        self._attr_name = f"iDM {config['name']}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{register_name}"
        self._attr_device_class = config.get("device_class")
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
        """Return true if the binary sensor is on."""
        value = self.coordinator.data.get(self._register_name)
        
        if value is None:
            return None
        
        # Convert register value to boolean
        return bool(value)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._register_name in self.coordinator.data
        )