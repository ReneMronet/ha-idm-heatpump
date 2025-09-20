"""
config_flow.py – v1.8 (2025-09-17)

ConfigFlow + OptionsFlow für die iDM Wärmepumpe Integration.

- Einrichtung über Host, Port und Update-Intervall
- Kein aktiver Verbindungstest beim Setup (nur Eingabe)
- Optionen können nachträglich über den OptionsFlow geändert werden
"""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT

# Eigene Konstanten
from .const import (
    DOMAIN,
    DEFAULT_PORT,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
)


class IDMHeatpumpConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """ConfigFlow für die Erst-Einrichtung der iDM Wärmepumpe."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """
        Erster Schritt beim Hinzufügen der Integration.

        Fragt den Benutzer nach:
        - Host (IP-Adresse)
        - Port (Standard: 502)
        - Update-Intervall in Sekunden
        """
        if user_input is not None:
            # Direkt einen Eintrag anlegen (kein Verbindungstest hier)
            return self.async_create_entry(
                title="iDM Wärmepumpe",
                data=user_input,
            )

        # Eingabeformular definieren
        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): int,
        })

        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    def async_get_options_flow(config_entry):
        """Verknüpft den OptionsFlow mit der Integration."""
        return IDMHeatpumpOptionsFlow(config_entry)


class IDMHeatpumpOptionsFlow(config_entries.OptionsFlow):
    """OptionsFlow für nachträgliche Änderungen der Integration."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """
        Erster Schritt der Optionen.

        Ermöglicht Änderungen am Update-Intervall,
        nachdem die Integration bereits eingerichtet wurde.
        """
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema({
            vol.Optional(
                CONF_UPDATE_INTERVAL,
                default=self.config_entry.options.get(
                    CONF_UPDATE_INTERVAL,
                    self.config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                ),
            ): int,
        })

        return self.async_show_form(step_id="init", data_schema=schema)
