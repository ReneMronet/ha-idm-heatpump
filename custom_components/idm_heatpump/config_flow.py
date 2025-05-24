# custom_components/idm_heatpump/config_flow.py
"""Config flow for iDM Heat Pump integration."""

import logging
import voluptuous as vol
from typing import Any
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, CONF_UNIT_ID

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
    vol.Optional(CONF_UNIT_ID, default=1): int,
    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
})


async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    """Validate the user input allows us to connect."""
    
    host = data[CONF_HOST]
    port = data[CONF_PORT]
    unit_id = data[CONF_UNIT_ID]
    
    # Test Modbus connection
    client = ModbusTcpClient(host=host, port=port, timeout=10)
    
    try:
        connection_result = await hass.async_add_executor_job(client.connect)
        if not connection_result:
            raise ConnectionError("Could not connect to Modbus device")
        
        # Test reading a basic register (outdoor temperature) - updated API call
        result = await hass.async_add_executor_job(
            lambda: client.read_input_registers(
                address=0, 
                count=2, 
                slave=unit_id
            )
        )
        
        if result.isError():
            raise ConnectionError("Could not read from Modbus device")
        
        # Try to identify if this is an iDM heat pump by reading system mode
        system_mode_result = await hass.async_add_executor_job(
            lambda: client.read_holding_registers(
                address=5, 
                count=1, 
                slave=unit_id
            )
        )
        
        if system_mode_result.isError():
            _LOGGER.warning("Could not read system mode, but basic connection works")
        
        await hass.async_add_executor_job(client.close)
        
        return {"title": f"iDM Heat Pump ({host})"}
        
    except Exception as exc:
        try:
            await hass.async_add_executor_job(client.close)
        except:
            pass
        if isinstance(exc, ModbusException):
            raise ConnectionError(f"Modbus error: {exc}")
        raise ConnectionError(f"Connection failed: {exc}")


class IDMConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for iDM Heat Pump."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                
                # Check if already configured
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(title=info["title"], data=user_input)
                
            except ConnectionError as exc:
                _LOGGER.error("Connection error: %s", exc)
                errors["base"] = "cannot_connect"
            except Exception as exc:
                _LOGGER.exception("Unexpected exception: %s", exc)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "default_port": str(DEFAULT_PORT),
                "default_unit_id": "1",
                "default_scan_interval": str(DEFAULT_SCAN_INTERVAL),
            },
        )

    async def async_step_import(self, import_config) -> FlowResult:
        """Import config from configuration.yaml."""
        return await self.async_step_user(import_config)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Create the options flow."""
        return IDMOptionsFlowHandler(config_entry)


class IDMOptionsFlowHandler(config_entries.OptionsFlow):
    """iDM Heat Pump config flow options handler."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize iDM Heat Pump options flow."""
        # KORRIGIERT: Verwende nicht mehr self.config_entry direkt
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self._config_entry.options.get(
                            CONF_SCAN_INTERVAL, 
                            self._config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                        ),
                    ): vol.All(int, vol.Range(min=10, max=300)),
                }
            ),
        )