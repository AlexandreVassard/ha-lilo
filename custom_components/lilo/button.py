"""Manual refresh of the Lilo."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import LiloConfigEntry, LiloCoordinator
from .entity import LiloEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LiloConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the refresh button."""
    async_add_entities([LiloRefreshButton(entry.runtime_data)])


class LiloRefreshButton(LiloEntity, ButtonEntity):
    """Reads the Lilo now, e.g. after a change made in the official app."""

    _attr_translation_key = "refresh"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: LiloCoordinator) -> None:
        super().__init__(coordinator, "refresh")

    async def async_press(self) -> None:
        await self.coordinator.async_refresh()
