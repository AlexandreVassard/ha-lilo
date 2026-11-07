"""Automatic or manual mode of the Lilo."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import LiloConfigEntry, LiloCoordinator
from .entity import LiloEntity
from .lilo import AUTO_BRIGHTNESS, AUTO_END, AUTO_START, MODE_AUTO, MODE_MANUAL

MODES = {"auto": MODE_AUTO, "manual": MODE_MANUAL}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LiloConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the mode select."""
    async_add_entities([LiloModeSelect(entry.runtime_data)])


class LiloModeSelect(LiloEntity, SelectEntity):
    """Mode select: automatic restores the app preset, manual keeps the settings."""

    _attr_translation_key = "mode"
    _attr_options = list(MODES)

    def __init__(self, coordinator: LiloCoordinator) -> None:
        super().__init__(coordinator, "mode")

    @property
    def current_option(self) -> str | None:
        mode = self.coordinator.data.mode
        return next((option for option, value in MODES.items() if value == mode), None)

    async def async_select_option(self, option: str) -> None:
        if option == "auto":
            await self.coordinator.async_write(
                mode=MODE_AUTO, brightness=AUTO_BRIGHTNESS, start=AUTO_START, end=AUTO_END
            )
        else:
            await self.coordinator.async_write(mode=MODE_MANUAL)
