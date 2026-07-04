"""Support for TireMoni BLE sensors."""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfPressure,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    BATTERY_PERCENT_KEY,
    DOMAIN,
    GATEWAY_RSSI_KEY,
    MANUFACTURER,
    PRESSURE_KEY,
    STATUS_KEY,
    TEMPERATURE_KEY,
)
from .coordinator import TireMoniData, TireMoniDataUpdateCoordinator
from .parser import TyreReading

_SensorValueType = str | int | float | None
_ValueGetter = Callable[[TireMoniData, str | None], _SensorValueType]


def _gateway_rssi(data: TireMoniData, sensor_id: str | None) -> _SensorValueType:
    """Return gateway RSSI."""
    return data.gateway_rssi


def _reading_value(
    data: TireMoniData,
    sensor_id: str | None,
    attr: str,
) -> _SensorValueType:
    """Return a value from a tyre reading."""
    if sensor_id is None:
        return None
    reading = _find_reading(data, sensor_id)
    return getattr(reading, attr, None) if reading else None


def _find_reading(data: TireMoniData, sensor_id: str) -> TyreReading | None:
    """Find a reading by sensor id."""
    return next(
        (reading for reading in data.readings if reading.sensor_id == sensor_id),
        None,
    )


SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    GATEWAY_RSSI_KEY: SensorEntityDescription(
        key=GATEWAY_RSSI_KEY,
        translation_key=GATEWAY_RSSI_KEY,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    PRESSURE_KEY: SensorEntityDescription(
        key=PRESSURE_KEY,
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.BAR,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    TEMPERATURE_KEY: SensorEntityDescription(
        key=TEMPERATURE_KEY,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BATTERY_PERCENT_KEY: SensorEntityDescription(
        key=BATTERY_PERCENT_KEY,
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    STATUS_KEY: SensorEntityDescription(
        key=STATUS_KEY,
        translation_key=STATUS_KEY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
}

ENTITY_NAMES = {
    GATEWAY_RSSI_KEY: "Gateway RSSI",
    PRESSURE_KEY: "Pressure",
    TEMPERATURE_KEY: "Temperature",
    BATTERY_PERCENT_KEY: "Battery",
    STATUS_KEY: "Status",
}

VALUE_GETTERS: dict[str, _ValueGetter] = {
    GATEWAY_RSSI_KEY: _gateway_rssi,
    PRESSURE_KEY: lambda data, sensor_id: _reading_value(
        data, sensor_id, "pressure_bar"
    ),
    TEMPERATURE_KEY: lambda data, sensor_id: _reading_value(
        data, sensor_id, "temperature_c"
    ),
    BATTERY_PERCENT_KEY: lambda data, sensor_id: _reading_value(
        data, sensor_id, "battery_percent"
    ),
    STATUS_KEY: lambda data, sensor_id: _reading_value(data, sensor_id, "status"),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up TireMoni BLE sensors."""
    coordinator: TireMoniDataUpdateCoordinator = entry.runtime_data
    known_entities: set[tuple[str | None, str]] = set()

    @callback
    def _async_add_missing_entities() -> None:
        """Add newly discovered tyre sensor entities."""
        data = coordinator.data
        if data is None:
            return

        entities: list[TireMoniSensorEntity] = []

        gateway_key = (None, GATEWAY_RSSI_KEY)
        if gateway_key not in known_entities:
            known_entities.add(gateway_key)
            entities.append(
                TireMoniSensorEntity(
                    coordinator,
                    None,
                    SENSOR_DESCRIPTIONS[GATEWAY_RSSI_KEY],
                )
            )

        for reading in data.readings:
            for sensor_key in (
                PRESSURE_KEY,
                TEMPERATURE_KEY,
                BATTERY_PERCENT_KEY,
                STATUS_KEY,
            ):
                if VALUE_GETTERS[sensor_key](data, reading.sensor_id) is None:
                    continue
                entity_key = (reading.sensor_id, sensor_key)
                if entity_key in known_entities:
                    continue
                known_entities.add(entity_key)
                entities.append(
                    TireMoniSensorEntity(
                        coordinator,
                        reading.sensor_id,
                        SENSOR_DESCRIPTIONS[sensor_key],
                    )
                )

        if entities:
            async_add_entities(entities)

    _async_add_missing_entities()
    entry.async_on_unload(coordinator.async_add_listener(_async_add_missing_entities))


class TireMoniSensorEntity(
    CoordinatorEntity[TireMoniDataUpdateCoordinator],
    SensorEntity,
):
    """Representation of a TireMoni BLE sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TireMoniDataUpdateCoordinator,
        sensor_id: str | None,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._sensor_id = sensor_id

        address = coordinator.address
        if sensor_id is None:
            self._attr_unique_id = f"{address}_{description.key}"
        else:
            self._attr_unique_id = f"{address}_sensor_{sensor_id}_{description.key}"

    @property
    def name(self) -> str:
        """Return the entity name."""
        return ENTITY_NAMES[self.entity_description.key]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for this entity."""
        data = self.coordinator.data
        gateway_name = (
            data.gateway_name
            if data
            else self.coordinator.gateway_name or "TireMoni BLE gateway"
        )

        if self._sensor_id is None or data is None:
            return {
                "connections": {(CONNECTION_BLUETOOTH, self.coordinator.address)},
                "identifiers": {(DOMAIN, self.coordinator.address)},
                "manufacturer": MANUFACTURER,
                "name": gateway_name,
            }

        reading = _find_reading(data, self._sensor_id)
        return {
            "identifiers": {
                (DOMAIN, f"{self.coordinator.address}_sensor_{self._sensor_id}")
            },
            "manufacturer": MANUFACTURER,
            "name": reading.device_name
            if reading
            else f"TireMoni sensor {self._sensor_id}",
            "via_device": (DOMAIN, self.coordinator.address),
        }

    @property
    def available(self) -> bool:
        """Return if the entity has a value."""
        return self.native_value is not None

    @property
    def native_value(self) -> _SensorValueType:
        """Return the native value."""
        data = self.coordinator.data
        if data is None:
            return None
        return VALUE_GETTERS[self.entity_description.key](data, self._sensor_id)
