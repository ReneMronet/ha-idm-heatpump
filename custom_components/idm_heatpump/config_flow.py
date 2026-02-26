# Datei: config_flow.py
"""
iDM Wärmepumpe (Modbus TCP)
Version: v2.0
Stand: 2026-02-26

Änderungen v2.0:
- Zweistufiger Config-Flow: Schritt 1 = Verbindung, Schritt 2 = Heizkreisauswahl
- Options-Flow: Heizkreise nachträglich ändern (löst Reload aus)
"""

import socket
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    DOMAIN,
    DEFAULT_PORT,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    CONF_UNIT_ID,
    DEFAULT_UNIT_ID,
    CONF_HEATING_CIRCUITS,
    DEFAULT_HEATING_CIRCUITS,
    ALL_HEATING_CIRCUITS,
)

HEATING_CIRCUIT_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=ALL_HEATING_CIRCUITS,
        multiple=True,
        mode=SelectSelectorMode.LIST,
    )
)


class IDMHeatpumpConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    def __init__(self):
        super().__init__()
        self._user_input = {}

    async def async_step_user(self, user_input=None):
        """Schritt 1: Verbindungsdaten."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)

            # Duplikatsprüfung
            for entry in self._async_current_entries():
                if (
                    entry.data.get(CONF_HOST) == host
                    and entry.data.get(CONF_PORT, DEFAULT_PORT) == port
                ):
                    return self.async_abort(reason="already_configured")

            try:
                sock = socket.create_connection((host, port), timeout=3)
                sock.close()
            except OSError:
                errors["base"] = "cannot_connect"
            else:
                self._user_input = user_input
                return await self.async_step_circuits()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_HOST,
                    default=user_input.get(CONF_HOST, "") if user_input else "",
                ): str,
                vol.Optional(
                    CONF_PORT,
                    default=user_input.get(CONF_PORT, DEFAULT_PORT) if user_input else DEFAULT_PORT,
                ): int,
                vol.Optional(
                    CONF_UNIT_ID,
                    default=user_input.get(CONF_UNIT_ID, DEFAULT_UNIT_ID) if user_input else DEFAULT_UNIT_ID,
                ): int,
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL) if user_input else DEFAULT_UPDATE_INTERVAL,
                ): int,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_circuits(self, user_input=None):
        """Schritt 2: Heizkreise auswählen."""
        if user_input is not None:
            selected = user_input.get(CONF_HEATING_CIRCUITS, DEFAULT_HEATING_CIRCUITS)
            self._user_input[CONF_HEATING_CIRCUITS] = selected

            return self.async_create_entry(
                title="iDM Wärmepumpe",
                data=self._user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_HEATING_CIRCUITS,
                    default=DEFAULT_HEATING_CIRCUITS,
                ): HEATING_CIRCUIT_SELECTOR,
            }
        )

        return self.async_show_form(
            step_id="circuits", data_schema=schema, errors={}
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return IDMHeatpumpOptionsFlow(config_entry)


class IDMHeatpumpOptionsFlow(config_entries.OptionsFlow):
    """OptionsFlow für nachträgliche Änderungen."""

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

            # Duplikatsprüfung
            for entry in self.hass.config_entries.async_entries(DOMAIN):
                if (
                    entry.entry_id != self._entry.entry_id
                    and entry.data.get(CONF_HOST) == host
                    and entry.data.get(CONF_PORT, DEFAULT_PORT) == port
                ):
                    return self.async_abort(reason="already_configured")

            try:
                sock = socket.create_connection((host, port), timeout=3)
                sock.close()
            except OSError:
                errors["base"] = "cannot_connect_options"
            else:
                return self.async_create_entry(title="", data=user_input)

        current_circuits = self._entry.options.get(
            CONF_HEATING_CIRCUITS,
            self._entry.data.get(CONF_HEATING_CIRCUITS, DEFAULT_HEATING_CIRCUITS),
        )

        schema = vol.Schema(
            {
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
                vol.Required(
                    CONF_HEATING_CIRCUITS,
                    default=current_circuits,
                ): HEATING_CIRCUIT_SELECTOR,
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=schema, errors=errors
        )
