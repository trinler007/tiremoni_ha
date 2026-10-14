# SPDX-FileCopyrightText: 2026 Markus Trinler
# SPDX-License-Identifier: GPL-3.0-or-later
# Python port of the OpenMQTTGateway TireMoni decoder and frame assembler.
# See NOTICE.md for provenance and upstream attribution.

"""Parser helpers for TireMoni / TireDog / TyreDog Bluetooth data.

This module intentionally has no Home Assistant imports. Keep the NUS frame
mapping here so it can be unit-tested without starting Home Assistant.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
import re
from typing import Any, Literal

from .const import (
    BRAND_NAME,
    DEFAULT_PRESSURE_OFFSET_PSI,
    DEFAULT_PRESSURE_SCALE,
    MANUFACTURER,
)

PayloadSource = Literal["manufacturer_data", "service_data"]
Decoder = Callable[["BlePayload", Any], Iterable["TyreReading"]]

_LIKELY_NAME_PATTERNS = ("tiremoni", "tiredog", "tyredog", "tpms")


@dataclass(frozen=True, slots=True)
class BlePayload:
    """A raw BLE payload from advertisement debugging."""

    source: PayloadSource
    identifier: int | str
    data: bytes


@dataclass(frozen=True, slots=True)
class TyreReading:
    """A decoded tyre sensor reading."""

    sensor_id: str
    position: str | None = None
    pressure_psi: float | None = None
    pressure_bar: float | None = None
    temperature_c: float | None = None
    battery_percent: int | None = None
    status: str | None = None

    @property
    def device_id(self) -> str:
        """Return a stable processor-local device id."""
        normalized = re.sub(r"[^a-z0-9_]+", "_", self.sensor_id.lower()).strip("_")
        return f"tyre_{normalized or 'unknown'}"

    @property
    def device_name(self) -> str:
        """Return a friendly tyre device name."""
        if self.position:
            return f"{BRAND_NAME} {self.position}"
        return f"{BRAND_NAME} tyre {self.sensor_id}"


@dataclass(frozen=True, slots=True)
class TireMoniUpdate:
    """Parsed data from one TireMoni BLE advertisement debug payload."""

    gateway_address: str
    gateway_name: str | None
    gateway_rssi: int | None
    readings: tuple[TyreReading, ...]
    raw_payloads: tuple[BlePayload, ...]


class TireMoniBleParser:
    """Decode TireMoni / TireDog BLE advertisement debug payloads."""

    def __init__(self, decoders: Iterable[Decoder] | None = None) -> None:
        """Initialize the parser."""
        self._decoders = tuple(decoders or (_decode_tiremoni_payload,))

    def update(self, service_info: Any) -> TireMoniUpdate:
        """Parse a BluetoothServiceInfo-like object."""
        raw_payloads = collect_payloads(service_info)
        readings: list[TyreReading] = []

        for payload in raw_payloads:
            for decoder in self._decoders:
                readings.extend(decoder(payload, service_info))

        return TireMoniUpdate(
            gateway_address=getattr(service_info, "address", ""),
            gateway_name=getattr(service_info, "name", None),
            gateway_rssi=getattr(service_info, "rssi", None),
            readings=tuple(readings),
            raw_payloads=raw_payloads,
        )


def collect_payloads(service_info: Any) -> tuple[BlePayload, ...]:
    """Collect manufacturer and service-data payloads from service info."""
    payloads: list[BlePayload] = []

    manufacturer_data = getattr(service_info, "manufacturer_data", {}) or {}
    for company_id, data in manufacturer_data.items():
        payloads.append(
            BlePayload(
                source="manufacturer_data",
                identifier=int(company_id),
                data=bytes(data),
            )
        )

    service_data = getattr(service_info, "service_data", {}) or {}
    for service_uuid, data in service_data.items():
        payloads.append(
            BlePayload(
                source="service_data",
                identifier=str(service_uuid),
                data=bytes(data),
            )
        )

    return tuple(payloads)


def is_likely_tiremoni_service_info(service_info: Any) -> bool:
    """Return True if service info looks like a TireMoni / TireDog gateway."""
    names = {
        str(value).lower()
        for value in (
            getattr(service_info, "name", None),
            getattr(getattr(service_info, "device", None), "name", None),
            getattr(service_info, "local_name", None),
        )
        if value
    }

    if any(pattern in name for pattern in _LIKELY_NAME_PATTERNS for name in names):
        return True

    parser = TireMoniBleParser()
    return bool(parser.update(service_info).readings)


def format_payload_dump(payloads: Iterable[BlePayload]) -> tuple[str, ...]:
    """Format raw payloads for debug logging."""
    return tuple(
        f"{payload.source}[{payload.identifier}]={payload.data.hex()}"
        for payload in payloads
    )


def _decode_tiremoni_payload(
    payload: BlePayload, service_info: Any
) -> tuple[TyreReading, ...]:
    """Decode a TireMoni / TireDog payload if a full NUS frame is present.

    The TireMoni gateway normally exposes these frames through a connectable
    Nordic UART service, not advertisements. This hook still accepts full ASCII
    frames if they appear in service/manufacturer data during debugging.
    """
    return TireMoniFrameAssembler().feed(payload.data)


class TireMoniFrameAssembler:
    """Reassemble TireMoni NUS notification fragments into tyre readings."""

    def __init__(
        self,
        pressure_scale: float = DEFAULT_PRESSURE_SCALE,
        pressure_offset_psi: float = DEFAULT_PRESSURE_OFFSET_PSI,
    ) -> None:
        """Initialize the frame assembler."""
        self._buffer = ""
        self._pressure_scale = pressure_scale
        self._pressure_offset_psi = pressure_offset_psi

    def feed(self, data: bytes | str) -> tuple[TyreReading, ...]:
        """Feed one BLE notification fragment and return decoded readings."""
        if isinstance(data, bytes):
            self._buffer += data.decode("ascii", errors="ignore")
        else:
            self._buffer += data

        readings: list[TyreReading] = []

        while True:
            start = self._buffer.find("$A0")
            if start == -1:
                if len(self._buffer) > 128:
                    self._buffer = ""
                break

            if start > 0:
                self._buffer = self._buffer[start:]

            end = self._buffer.find("#")
            if end == -1:
                break

            frame = self._buffer[: end + 1]
            self._buffer = self._buffer[end + 1 :]

            if len(frame) != 16:
                continue

            if reading := decode_tiremoni_frame(
                frame,
                pressure_scale=self._pressure_scale,
                pressure_offset_psi=self._pressure_offset_psi,
            ):
                readings.append(reading)

        return tuple(readings)


def decode_tiremoni_frame(
    frame: str,
    pressure_scale: float = DEFAULT_PRESSURE_SCALE,
    pressure_offset_psi: float = DEFAULT_PRESSURE_OFFSET_PSI,
) -> TyreReading | None:
    """Decode one 16-character TireMoni ASCII frame.

    The mapping is ported from the OpenMQTTGateway TireMoni adaptation:

    - Frame format: ``$A0...........#`` with exactly 16 characters
    - Sensor number: hex nibble at offset 6, plus one
    - Flags: byte from offsets 7 and 8
    - Pressure: offsets 9, 10 and the high nibble at offset 11
    - Temperature: byte at offsets 11 and 12, minus 40 C
    """
    if len(frame) != 16 or not frame.startswith("$A0") or not frame.endswith("#"):
        return None

    try:
        sensor_no = int(frame[6], 16) + 1
        flags = (int(frame[7], 16) << 4) | int(frame[8], 16)
        raw_pressure_units = int(frame[9:11] + frame[11], 16)
        temp_c = int(frame[11:13], 16) - 40
    except ValueError:
        return None

    half_point = bool(flags & 0x01)
    battery_low = bool(flags & 0x02)
    rx_data_fresh = bool(flags & 0x80)
    if not rx_data_fresh:
        return None

    pressure_psi = raw_pressure_units / 14.5
    if half_point:
        pressure_psi += 0.5
    pressure_psi = pressure_psi * pressure_scale + pressure_offset_psi
    pressure_bar = pressure_psi * 0.0689476

    return TyreReading(
        sensor_id=str(sensor_no),
        position=f"Sensor {sensor_no}",
        pressure_psi=round(pressure_psi, 1),
        pressure_bar=round(pressure_bar, 3),
        temperature_c=temp_c,
        battery_percent=20 if battery_low else 100,
        status="battery_low" if battery_low else "ok",
    )


def gateway_device_info(update: TireMoniUpdate) -> dict[str, Any]:
    """Build the Home Assistant device info for the BLE gateway."""
    return {
        "identifiers": {("tiremoni_ble", update.gateway_address)},
        "manufacturer": MANUFACTURER,
        "name": update.gateway_name or f"{BRAND_NAME} BLE gateway",
    }
