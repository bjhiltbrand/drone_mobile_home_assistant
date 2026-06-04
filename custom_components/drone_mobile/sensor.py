"""Sensor platform for DroneMobile integration."""
from datetime import datetime
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
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
from homeassistant.util import dt as dt_util

from . import DroneMobileEntity
from .const import CONF_UNIT, DEFAULT_UNIT, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DroneMobile sensor entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    units = config_entry.options.get(CONF_UNIT, DEFAULT_UNIT)
    use_metric = units == "Metric"

    entities = [
        DroneMobileOdometer(coordinator, use_metric),
        DroneMobileBattery(coordinator),
        DroneMobileTemperature(coordinator, use_metric),
        DroneMobileAlarm(coordinator),
        DroneMobileIgnition(coordinator),
        DroneMobileEngine(coordinator),
        DroneMobileDoor(coordinator),
        DroneMobileTrunkSensor(coordinator),
        DroneMobileHood(coordinator),
        DroneMobileLastRefresh(coordinator),
    ]

    # Only add GPS sensor if location is available
    status = coordinator.data["status"]
    if status.location is not None:
        entities.append(DroneMobileGPS(coordinator))

    async_add_entities(entities, True)

    _LOGGER.warning(
        "The string status sensors (Alarm, Ignition, Engine, Doors, Trunk, "
        "Hood) are deprecated in favor of the new binary_sensor entities and "
        "are disabled by default for new installs. They will be removed in a "
        "future release; please migrate dashboards and automations to the "
        "binary_sensor equivalents."
    )


class DroneMobileOdometer(DroneMobileEntity, SensorEntity):
    """Odometer sensor."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator, use_metric: bool) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            device_id="odometer",
            name=f"{coordinator.vehicle.name} Odometer",
        )
        self._use_metric = use_metric
        self._attr_icon = "mdi:counter"
        self._attr_native_unit_of_measurement = (
            UnitOfLength.KILOMETERS if use_metric else UnitOfLength.MILES
        )

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        status = self.coordinator.data["status"]
        if status.odometer is None:
            return None

        if self._use_metric:
            return round(status.odometer * 1.60934, 1)
        return status.odometer


class DroneMobileBattery(DroneMobileEntity, SensorEntity):
    """Battery voltage sensor."""

    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            device_id="battery",
            name=f"{coordinator.vehicle.name} Battery",
        )
        self._attr_icon = "mdi:car-battery"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        status = self.coordinator.data["status"]
        return status.battery_voltage

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        status = self.coordinator.data["status"]
        attrs = {}
        if status.battery_percent is not None:
            attrs["battery_percent"] = status.battery_percent
        return attrs


class DroneMobileTemperature(DroneMobileEntity, SensorEntity):
    """Temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, use_metric: bool) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            device_id="temperature",
            name=f"{coordinator.vehicle.name} Temperature",
        )
        self._use_metric = use_metric
        self._attr_icon = "mdi:thermometer"
        self._attr_native_unit_of_measurement = (
            UnitOfTemperature.CELSIUS if use_metric else UnitOfTemperature.FAHRENHEIT
        )

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        status = self.coordinator.data["status"]
        if status.interior_temperature is None:
            return None

        temp_c = status.interior_temperature
        if self._use_metric:
            return round(temp_c, 1)
        return round(temp_c * 9 / 5 + 32, 1)

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        status = self.coordinator.data["status"]
        attrs = {}
        if status.exterior_temperature is not None:
            if self._use_metric:
                attrs["exterior_temperature"] = round(status.exterior_temperature, 1)
            else:
                attrs["exterior_temperature"] = round(
                    status.exterior_temperature * 9 / 5 + 32, 1
                )
        return attrs


class DroneMobileGPS(DroneMobileEntity, SensorEntity):
    """GPS direction sensor."""

    def __init__(self, coordinator) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            device_id="gps",
            name=f"{coordinator.vehicle.name} GPS",
        )
        self._attr_icon = "mdi:radar"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        status = self.coordinator.data["status"]
        if status.location is None:
            return None
        return f"{status.location.latitude}, {status.location.longitude}"

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        status = self.coordinator.data["status"]
        if status.location is None:
            return {}
        return {
            "latitude": status.location.latitude,
            "longitude": status.location.longitude,
            "accuracy": status.location.accuracy,
        }


class DroneMobileAlarm(DroneMobileEntity, SensorEntity):
    """Alarm status sensor.

    Deprecated: superseded by the Lock binary sensor. Disabled by default for
    new installs; will be removed in a future release.
    """

    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            device_id="alarm",
            name=f"{coordinator.vehicle.name} Alarm",
        )
        self._attr_icon = "mdi:bell"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        status = self.coordinator.data["status"]
        return "Armed" if status.is_locked else "Disarmed"


class DroneMobileIgnition(DroneMobileEntity, SensorEntity):
    """Ignition status sensor.

    Deprecated: superseded by the Ignition binary sensor. Disabled by default
    for new installs; will be removed in a future release.
    """

    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            device_id="ignition_status",
            name=f"{coordinator.vehicle.name} Ignition",
        )
        self._attr_icon = "hass:power"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        status = self.coordinator.data["status"]
        # Check nested structure: raw_data.last_known_state.controller.ignition_on
        if "last_known_state" in status.raw_data:
            controller = status.raw_data["last_known_state"].get("controller", {})
            ignition_on = controller.get("ignition_on", False)
            return "On" if ignition_on else "Off"
        return "Unknown"


class DroneMobileEngine(DroneMobileEntity, SensorEntity):
    """Engine status sensor.

    Deprecated: superseded by the Engine binary sensor. Disabled by default
    for new installs; will be removed in a future release.
    """

    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            device_id="engine_status",
            name=f"{coordinator.vehicle.name} Engine",
        )
        self._attr_icon = "mdi:engine"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        status = self.coordinator.data["status"]
        return "Running" if status.is_running else "Off"


class DroneMobileDoor(DroneMobileEntity, SensorEntity):
    """Door status sensor.

    Deprecated: superseded by the Doors binary sensor. Disabled by default for
    new installs; will be removed in a future release.
    """

    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            device_id="door_status",
            name=f"{coordinator.vehicle.name} Doors",
        )
        self._attr_icon = "mdi:car-door"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        status = self.coordinator.data["status"]
        if "last_known_state" in status.raw_data:
            controller = status.raw_data["last_known_state"].get("controller", {})
            door_open = controller.get("door_open", False)
            return "Open" if door_open else "Closed"
        return "Unknown"


class DroneMobileTrunkSensor(DroneMobileEntity, SensorEntity):
    """Trunk status sensor.

    Deprecated: superseded by the Trunk binary sensor. Disabled by default for
    new installs; will be removed in a future release.
    """

    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            device_id="trunk_status",
            name=f"{coordinator.vehicle.name} Trunk Status",
        )
        self._attr_icon = "mdi:car-back"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        status = self.coordinator.data["status"]
        if "last_known_state" in status.raw_data:
            controller = status.raw_data["last_known_state"].get("controller", {})
            trunk_open = controller.get("trunk_open", False)
            return "Open" if trunk_open else "Closed"
        return "Unknown"


class DroneMobileHood(DroneMobileEntity, SensorEntity):
    """Hood status sensor.

    Deprecated: superseded by the Hood binary sensor. Disabled by default for
    new installs; will be removed in a future release.
    """

    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            device_id="hood_status",
            name=f"{coordinator.vehicle.name} Hood",
        )
        self._attr_icon = "mdi:car-info"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        status = self.coordinator.data["status"]
        if "last_known_state" in status.raw_data:
            controller = status.raw_data["last_known_state"].get("controller", {})
            hood_open = controller.get("hood_open", False)
            return "Open" if hood_open else "Closed"
        return "Unknown"


class DroneMobileLastRefresh(DroneMobileEntity, SensorEntity):
    """Last refresh timestamp sensor."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator,
            device_id="last_refresh",
            name=f"{coordinator.vehicle.name} Last Refresh",
        )
        self._attr_icon = "mdi:clock"

    @property
    def native_value(self) -> datetime | None:
        """Return the state of the sensor."""
        status = self.coordinator.data["status"]
        if status.last_updated:
            return dt_util.as_local(status.last_updated)
        return None