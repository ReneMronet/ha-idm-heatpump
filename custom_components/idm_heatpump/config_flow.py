"""Config flow for iDM Heat Pump integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import CONF_NAME
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.exceptions import ConnectionException

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    CONF_UNIT_ID,
    CONF_SCAN_INTERVAL,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_UNIT_ID,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class IdmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for iDM Heat Pump."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            unit_id = user_input.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)
            
            # Check if already configured
            await self.async_set_unique_id(f"{host}_{port}_{unit_id}")
            self._abort_if_unique_id_configured()
            
            # Test connection
            if not await self._test_connection(host, port):
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, DEFAULT_NAME),
                    data=user_input
                )

        # Show form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Optional(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): int,
                    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
                }
            ),
            errors=errors,
        )
    
    async def _test_connection(self, host, port):
        """Test connectivity to the Modbus server."""
        try:
            modbus_client = await self.hass.async_add_executor_job(
                ModbusTcpClient, host, port
            )
            connected = await self.hass.async_add_executor_job(
                modbus_client.connect
            )
            if connected:
                await self.hass.async_add_executor_job(modbus_client.close)
                return True
            return False
        except ConnectionException:
            return False
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unknown error connecting to iDM heat pump")
            return False

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return IdmOptionsFlowHandler(config_entry)


class IdmOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow for iDM."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=self.config_entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                ),
            ): int,
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))