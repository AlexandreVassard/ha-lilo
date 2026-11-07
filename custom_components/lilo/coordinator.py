"""Coordinator for the Lilo integration."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, time, timedelta
import logging

from bleak.exc import BleakError

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_REFRESH_AT,
    DAILY_REFRESH_DELAY,
    DEFAULT_BRIGHTNESS,
    DEFAULT_REFRESH_AT,
    DOMAIN,
    REFRESH_AT_START,
)
from .lilo import LiloDevice, LiloState

_LOGGER = logging.getLogger(__name__)

type LiloConfigEntry = ConfigEntry[LiloCoordinator]


class LiloCoordinator(DataUpdateCoordinator[LiloState]):
    """Talks to the Lilo as rarely as possible: its LEDs blink on every connection.

    Besides writes and manual refreshes, it reads the Lilo (and resyncs its
    clock) once a day, right after the light turns on or off.
    """

    config_entry: LiloConfigEntry

    def __init__(self, hass: HomeAssistant, entry: LiloConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{entry.data[CONF_ADDRESS]}",
        )
        self.address: str = entry.data[CONF_ADDRESS]
        self.device = LiloDevice(entry.title)
        # Brightness restored by a plain "turn on".
        self.last_brightness = DEFAULT_BRIGHTNESS
        self._unsub_daily: Callable[[], None] | None = None
        entry.async_on_unload(self._cancel_daily_refresh)

    def _ble_device(self):
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if ble_device is None:
            raise UpdateFailed(f"Lilo {self.address} is out of Bluetooth range")
        return ble_device

    def _remember(self, state: LiloState) -> LiloState:
        if state.brightness:
            self.last_brightness = state.brightness
        self._schedule_daily_refresh(state)
        return state

    def _cancel_daily_refresh(self) -> None:
        if self._unsub_daily:
            self._unsub_daily()
            self._unsub_daily = None

    def _schedule_daily_refresh(self, state: LiloState) -> None:
        self._cancel_daily_refresh()
        refresh_at = self.config_entry.options.get(CONF_REFRESH_AT, DEFAULT_REFRESH_AT)
        anchor = state.start if refresh_at == REFRESH_AT_START else state.end
        now = dt_util.now()
        when = datetime.combine(now.date(), anchor, now.tzinfo) + DAILY_REFRESH_DELAY
        while when <= now:
            when += timedelta(days=1)
        _LOGGER.debug("Next daily refresh of %s at %s", self.address, when)
        self._unsub_daily = async_track_point_in_time(
            self.hass, self._async_daily_refresh, when
        )

    async def _async_daily_refresh(self, _now: datetime) -> None:
        self._unsub_daily = None
        await self.async_refresh()
        if self._unsub_daily is None and self.data is not None:
            # The refresh failed: try again tomorrow.
            self._schedule_daily_refresh(self.data)

    async def _async_update_data(self) -> LiloState:
        ble_device = self._ble_device()
        try:
            return self._remember(
                await self.device.update(ble_device, now=dt_util.now().time())
            )
        except (BleakError, TimeoutError) as err:
            raise UpdateFailed(f"Cannot read Lilo {self.address}: {err}") from err

    async def async_write(
        self,
        *,
        mode: int | None = None,
        brightness: int | None = None,
        start: time | None = None,
        end: time | None = None,
    ) -> None:
        """Write settings to the Lilo and publish the new state."""
        try:
            state = await self.device.write(
                self._ble_device(),
                now=dt_util.now().time(),
                mode=mode,
                brightness=brightness,
                start=start,
                end=end,
            )
        except (UpdateFailed, BleakError, TimeoutError) as err:
            raise HomeAssistantError(f"Cannot write to Lilo {self.address}: {err}") from err
        self.async_set_updated_data(self._remember(state))
