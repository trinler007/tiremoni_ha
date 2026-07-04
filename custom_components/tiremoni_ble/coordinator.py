"""Data coordinator for TireMoni BLE."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from logging import Logger

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import TireMoniClientError, read_tiremoni_device
from .const import DEFAULT_POLL_INTERVAL_SECONDS, DOMAIN
from .parser import TyreReading


@dataclass(frozen=True, slots=True)
class TireMoniData:
    """Latest TireMoni gateway state."""

    gateway_address: str
    gateway_name: str | None
    gateway_rssi: int | None
    readings: tuple[TyreReading, ...]
    reading_last_seen: dict[str, datetime]


class TireMoniDataUpdateCoordinator(DataUpdateCoordinator[TireMoniData]):
    """Poll TireMoni / TyreDog readings through an active BLE connection."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: Logger,
        address: str,
        name: str | None,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_POLL_INTERVAL_SECONDS),
        )
        self.address = address
        self.gateway_name = name
        self._logger = logger

    async def _async_update_data(self) -> TireMoniData:
        """Fetch one batch of TireMoni readings."""
        service_info = bluetooth.async_last_service_info(
            self.hass, self.address, connectable=True
        )
        gateway_rssi = service_info.rssi if service_info else None
        gateway_name = (
            self.gateway_name
            or (service_info.name if service_info else None)
            or self.address
        )

        try:
            result = await read_tiremoni_device(
                self.hass,
                self.address,
                name=gateway_name,
            )
        except TireMoniClientError as err:
            if self.data is not None:
                self._logger.debug(
                    "Keeping previous TireMoni readings after update failure: %s",
                    err,
                )
                return TireMoniData(
                    gateway_address=self.address,
                    gateway_name=gateway_name,
                    gateway_rssi=gateway_rssi,
                    readings=self.data.readings,
                    reading_last_seen=dict(self.data.reading_last_seen),
                )
            raise UpdateFailed(str(err)) from err

        if result.gateway_name:
            gateway_name = result.gateway_name
            self.gateway_name = result.gateway_name

        readings_by_sensor = {
            reading.sensor_id: reading
            for reading in (self.data.readings if self.data else ())
        }
        readings_by_sensor.update(
            {reading.sensor_id: reading for reading in result.readings}
        )
        reading_last_seen = (
            dict(self.data.reading_last_seen) if self.data is not None else {}
        )
        now = datetime.now(timezone.utc)
        for reading in result.readings:
            reading_last_seen[reading.sensor_id] = now

        return TireMoniData(
            gateway_address=self.address,
            gateway_name=gateway_name,
            gateway_rssi=gateway_rssi,
            readings=tuple(
                readings_by_sensor[sensor_id]
                for sensor_id in sorted(readings_by_sensor)
            ),
            reading_last_seen=reading_last_seen,
        )
