# Datei: config_flow.py
"""
iDM Wärmepumpe (Modbus TCP)
Version: v1.20 (Dokumentations-Update)
Stand: 2025-09-24
"""

import socket
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
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)

            # Duplikatsprüfung (Setup)
            for entry in self._async_current_entries():
                if entry.data[CONF_HOST] == host and entry.data.get(CONF_PORT, DEFAULT_PORT) == port:
                    return self.async_abort(reason="already_configured")

            try:
                sock = socket.create_connection((host, port), timeout=3)
                sock.close()

                return self.async_create_entry(
                    title="iDM Wärmepumpe",
                    data=user_input,
                )

            except OSError:
                errors["base"] = "cannot_connect"

        schema = vol.Schema({
            vol.Required(CONF_HOST, default=user_input.get(CONF_HOST) if user_input else ""): str,
            vol.Optional(CONF_PORT, default=user_input.get(CONF_PORT) if user_input else DEFAULT_PORT): int,
            vol.Optional(CONF_UNIT_ID, default=user_input.get(CONF_UNIT_ID) if user_input else DEFAULT_UNIT_ID): int,
            vol.Optional(CONF_UPDATE_INTERVAL, default=user_input.get(CONF_UPDATE_INTERVAL) if user_input else DEFAULT_UPDATE_INTERVAL): int,
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry):
        return IDMHeatpumpOptionsFlow(config_entry)


class IDMHeatpumpOptionsFlow(config_entries.OptionsFlow):
    """OptionsFlow für nachträgliche Änderungen der Integration."""

    def __init__(self, config_entry):
        super().__init__()
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}

        if user_input is not None:
            host = user_input.get(
                CONF_HOST,
                self._entry.options.get(
                    CONF_HOST,
                    self._entry.data.get(CONF_HOST, "0.0.0.0"),
                ),
            )
            port = user_input.get(
                CONF_PORT,
                self._entry.options.get(
                    CONF_PORT,
                    self._entry.data.get(CONF_PORT, DEFAULT_PORT),
                ),
            )

            # Duplikatsprüfung (OptionsFlow)
            for entry in self.hass.config_entries.async_entries(DOMAIN):
                if (
                    entry.entry_id != self._entry.entry_id
                    and entry.data[CONF_HOST] == host
                    and entry.data.get(CONF_PORT, DEFAULT_PORT) == port
                ):
                    return self.async_abort(reason="already_configured")

            try:
                sock = socket.create_connection((host, port), timeout=3)
                sock.close()

                return self.async_create_entry(title="", data=user_input)

            except OSError:
                errors["base"] = "cannot_connect_options"

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

        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
