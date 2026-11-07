"""Polling coordinator for the Lilo integration."""

from __future__ import annotations

from datetime import time
import logging

from bleak.exc import BleakError

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DEFAULT_BRIGHTNESS, DOMAIN, UPDATE_INTERVAL
from .lilo import LiloDevice, LiloState

_LOGGER = logging.getLogger(__name__)

type LiloConfigEntry = ConfigEntry[LiloCoordinator]


class LiloCoordinator(DataUpdateCoordinator[LiloState]):
    """Reads the Lilo every few minutes and forwards writes to it."""

    config_entry: LiloConfigEntry

    def __init__(self, hass: HomeAssistant, entry: LiloConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{entry.data[CONF_ADDRESS]}",
            update_interval=UPDATE_INTERVAL,
        )
        self.address: str = entry.data[CONF_ADDRESS]
        self.device = LiloDevice(entry.title)
        # Brightness restored by a plain "turn on".
        self.last_brightness = DEFAULT_BRIGHTNESS

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
        return state

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
                mode=mode,
                brightness=brightness,
                start=start,
                end=end,
            )
        except (UpdateFailed, BleakError, TimeoutError) as err:
            raise HomeAssistantError(f"Cannot write to Lilo {self.address}: {err}") from err
        self.async_set_updated_data(self._remember(state))
