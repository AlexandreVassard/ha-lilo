"""Grow light of the Lilo."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import LiloConfigEntry
from .entity import LiloEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LiloConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Lilo light."""
    async_add_entities([LiloLight(entry.runtime_data)])


class LiloLight(LiloEntity, LightEntity):
    """The grow light.

    "On" means enabled with a non-zero brightness: the Lilo itself still only
    lights up between the start and end times.
    """

    _attr_name = None
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "light")

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.brightness > 0

    @property
    def brightness(self) -> int:
        return round(self.coordinator.data.brightness * 255 / 100)

    async def async_turn_on(self, **kwargs: Any) -> None:
        if ATTR_BRIGHTNESS in kwargs:
            percent = max(1, round(kwargs[ATTR_BRIGHTNESS] * 100 / 255))
        else:
            percent = self.coordinator.last_brightness
        await self.coordinator.async_write(brightness=percent)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_write(brightness=0)
