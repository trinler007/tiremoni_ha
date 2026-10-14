# SPDX-FileCopyrightText: 2026 Markus Trinler
# SPDX-License-Identifier: GPL-3.0-or-later

"""Binary sensors for TireMoni BLE."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_MAX_DATA_AGE_MINUTES,
    DATA_CURRENT_KEY,
    DEFAULT_MAX_DATA_AGE_MINUTES,
    DOMAIN,
    MANUFACTURER,
)
from .coordinator import TireMoniDataUpdateCoordinator
from .freshness import data_is_current, oldest_reading_age_seconds, stale_sensor_ids

DESCRIPTION = BinarySensorEntityDescription(
    key=DATA_CURRENT_KEY,
    translation_key=DATA_CURRENT_KEY,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up TireMoni BLE binary sensors."""
    coordinator: TireMoniDataUpdateCoordinator = entry.runtime_data
    async_add_entities([TireMoniDataCurrentBinarySensor(coordinator, entry)])


class TireMoniDataCurrentBinarySensor(
    CoordinatorEntity[TireMoniDataUpdateCoordinator],
    BinarySensorEntity,
):
    """Indicate whether the latest TireMoni readings are still current."""

    _attr_has_entity_name = True
    entity_description = DESCRIPTION

    def __init__(
        self,
        coordinator: TireMoniDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{coordinator.address}_{DATA_CURRENT_KEY}"

    @property
    def name(self) -> str:
        """Return the entity name."""
        return "Data current"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for this entity."""
        data = self.coordinator.data
        return {
            "connections": {(CONNECTION_BLUETOOTH, self.coordinator.address)},
            "identifiers": {(DOMAIN, self.coordinator.address)},
            "manufacturer": MANUFACTURER,
            "name": data.gateway_name
            if data
            else self.coordinator.gateway_name or "TireMoni BLE gateway",
        }

    @property
    def is_on(self) -> bool:
        """Return True when all known tyre readings are younger than the limit."""
        data = self.coordinator.data
        if data is None:
            return False

        sensor_ids = tuple(reading.sensor_id for reading in data.readings)
        return data_is_current(
            sensor_ids,
            data.reading_last_seen,
            datetime.now(timezone.utc),
            self._max_age_minutes,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return details about reading freshness."""
        data = self.coordinator.data
        if data is None:
            return {"max_age_minutes": self._max_age_minutes}

        now = datetime.now(timezone.utc)
        sensor_ids = tuple(reading.sensor_id for reading in data.readings)
        stale_ids = stale_sensor_ids(
            sensor_ids,
            data.reading_last_seen,
            now,
            self._max_age_minutes,
        )
        oldest_age = oldest_reading_age_seconds(
            sensor_ids,
            data.reading_last_seen,
            now,
        )

        return {
            "max_age_minutes": self._max_age_minutes,
            "known_sensors": len(sensor_ids),
            "stale_sensors": list(stale_ids),
            "oldest_reading_age_seconds": oldest_age,
            "last_seen": {
                sensor_id: data.reading_last_seen[sensor_id].isoformat()
                for sensor_id in sorted(sensor_ids)
                if sensor_id in data.reading_last_seen
            },
        }

    @property
    def _max_age_minutes(self) -> int:
        """Return the configured max reading age in minutes."""
        return int(
            self._entry.options.get(
                CONF_MAX_DATA_AGE_MINUTES,
                DEFAULT_MAX_DATA_AGE_MINUTES,
            )
        )
