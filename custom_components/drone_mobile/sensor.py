"""Support for DroneMobile sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util

from . import DroneMobileDataUpdateCoordinator, DroneMobileEntity
from .const import CONF_UNIT, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class DroneMobileSensorEntityDescription(SensorEntityDescription):
    """Describes DroneMobile sensor entity."""

    value_fn: Callable[[Any, str], StateType] | None = None
    available_fn: Callable[[Any], bool] | None = None


def get_odometer_value(status: Any, unit: str) -> float | None:
    """Get odometer value in correct units."""
    if not status or not status.odometer:
        return None
    
    if unit == "Imperial":
        return status.odometer
    # Convert miles to kilometers
    return round(status.odometer * 1.60934, 2)


def get_temperature_value(status: Any, unit: str) -> float | None:
    """Get temperature value in correct units."""
    if not status or status.interior_temperature is None:
        return None
    
    temp_celsius = status.interior_temperature
    
    if unit == "Imperial":
        # Convert Celsius to Fahrenheit
        return round((temp_celsius * 9 / 5) + 32, 1)
    return temp_celsius


SENSOR_DESCRIPTIONS: tuple[DroneMobileSensorEntityDescription, ...] = (
    DroneMobileSensorEntityDescription(
        key="odometer",
        name="Odometer",
        icon="mdi:counter",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfLength.MILES,
        value_fn=lambda status, unit: get_odometer_value(status, unit),
    ),
    DroneMobileSensorEntityDescription(
        key="battery",
        name="Battery voltage",
        icon="mdi:car-battery",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=lambda status, unit: status.battery_voltage if status else None,
        suggested_display_precision=1,
    ),
    DroneMobileSensorEntityDescription(
        key="battery_percent",
        name="Battery level",
        icon="mdi:battery",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda status, unit: status.battery_percent if status else None,
    ),
    DroneMobileSensorEntityDescription(
        key="temperature",
        name="Interior temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda status, unit: get_temperature_value(status, unit),
        available_fn=lambda status: status and status.interior_temperature is not None,
    ),
    DroneMobileSensorEntityDescription(
        key="fuel_level",
        name="Fuel level",
        icon="mdi:gas-station",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda status, unit: status.fuel_level if status else None,
        available_fn=lambda status: status and status.fuel_level is not None,
    ),
    DroneMobileSensorEntityDescription(
        key="alarm",
        name="Alarm status",
        icon="mdi:shield-car",
        device_class=SensorDeviceClass.ENUM,
        options=["armed", "disarmed"],
        value_fn=lambda status, unit: "armed" if status and status.is_locked else "disarmed",
    ),
    DroneMobileSensorEntityDescription(
        key="last_refresh",
        name="Last update",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda status, unit: (
            dt_util.as_local(status.last_updated) if status and status.last_updated else None
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DroneMobile sensors based on a config entry."""
    coordinator: DroneMobileDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        DroneMobileSensor(coordinator, description, entry.options.get(CONF_UNIT, "Imperial"))
        for description in SENSOR_DESCRIPTIONS
    ]
    
    async_add_entities(entities)


class DroneMobileSensor(DroneMobileEntity, SensorEntity):
    """Representation of a DroneMobile sensor."""

    entity_description: DroneMobileSensorEntityDescription

    def __init__(
        self,
        coordinator: DroneMobileDataUpdateCoordinator,
        description: DroneMobileSensorEntityDescription,
        unit: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._unit = unit
        self._attr_name = description.name

        # Update unit of measurement for distance based on user preference
        if description.key == "odometer":
            if unit == "Metric":
                self._attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
        
        # Update unit for temperature
        if description.key == "temperature":
            if unit == "Imperial":
                self._attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.entity_description.value_fn is None:
            return None
        
        return self.entity_description.value_fn(self.coordinator.data, self._unit)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not super().available:
            return False
        
        if self.entity_description.available_fn is not None:
            return self.entity_description.available_fn(self.coordinator.data)
        
        return True

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return entity specific state attributes."""
        if not self.coordinator.data:
            return None
        
        # For odometer, add raw data
        if self.entity_description.key == "odometer":
            return {
                "vehicle_id": self.coordinator.vehicle.vehicle_id,
                "last_updated": self.coordinator.data.last_updated,
            }
        
        return None