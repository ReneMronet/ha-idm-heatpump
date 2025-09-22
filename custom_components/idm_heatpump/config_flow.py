"""
config_flow.py – v1.11 (2025-09-22)

ConfigFlow + OptionsFlow für die iDM Wärmepumpe Integration.
- Einrichtung über Host, Port, Unit-ID und Update-Intervall
- Optionen können nachträglich geändert werden
"""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import (
    DOMAIN,
    DEFAULT_PORT,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    CONF_UNIT_ID,
    DEFAULT_UNIT_ID,
)


class IDMHeatpumpConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="iDM Wärmepumpe",
                data=user_input,
            )

        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Optional(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): int,
            vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): int,
        })

        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    def async_get_options_flow(config_entry):
        return IDMHeatpumpOptionsFlow(config_entry)


class IDMHeatpumpOptionsFlow(config_entries.OptionsFlow):
    """OptionsFlow für nachträgliche Änderungen der Integration."""

    def __init__(self, config_entry):
        super().__init__()
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema({
            vol.Optional(
                CONF_HOST,
                default=self._entry.options.get(
                    CONF_HOST,
                    self._entry.data.get(CONF_HOST, "0.0.0.0"),
                ),
            ): str,
            vol.Optional(
                CONF_PORT,
                default=self._entry.options.get(
                    CONF_PORT,
                    self._entry.data.get(CONF_PORT, DEFAULT_PORT),
                ),
            ): int,
            vol.Optional(
                CONF_UNIT_ID,
                default=self._entry.options.get(
                    CONF_UNIT_ID,
                    self._entry.data.get(CONF_UNIT_ID, DEFAULT_UNIT_ID),
                ),
            ): int,
            vol.Optional(
                CONF_UPDATE_INTERVAL,
                default=self._entry.options.get(
                    CONF_UPDATE_INTERVAL,
                    self._entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                ),
            ): int,
        })

        return self.async_show_form(step_id="init", data_schema=schema)
