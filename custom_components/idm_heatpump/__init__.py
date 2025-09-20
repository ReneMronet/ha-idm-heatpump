"""
__init__.py – v1.7 (2025-09-18)

Initialisierung der iDM Wärmepumpen Integration.
- Registriert die unterstützten Plattformen (Sensoren, Selects, Switches)
- Nutzt async_forward_entry_setups korrekt mit await (HA >= 2025.x)
"""

from homeassistant.const import Platform
from .const import DOMAIN

# Liste der Plattformen, die diese Integration bereitstellt
PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.SELECT,
    Platform.SWITCH,
]


async def async_setup_entry(hass, entry):
    """
    Wird beim Hinzufügen einer neuen iDM Wärmepumpe aufgerufen.
    Erstellt die Integration und leitet den Config-Entry an die Plattformen weiter.
    """
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"data": entry.data}

    # Plattformen asynchron, aber explizit awaiten → Sensoren/Selects/Switches werden sicher geladen
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass, entry):
    """
    Wird beim Entfernen einer iDM Wärmepumpe aufgerufen.
    Lädt die Plattformen wieder aus und entfernt die Daten aus hass.data.
    """
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
