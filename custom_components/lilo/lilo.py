"""BLE client for the Prêt à Pousser Lilo (firmware exposing service c9d9bfe1).

Protocol, reverse-engineered from the official app:

    e2      clock, seconds since local midnight (uint32 LE, read/write/notify)
    e4      mode (uint8): 0xc3 manual, 0xb2 automatic
    e5, e6  light brightness, 0-100 (uint8); 0 means "off"
    e7, e8  daily light start, seconds since midnight (uint32 LE)
    e9, ea  daily light end, seconds since midnight (uint32 LE)

Each setting is stored twice (e5/e6, e7/e8, e9/ea); the app always writes
both, so this client does the same.

In automatic mode the Lilo restores its own schedule once disconnected, so a
schedule change only sticks in manual mode.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import time
import logging

from bleak.backends.device import BLEDevice
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

_LOGGER = logging.getLogger(__name__)


def _uuid(short: str) -> str:
    return f"c9d9bf{short}-324c-4b79-bbaf-8a473e6540ec"


SERVICE_UUID = _uuid("e1")
CHAR_CLOCK = _uuid("e2")
CHAR_MODE = _uuid("e4")
CHARS_BRIGHTNESS = (_uuid("e5"), _uuid("e6"))
CHARS_START = (_uuid("e7"), _uuid("e8"))
CHARS_END = (_uuid("e9"), _uuid("ea"))

MODE_MANUAL = 0xC3
MODE_AUTO = 0xB2

# Settings the app applies along with the automatic mode.
AUTO_BRIGHTNESS = 100
AUTO_START = time(6, 0)
AUTO_END = time(22, 0)

# Tolerated drift between the Lilo clock and Home Assistant before resyncing.
CLOCK_TOLERANCE = 60


def _seconds_to_time(value: int) -> time:
    value %= 86400
    return time(value // 3600, value % 3600 // 60, value % 60)


def _time_to_seconds(value: time) -> int:
    return value.hour * 3600 + value.minute * 60 + value.second


@dataclass(frozen=True)
class LiloState:
    """Snapshot of the Lilo settings."""

    mode: int
    brightness: int
    start: time
    end: time
    clock: time


class LiloDevice:
    """Short-lived connections to a Lilo, so the official app keeps working."""

    def __init__(self, name: str) -> None:
        self._name = name
        self._lock = asyncio.Lock()

    async def _connect(self, ble_device: BLEDevice) -> BleakClientWithServiceCache:
        return await establish_connection(
            BleakClientWithServiceCache, ble_device, self._name, max_attempts=3
        )

    async def update(self, ble_device: BLEDevice, now: time | None = None) -> LiloState:
        """Read the settings, resyncing the Lilo clock to ``now`` if it drifted."""
        async with self._lock:
            client = await self._connect(ble_device)
            try:
                if now is not None:
                    clock = int.from_bytes(await client.read_gatt_char(CHAR_CLOCK), "little")
                    drift = abs(clock - _time_to_seconds(now))
                    if min(drift, 86400 - drift) > CLOCK_TOLERANCE:
                        _LOGGER.debug("Resyncing %s clock (drift %ss)", self._name, drift)
                        await client.write_gatt_char(
                            CHAR_CLOCK, _time_to_seconds(now).to_bytes(4, "little"), response=True
                        )
                return await self._read(client)
            finally:
                await client.disconnect()

    async def write(
        self,
        ble_device: BLEDevice,
        *,
        mode: int | None = None,
        brightness: int | None = None,
        start: time | None = None,
        end: time | None = None,
    ) -> LiloState:
        """Write the given settings and return the resulting state.

        Changing the schedule switches to manual mode unless ``mode`` is given.
        """
        if mode is None and (start is not None or end is not None):
            mode = MODE_MANUAL

        payloads: list[tuple[tuple[str, ...], bytes]] = []
        if mode is not None:
            payloads.append(((CHAR_MODE,), bytes([mode])))
        if brightness is not None:
            payloads.append((CHARS_BRIGHTNESS, bytes([max(0, min(100, brightness))])))
        if start is not None:
            payloads.append((CHARS_START, _time_to_seconds(start).to_bytes(4, "little")))
        if end is not None:
            payloads.append((CHARS_END, _time_to_seconds(end).to_bytes(4, "little")))

        async with self._lock:
            client = await self._connect(ble_device)
            try:
                for chars, data in payloads:
                    for char in chars:
                        await client.write_gatt_char(char, data, response=True)
                return await self._read(client)
            finally:
                await client.disconnect()

    async def _read(self, client: BleakClientWithServiceCache) -> LiloState:
        async def read_int(char: str) -> int:
            return int.from_bytes(await client.read_gatt_char(char), "little")

        return LiloState(
            mode=await read_int(CHAR_MODE),
            brightness=await read_int(CHARS_BRIGHTNESS[0]),
            start=_seconds_to_time(await read_int(CHARS_START[0])),
            end=_seconds_to_time(await read_int(CHARS_END[0])),
            clock=_seconds_to_time(await read_int(CHAR_CLOCK)),
        )
