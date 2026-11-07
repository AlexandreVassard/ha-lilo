"""The Prêt à Pousser Lilo integration."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import LiloConfigEntry, LiloCoordinator

PLATFORMS = [Platform.BUTTON, Platform.LIGHT, Platform.SELECT, Platform.TIME]


async def async_setup_entry(hass: HomeAssistant, entry: LiloConfigEntry) -> bool:
    """Set up a Lilo from a config entry."""
    coordinator = LiloCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: LiloConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
