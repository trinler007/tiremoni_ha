# SPDX-FileCopyrightText: 2026 Markus Trinler
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from custom_components.tiremoni_ble.parser import (  # noqa: E402
    BlePayload,
    TireMoniBleParser,
    TireMoniFrameAssembler,
    TyreReading,
    collect_payloads,
    decode_tiremoni_frame,
    format_payload_dump,
    is_likely_tiremoni_service_info,
)


@dataclass
class FakeDevice:
    name: str | None = None


@dataclass
class FakeServiceInfo:
    address: str = "AA:BB:CC:DD:EE:FF"
    name: str | None = None
    rssi: int | None = -63
    manufacturer_data: dict[int, bytes] | None = None
    service_data: dict[str, bytes] | None = None
    device: FakeDevice | None = None


class ParserTests(unittest.TestCase):
    def test_collect_payloads_includes_manufacturer_and_service_data(self) -> None:
        service_info = FakeServiceInfo(
            manufacturer_data={0x1234: b"\x01\x02"},
            service_data={"0000180f-0000-1000-8000-00805f9b34fb": b"\x64"},
        )

        payloads = collect_payloads(service_info)

        self.assertEqual(
            payloads,
            (
                BlePayload("manufacturer_data", 0x1234, b"\x01\x02"),
                BlePayload(
                    "service_data",
                    "0000180f-0000-1000-8000-00805f9b34fb",
                    b"\x64",
                ),
            ),
        )

    def test_likely_tiremoni_name_matches_gateway_names(self) -> None:
        self.assertTrue(is_likely_tiremoni_service_info(FakeServiceInfo(name="TireDog")))
        self.assertTrue(is_likely_tiremoni_service_info(FakeServiceInfo(name="TYREDOG")))
        self.assertTrue(
            is_likely_tiremoni_service_info(FakeServiceInfo(name="TireMoni BLE"))
        )

    def test_decode_tiremoni_frame(self) -> None:
        reading = decode_tiremoni_frame("$A00000802D4800#")

        assert reading is not None
        self.assertEqual(reading.sensor_id, "1")
        self.assertEqual(reading.position, "Sensor 1")
        self.assertEqual(reading.temperature_c, 32)
        self.assertEqual(reading.battery_percent, 100)
        self.assertEqual(reading.status, "ok")
        self.assertAlmostEqual(reading.pressure_psi, 45.2)
        self.assertAlmostEqual(reading.pressure_bar, 3.115)

    def test_decode_tiremoni_battery_low_half_point(self) -> None:
        reading = decode_tiremoni_frame("$A00000832D4800#")

        assert reading is not None
        self.assertEqual(reading.battery_percent, 20)
        self.assertEqual(reading.status, "battery_low")
        self.assertAlmostEqual(reading.pressure_psi, 45.6)
        self.assertAlmostEqual(reading.pressure_bar, 3.146)

    def test_decode_tiremoni_ignores_stale_frames(self) -> None:
        self.assertIsNone(decode_tiremoni_frame("$A00000002D4800#"))

    def test_frame_assembler_handles_fragments_and_noise(self) -> None:
        assembler = TireMoniFrameAssembler()

        self.assertEqual(assembler.feed(b"noise$A000"), ())
        readings = assembler.feed(b"00802D4800#tail")

        self.assertEqual(len(readings), 1)
        self.assertEqual(readings[0].sensor_id, "1")
        self.assertEqual(readings[0].temperature_c, 32)

    def test_parser_accepts_injected_decoder(self) -> None:
        def decoder(payload: BlePayload, service_info: FakeServiceInfo):
            self.assertEqual(service_info.address, "AA:BB:CC:DD:EE:FF")
            if payload.source != "manufacturer_data":
                return ()
            return (
                TyreReading(
                    sensor_id="123456",
                    position="front left",
                    pressure_bar=4.75,
                    temperature_c=32.0,
                ),
            )

        parser = TireMoniBleParser(decoders=(decoder,))
        update = parser.update(
            FakeServiceInfo(
                name="TireMoni",
                manufacturer_data={0x1234: b"\x01\x02"},
            )
        )

        self.assertEqual(update.gateway_name, "TireMoni")
        self.assertEqual(update.gateway_rssi, -63)
        self.assertEqual(len(update.readings), 1)
        self.assertEqual(update.readings[0].device_id, "tyre_123456")
        self.assertEqual(update.readings[0].pressure_bar, 4.75)

    def test_format_payload_dump(self) -> None:
        self.assertEqual(
            format_payload_dump((BlePayload("manufacturer_data", 1, b"\x0a"),)),
            ("manufacturer_data[1]=0a",),
        )


if __name__ == "__main__":
    unittest.main()
