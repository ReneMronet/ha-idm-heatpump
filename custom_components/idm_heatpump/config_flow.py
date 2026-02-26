"""
iDM Wärmepumpe (Modbus TCP)
Version: v5.0
Stand: 2026-02-26

Änderungen v5.0 (Schritt 2):
- Sensor-Gruppen-Auswahl in Schritt 2 (circuits) und Options-Flow
- Config-Version 3 (Migration v2→v3: sensor_groups mit Defaults hinzufügen)
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
    CONF_SENSOR_GROUPS,
    DEFAULT_SENSOR_GROUPS,
    ALL_SENSOR_GROUPS,
)

HEATING_CIRCUIT_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[
            {"value": "A", "label": "🏠 Heizkreis A"},
            {"value": "B", "label": "🏠 Heizkreis B"},
            {"value": "C", "label": "🏠 Heizkreis C"},
            {"value": "D", "label": "🏠 Heizkreis D"},
            {"value": "E", "label": "🏠 Heizkreis E"},
            {"value": "F", "label": "🏠 Heizkreis F"},
            {"value": "G", "label": "🏠 Heizkreis G"},
        ],
        multiple=True,
        mode=SelectSelectorMode.LIST,
    )
)

SENSOR_GROUP_LABELS_DE = {
    "solar": "☀️ Solar (Kollektor, Leistung, Betriebsart)",
    "pv_battery": "🔋 PV / Batterie (Überschuss, Produktion, SmartGrid, Strompreis)",
    "cooling": "❄️ Kühlung (Kühlanforderung, Kühlsollwerte pro HK)",
    "diagnostic": "🔧 Diagnose (Verdichter, EVU-Sperre, Ladepumpe, Ventile)",
    "room_control": "🌡️ Einzelraumregelung (Raumtemperatur pro HK, Feuchte)",
    "extended_temps": "📊 Erweiterte Temperaturen (Wärmesenke, Kältespeicher, Luftwärmetauscher)",
}

SENSOR_GROUP_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[
            {"value": key, "label": label}
            for key, label in SENSOR_GROUP_LABELS_DE.items()
        ],
        multiple=True,
        mode=SelectSelectorMode.LIST,
    )
)


class IDMHeatpumpConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 3

    def __init__(self):
        super().__init__()
        self._user_input = {}

    async def async_step_user(self, user_input=None):
        """Schritt 1: Verbindungsdaten."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)

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
        """Schritt 2: Heizkreise + Sensor-Gruppen auswählen."""
        if user_input is not None:
            selected_hc = user_input.get(CONF_HEATING_CIRCUITS, DEFAULT_HEATING_CIRCUITS)
            selected_sg = user_input.get(CONF_SENSOR_GROUPS, DEFAULT_SENSOR_GROUPS)
            self._user_input[CONF_HEATING_CIRCUITS] = selected_hc
            self._user_input[CONF_SENSOR_GROUPS] = selected_sg

            return self.async_create_entry(
                title="iDM W\u00e4rmepumpe",
                data=self._user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_HEATING_CIRCUITS,
                    default=DEFAULT_HEATING_CIRCUITS,
                ): HEATING_CIRCUIT_SELECTOR,
                vol.Required(
                    CONF_SENSOR_GROUPS,
                    default=DEFAULT_SENSOR_GROUPS,
                ): SENSOR_GROUP_SELECTOR,
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
        current_groups = self._entry.options.get(
            CONF_SENSOR_GROUPS,
            self._entry.data.get(CONF_SENSOR_GROUPS, DEFAULT_SENSOR_GROUPS),
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
                vol.Required(
                    CONF_SENSOR_GROUPS,
                    default=current_groups,
                ): SENSOR_GROUP_SELECTOR,
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=schema, errors=errors
        )
