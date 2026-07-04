"""Freshness helpers for TireMoni BLE readings."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timedelta


def stale_sensor_ids(
    sensor_ids: Iterable[str],
    last_seen_by_sensor: Mapping[str, datetime],
    now: datetime,
    max_age_minutes: int,
) -> tuple[str, ...]:
    """Return sensor ids whose latest reading is older than the configured age."""
    cutoff = now - timedelta(minutes=max_age_minutes)
    return tuple(
        sensor_id
        for sensor_id in sorted(sensor_ids)
        if (last_seen := last_seen_by_sensor.get(sensor_id)) is None
        or last_seen <= cutoff
    )


def data_is_current(
    sensor_ids: Iterable[str],
    last_seen_by_sensor: Mapping[str, datetime],
    now: datetime,
    max_age_minutes: int,
) -> bool:
    """Return True when at least one reading exists and all readings are current."""
    sensor_id_tuple = tuple(sensor_ids)
    return bool(sensor_id_tuple) and not stale_sensor_ids(
        sensor_id_tuple,
        last_seen_by_sensor,
        now,
        max_age_minutes,
    )


def oldest_reading_age_seconds(
    sensor_ids: Iterable[str],
    last_seen_by_sensor: Mapping[str, datetime],
    now: datetime,
) -> int | None:
    """Return the age in seconds of the oldest known reading."""
    timestamps = [
        last_seen_by_sensor[sensor_id]
        for sensor_id in sensor_ids
        if sensor_id in last_seen_by_sensor
    ]
    if not timestamps:
        return None

    oldest = min(timestamps)
    return max(0, int((now - oldest).total_seconds()))
