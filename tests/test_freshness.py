from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from custom_components.tiremoni_ble.freshness import (  # noqa: E402
    data_is_current,
    oldest_reading_age_seconds,
    stale_sensor_ids,
)


class FreshnessTests(unittest.TestCase):
    def test_data_is_current_when_all_readings_are_younger_than_limit(self) -> None:
        now = datetime(2026, 6, 29, 12, 0, tzinfo=timezone.utc)

        self.assertTrue(
            data_is_current(
                ("1", "2"),
                {
                    "1": now - timedelta(minutes=10),
                    "2": now - timedelta(minutes=59),
                },
                now,
                60,
            )
        )

    def test_data_is_not_current_without_known_readings(self) -> None:
        now = datetime(2026, 6, 29, 12, 0, tzinfo=timezone.utc)

        self.assertFalse(data_is_current((), {}, now, 60))

    def test_stale_sensor_ids_include_old_and_missing_timestamps(self) -> None:
        now = datetime(2026, 6, 29, 12, 0, tzinfo=timezone.utc)

        self.assertEqual(
            stale_sensor_ids(
                ("1", "2", "3"),
                {
                    "1": now - timedelta(minutes=60),
                    "2": now - timedelta(minutes=15),
                },
                now,
                60,
            ),
            ("1", "3"),
        )

    def test_oldest_reading_age_seconds(self) -> None:
        now = datetime(2026, 6, 29, 12, 0, tzinfo=timezone.utc)

        self.assertEqual(
            oldest_reading_age_seconds(
                ("1", "2"),
                {
                    "1": now - timedelta(seconds=30),
                    "2": now - timedelta(seconds=90),
                },
                now,
            ),
            90,
        )


if __name__ == "__main__":
    unittest.main()
