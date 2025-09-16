from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, DEFAULT_PORT, DEFAULT_UNIT

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required("host"): str,
    vol.Optional("port", default=DEFAULT_PORT): int,
    vol.Optional("unit", default=DEFAULT_UNIT): int,
})

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # basic validation could be added here
            return self.async_create_entry(title=user_input["host"], data=user_input)
        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors)
