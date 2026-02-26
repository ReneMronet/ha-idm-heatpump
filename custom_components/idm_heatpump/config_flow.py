"""
iDM Wärmepumpe (Modbus TCP)
Version: v0.7.0
Stand: 2026-02-26

Änderungen v0.7.0:
- Schreib-Intervall: "Deaktiviert" als Standard
- Config-Version 5

Änderungen v0.6.0:
- Schritt 3a: Raumtemperatur-Übernahme (Entity-Picker, Intervall, Saison-Toggle)
- Schritt 3b: Saison-Zeitraum (nur wenn Saison-Toggle aktiv)
- Options-Flow: 3-stufig (Verbindung/Gruppen → Raumtemperatur → Saison)
- Config-Version 4
"""

import socket
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
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
    CONF_ROOM_TEMP_ENTITIES,
    CONF_ROOM_TEMP_INTERVAL,
    CONF_ROOM_TEMP_SEASON_ENABLED,
    CONF_ROOM_TEMP_SEASON_START_MONTH,
    CONF_ROOM_TEMP_SEASON_START_DAY,
    CONF_ROOM_TEMP_SEASON_END_MONTH,
    CONF_ROOM_TEMP_SEASON_END_DAY,
    DEFAULT_ROOM_TEMP_ENTITIES,
    DEFAULT_ROOM_TEMP_INTERVAL,
    DEFAULT_ROOM_TEMP_SEASON_ENABLED,
    DEFAULT_ROOM_TEMP_SEASON_START_MONTH,
    DEFAULT_ROOM_TEMP_SEASON_START_DAY,
    DEFAULT_ROOM_TEMP_SEASON_END_MONTH,
    DEFAULT_ROOM_TEMP_SEASON_END_DAY,
    ROOM_TEMP_INTERVAL_OPTIONS,
)

# -------------------------------------------------------------------
# Selektoren
# -------------------------------------------------------------------

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

TEMP_ENTITY_SELECTOR = EntitySelector(
    EntitySelectorConfig(
        domain="sensor",
        device_class="temperature",
    )
)

ROOM_TEMP_INTERVAL_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[
            {"value": key, "label": label}
            for key, label in ROOM_TEMP_INTERVAL_OPTIONS.items()
        ],
        multiple=False,
        mode=SelectSelectorMode.DROPDOWN,
    )
)

MONTH_SELECTOR = NumberSelector(
    NumberSelectorConfig(min=1, max=12, step=1, mode=NumberSelectorMode.BOX)
)

DAY_SELECTOR = NumberSelector(
    NumberSelectorConfig(min=1, max=31, step=1, mode=NumberSelectorMode.BOX)
)


# -------------------------------------------------------------------
# Schema-Builder
# -------------------------------------------------------------------

def _build_room_temp_schema(
    heating_circuits: list[str],
    current_entities: dict,
    current_interval: str,
    current_season_enabled: bool,
) -> vol.Schema:
    """Schema für Schritt 3a: Sensoren, Intervall, Saison-Toggle."""
    fields = {}

    # Entity-Picker pro aktivem Heizkreis
    for hc in sorted(heating_circuits):
        key = f"room_temp_{hc.lower()}"
        current = current_entities.get(hc, "")
        fields[vol.Optional(key, default=current)] = TEMP_ENTITY_SELECTOR

    # Schreib-Intervall
    fields[vol.Required(
        CONF_ROOM_TEMP_INTERVAL,
        default=current_interval,
    )] = ROOM_TEMP_INTERVAL_SELECTOR

    # Saisonale Automatik (nur Toggle)
    fields[vol.Required(
        CONF_ROOM_TEMP_SEASON_ENABLED,
        default=current_season_enabled,
    )] = BooleanSelector()

    return vol.Schema(fields)


def _build_season_schema(
    current_start_month: int,
    current_start_day: int,
    current_end_month: int,
    current_end_day: int,
) -> vol.Schema:
    """Schema für Schritt 3b: Saison-Zeitraum (nur wenn Toggle aktiv)."""
    return vol.Schema({
        vol.Required(
            CONF_ROOM_TEMP_SEASON_START_MONTH,
            default=current_start_month,
        ): MONTH_SELECTOR,
        vol.Required(
            CONF_ROOM_TEMP_SEASON_START_DAY,
            default=current_start_day,
        ): DAY_SELECTOR,
        vol.Required(
            CONF_ROOM_TEMP_SEASON_END_MONTH,
            default=current_end_month,
        ): MONTH_SELECTOR,
        vol.Required(
            CONF_ROOM_TEMP_SEASON_END_DAY,
            default=current_end_day,
        ): DAY_SELECTOR,
    })


def _extract_room_temp_entities(user_input: dict, heating_circuits: list[str]) -> dict:
    """Extrahiert die Entity-Zuordnungen aus dem Formular-Input."""
    entities = {}
    for hc in heating_circuits:
        key = f"room_temp_{hc.lower()}"
        entity_id = user_input.get(key, "")
        if entity_id:
            entities[hc] = entity_id
    return entities


def _store_room_temp_input(target: dict, user_input: dict, heating_circuits: list[str]):
    """Speichert Raumtemperatur-Daten aus Schritt 3a in target dict."""
    target[CONF_ROOM_TEMP_ENTITIES] = _extract_room_temp_entities(
        user_input, heating_circuits
    )
    target[CONF_ROOM_TEMP_INTERVAL] = user_input.get(
        CONF_ROOM_TEMP_INTERVAL, DEFAULT_ROOM_TEMP_INTERVAL
    )
    target[CONF_ROOM_TEMP_SEASON_ENABLED] = user_input.get(
        CONF_ROOM_TEMP_SEASON_ENABLED, DEFAULT_ROOM_TEMP_SEASON_ENABLED
    )


def _store_season_input(target: dict, user_input: dict):
    """Speichert Saison-Daten aus Schritt 3b in target dict."""
    target[CONF_ROOM_TEMP_SEASON_START_MONTH] = int(user_input.get(
        CONF_ROOM_TEMP_SEASON_START_MONTH, DEFAULT_ROOM_TEMP_SEASON_START_MONTH
    ))
    target[CONF_ROOM_TEMP_SEASON_START_DAY] = int(user_input.get(
        CONF_ROOM_TEMP_SEASON_START_DAY, DEFAULT_ROOM_TEMP_SEASON_START_DAY
    ))
    target[CONF_ROOM_TEMP_SEASON_END_MONTH] = int(user_input.get(
        CONF_ROOM_TEMP_SEASON_END_MONTH, DEFAULT_ROOM_TEMP_SEASON_END_MONTH
    ))
    target[CONF_ROOM_TEMP_SEASON_END_DAY] = int(user_input.get(
        CONF_ROOM_TEMP_SEASON_END_DAY, DEFAULT_ROOM_TEMP_SEASON_END_DAY
    ))


def _store_season_defaults(target: dict):
    """Schreibt Saison-Defaults wenn Saison deaktiviert."""
    target[CONF_ROOM_TEMP_SEASON_START_MONTH] = DEFAULT_ROOM_TEMP_SEASON_START_MONTH
    target[CONF_ROOM_TEMP_SEASON_START_DAY] = DEFAULT_ROOM_TEMP_SEASON_START_DAY
    target[CONF_ROOM_TEMP_SEASON_END_MONTH] = DEFAULT_ROOM_TEMP_SEASON_END_MONTH
    target[CONF_ROOM_TEMP_SEASON_END_DAY] = DEFAULT_ROOM_TEMP_SEASON_END_DAY


# ===================================================================
# Config Flow (Ersteinrichtung)
# ===================================================================

class IDMHeatpumpConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 5

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
            return await self.async_step_room_temp()

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

    async def async_step_room_temp(self, user_input=None):
        """Schritt 3a: Raumtemperatur-Übernahme (Sensoren, Intervall, Saison-Toggle)."""
        heating_circuits = self._user_input.get(
            CONF_HEATING_CIRCUITS, DEFAULT_HEATING_CIRCUITS
        )

        if user_input is not None:
            _store_room_temp_input(self._user_input, user_input, heating_circuits)

            # Saison aktiviert → weiter zu Schritt 3b
            if self._user_input.get(CONF_ROOM_TEMP_SEASON_ENABLED, False):
                return await self.async_step_room_temp_season()

            # Saison deaktiviert → Defaults setzen und fertig
            _store_season_defaults(self._user_input)
            return self.async_create_entry(
                title="iDM W\u00e4rmepumpe",
                data=self._user_input,
            )

        schema = _build_room_temp_schema(
            heating_circuits=heating_circuits,
            current_entities=DEFAULT_ROOM_TEMP_ENTITIES,
            current_interval=DEFAULT_ROOM_TEMP_INTERVAL,
            current_season_enabled=DEFAULT_ROOM_TEMP_SEASON_ENABLED,
        )

        return self.async_show_form(
            step_id="room_temp", data_schema=schema, errors={}
        )

    async def async_step_room_temp_season(self, user_input=None):
        """Schritt 3b: Saison-Zeitraum (nur wenn Saison-Toggle aktiv)."""
        if user_input is not None:
            _store_season_input(self._user_input, user_input)
            return self.async_create_entry(
                title="iDM W\u00e4rmepumpe",
                data=self._user_input,
            )

        schema = _build_season_schema(
            current_start_month=DEFAULT_ROOM_TEMP_SEASON_START_MONTH,
            current_start_day=DEFAULT_ROOM_TEMP_SEASON_START_DAY,
            current_end_month=DEFAULT_ROOM_TEMP_SEASON_END_MONTH,
            current_end_day=DEFAULT_ROOM_TEMP_SEASON_END_DAY,
        )

        return self.async_show_form(
            step_id="room_temp_season", data_schema=schema, errors={}
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return IDMHeatpumpOptionsFlow(config_entry)


# ===================================================================
# Options Flow (nachträgliche Änderungen)
# ===================================================================

class IDMHeatpumpOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        super().__init__()
        self._entry = config_entry
        self._options = {}

    def _get(self, key, default=None):
        """Holt einen Wert aus options → data → default."""
        return self._entry.options.get(
            key, self._entry.data.get(key, default)
        )

    async def async_step_init(self, user_input=None):
        """Options Schritt 1: Verbindung, Heizkreise, Sensorgruppen."""
        errors = {}

        if user_input is not None:
            host = user_input.get(CONF_HOST, self._get(CONF_HOST, "0.0.0.0"))
            port = user_input.get(CONF_PORT, self._get(CONF_PORT, DEFAULT_PORT))

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
                self._options = dict(user_input)
                return await self.async_step_room_temp()

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_HOST, default=self._get(CONF_HOST, "0.0.0.0"),
                ): str,
                vol.Optional(
                    CONF_PORT, default=self._get(CONF_PORT, DEFAULT_PORT),
                ): int,
                vol.Optional(
                    CONF_UNIT_ID, default=self._get(CONF_UNIT_ID, DEFAULT_UNIT_ID),
                ): int,
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=self._get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                ): int,
                vol.Required(
                    CONF_HEATING_CIRCUITS,
                    default=self._get(CONF_HEATING_CIRCUITS, DEFAULT_HEATING_CIRCUITS),
                ): HEATING_CIRCUIT_SELECTOR,
                vol.Required(
                    CONF_SENSOR_GROUPS,
                    default=self._get(CONF_SENSOR_GROUPS, DEFAULT_SENSOR_GROUPS),
                ): SENSOR_GROUP_SELECTOR,
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=schema, errors=errors
        )

    async def async_step_room_temp(self, user_input=None):
        """Options Schritt 2: Raumtemperatur-Übernahme."""
        heating_circuits = self._options.get(
            CONF_HEATING_CIRCUITS,
            self._get(CONF_HEATING_CIRCUITS, DEFAULT_HEATING_CIRCUITS),
        )

        if user_input is not None:
            _store_room_temp_input(self._options, user_input, heating_circuits)

            # Saison aktiviert → weiter zu Schritt 3
            if self._options.get(CONF_ROOM_TEMP_SEASON_ENABLED, False):
                return await self.async_step_room_temp_season()

            # Saison deaktiviert → Defaults setzen und fertig
            _store_season_defaults(self._options)
            return self.async_create_entry(title="", data=self._options)

        current_entities = self._get(CONF_ROOM_TEMP_ENTITIES, DEFAULT_ROOM_TEMP_ENTITIES)

        schema = _build_room_temp_schema(
            heating_circuits=heating_circuits,
            current_entities=current_entities,
            current_interval=self._get(CONF_ROOM_TEMP_INTERVAL, DEFAULT_ROOM_TEMP_INTERVAL),
            current_season_enabled=self._get(
                CONF_ROOM_TEMP_SEASON_ENABLED, DEFAULT_ROOM_TEMP_SEASON_ENABLED
            ),
        )

        return self.async_show_form(
            step_id="room_temp", data_schema=schema, errors={}
        )

    async def async_step_room_temp_season(self, user_input=None):
        """Options Schritt 3: Saison-Zeitraum (nur wenn Toggle aktiv)."""
        if user_input is not None:
            _store_season_input(self._options, user_input)
            return self.async_create_entry(title="", data=self._options)

        schema = _build_season_schema(
            current_start_month=self._get(
                CONF_ROOM_TEMP_SEASON_START_MONTH, DEFAULT_ROOM_TEMP_SEASON_START_MONTH
            ),
            current_start_day=self._get(
                CONF_ROOM_TEMP_SEASON_START_DAY, DEFAULT_ROOM_TEMP_SEASON_START_DAY
            ),
            current_end_month=self._get(
                CONF_ROOM_TEMP_SEASON_END_MONTH, DEFAULT_ROOM_TEMP_SEASON_END_MONTH
            ),
            current_end_day=self._get(
                CONF_ROOM_TEMP_SEASON_END_DAY, DEFAULT_ROOM_TEMP_SEASON_END_DAY
            ),
        )

        return self.async_show_form(
            step_id="room_temp_season", data_schema=schema, errors={}
        )
