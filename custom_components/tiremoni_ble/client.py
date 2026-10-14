# SPDX-FileCopyrightText: 2026 Markus Trinler
# SPDX-License-Identifier: GPL-3.0-or-later
# BLE command sequence from Markus Trinler's own TireMoni extension for
# OpenMQTTGateway 1.8.1, not from upstream. See NOTICE.md for provenance.

"""Active Bluetooth client for TireMoni BLE gateways."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass
import logging
from typing import Any

from bleak.exc import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant

from .const import (
    DEFAULT_NOTIFICATION_HOLD_SECONDS,
    TIREMONI_NUS_RX_UUID,
    TIREMONI_NUS_SERVICE_UUID,
    TIREMONI_NUS_TX_UUID,
    TIREMONI_START_COMMAND,
)
from .parser import TireMoniFrameAssembler, TyreReading

_LOGGER = logging.getLogger(__name__)


class TireMoniClientError(Exception):
    """Base error for TireMoni BLE client failures."""


class TireMoniDeviceNotFound(TireMoniClientError):
    """Raised when no connectable Bluetooth device is available."""


@dataclass(frozen=True, slots=True)
class TireMoniClientResult:
    """Result from one active TireMoni read session."""

    gateway_name: str | None
    readings: tuple[TyreReading, ...]


async def read_tiremoni_device(
    hass: HomeAssistant,
    address: str,
    name: str | None = None,
    hold_seconds: int = DEFAULT_NOTIFICATION_HOLD_SECONDS,
) -> TireMoniClientResult:
    """Connect to a TireMoni gateway, start NUS output and collect readings."""
    ble_device = bluetooth.async_ble_device_from_address(
        hass, address, connectable=True
    )
    if ble_device is None:
        raise TireMoniDeviceNotFound(
            f"No connectable Bluetooth path found for {address}"
        )

    gateway_name = ble_device.name or name
    connection_name = gateway_name or address
    assembler = TireMoniFrameAssembler()
    readings: list[TyreReading] = []

    def notification_handler(_sender: Any, data: bytearray) -> None:
        """Handle incoming NUS notification fragments."""
        decoded = assembler.feed(bytes(data))
        if decoded:
            readings.extend(decoded)

    client = await _establish_connection(ble_device, connection_name)
    try:
        try:
            await client.start_notify(TIREMONI_NUS_TX_UUID, notification_handler)
            try:
                await client.write_gatt_char(
                    TIREMONI_NUS_RX_UUID, TIREMONI_START_COMMAND, response=False
                )
            except BleakError:
                await client.write_gatt_char(
                    TIREMONI_NUS_RX_UUID, TIREMONI_START_COMMAND, response=True
                )

            await asyncio.sleep(hold_seconds)
            with suppress(Exception):
                await client.stop_notify(TIREMONI_NUS_TX_UUID)
        except BleakError as err:
            raise TireMoniClientError(
                f"Failed reading TireMoni data from {address}: {err}"
            ) from err
    finally:
        if client.is_connected:
            await client.disconnect()

    latest_by_sensor = {reading.sensor_id: reading for reading in readings}
    return TireMoniClientResult(
        gateway_name=gateway_name,
        readings=tuple(
            latest_by_sensor[sensor_id] for sensor_id in sorted(latest_by_sensor)
        ),
    )


async def _establish_connection(ble_device: Any, name: str) -> Any:
    """Establish a BLE connection through Home Assistant's Bluetooth stack."""
    try:
        try:
            return await establish_connection(
                BleakClientWithServiceCache,
                ble_device,
                name,
                services=[TIREMONI_NUS_SERVICE_UUID],
            )
        except TypeError:
            _LOGGER.debug(
                "Retrying TireMoni connection without service filter for compatibility"
            )
            return await establish_connection(
                BleakClientWithServiceCache,
                ble_device,
                name,
            )
    except BleakError as err:
        raise TireMoniClientError(f"Failed connecting to TireMoni device: {err}") from err
