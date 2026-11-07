"""Daily light schedule of the Lilo."""

from __future__ import annotations

from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import LiloConfigEntry, LiloCoordinator
from .entity import LiloEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LiloConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the light schedule entities."""
    coordinator = entry.runtime_data
    async_add_entities([LiloTime(coordinator, "start"), LiloTime(coordinator, "end")])


class LiloTime(LiloEntity, TimeEntity):
    """Time of day the light turns on ("start") or off ("end")."""

    def __init__(self, coordinator: LiloCoordinator, key: str) -> None:
        super().__init__(coordinator, key)
        self._key = key
        self._attr_translation_key = key

    @property
    def native_value(self) -> time:
        return getattr(self.coordinator.data, self._key)

    async def async_set_value(self, value: time) -> None:
        await self.coordinator.async_write(**{self._key: value})
