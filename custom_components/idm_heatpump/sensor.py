# custom_components/idm_heatpump/sensor.py
"""Sensor platform for iDM Heat Pump."""

import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import SensorEntity
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
    """Set up iDM Heat Pump sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    skipped_entities = []  # Liste der übersprungenen Entitäten
    
    # Create sensors for all registers that don't have a specific entity_type
    for register_name, config in MODBUS_REGISTERS.items():
        if config.get("entity_type") is None:
            entities.append(IDMSensor(coordinator, register_name, config))
            _LOGGER.debug("Created sensor entity for register: %s (address: %s)", 
                         register_name, config["address"])
        else:
            skipped_entities.append(f"{register_name} (type: {config.get('entity_type')})")
    
    # Log information about entity creation
    _LOGGER.info("Created %d sensor entities", len(entities))
    if skipped_entities:
        _LOGGER.debug("Skipped sensor entities (handled by other platforms): %s", 
                     ", ".join(skipped_entities[:20]) + ("..." if len(skipped_entities) > 20 else ""))
    
    async_add_entities(entities, True)


class IDMSensor(CoordinatorEntity, SensorEntity):
    """Representation of an iDM Heat Pump sensor."""

    def __init__(
        self,
        coordinator: IDMDataUpdateCoordinator,
        register_name: str,
        config: Dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        self._register_name = register_name
        self._config = config
        self._attr_name = f"iDM {config['name']}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{register_name}"
        
        # Für Status-Sensoren mit options: Keine numerischen Eigenschaften setzen
        if "options" in config:
            self._attr_native_unit_of_measurement = None
            self._attr_device_class = None
            self._attr_state_class = None
            self._attr_suggested_display_precision = None
        else:
            # Normale Sensoren: Standard-Eigenschaften setzen
            self._attr_native_unit_of_measurement = config.get("unit")
            self._attr_device_class = config.get("device_class")
            self._attr_state_class = config.get("state_class")
            self._attr_suggested_display_precision = config.get("precision", 1)
        
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
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        value = self.coordinator.data.get(self._register_name)
        
        if value is None:
            return None
        
        # Handle special cases for status registers with options
        # Diese werden als Text-Sensoren behandelt
        if "options" in self._config:
            options = self._config["options"]
            return options.get(value, f"Unknown ({value})")
        
        # Round float values to reasonable precision
        if isinstance(value, float):
            precision = self._config.get("precision", 1)
            return round(value, precision)
        
        return value

    @property
    def device_class(self) -> Optional[str]:
        """Return the device class."""
        # Status-Sensoren mit options haben explizit keine device_class
        if "options" in self._config:
            return None
        return self._attr_device_class

    @property
    def state_class(self) -> Optional[str]:
        """Return the state class."""
        # Status-Sensoren mit options haben explizit keine state_class
        if "options" in self._config:
            return None
        return self._attr_state_class

    @property
    def native_unit_of_measurement(self) -> Optional[str]:
        """Return the unit of measurement."""
        # Status-Sensoren mit options haben explizit keine Einheit
        if "options" in self._config:
            return None
        return self._attr_native_unit_of_measurement

    @property
    def suggested_display_precision(self) -> Optional[int]:
        """Return the suggested display precision."""
        # Status-Sensoren mit options haben keine Precision
        if "options" in self._config:
            return None
        return self._config.get("precision", 1)

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return True

    @property
    def entity_category(self) -> Optional[str]:
        """Return the entity category."""
        return self._config.get("entity_category")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        attributes = {
            "register_address": self._config["address"],
            "register_type": self._config["type"],
            "data_type": self._config["data_type"],
        }
        
        # Für Status-Register: Numerischen Wert als Attribut hinzufügen
        if "options" in self._config:
            raw_value = self.coordinator.data.get(self._register_name)
            if raw_value is not None:
                attributes["raw_value"] = raw_value
                # Zusätzlich alle verfügbaren Optionen anzeigen
                attributes["available_options"] = self._config["options"]
        
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        is_available = (
            self.coordinator.last_update_success
            and self._register_name in self.coordinator.data
        )
        if not is_available:
            _LOGGER.debug("Entity %s is not available. Coordinator success: %s, Register in data: %s",
                         self._attr_name,
                         self.coordinator.last_update_success,
                         self._register_name in self.coordinator.data if self.coordinator.data else False)
        return is_available