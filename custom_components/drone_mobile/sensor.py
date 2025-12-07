"""Support for DroneMobile sensors."""
from datetime import datetime
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt

from . import DroneMobileEntity
from .const import CONF_UNIT, DOMAIN, SENSORS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Entities from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    entities = []

    for key, value in SENSORS.items():
        entities.append(CarSensor(entry, key, config_entry.options))

    async_add_entities(entities, True)


class CarSensor(DroneMobileEntity, SensorEntity):
    """Representation of a DroneMobile sensor."""

    def __init__(self, coordinator, sensor: str, options: dict):
        """Initialize the sensor."""
        super().__init__(
            device_id=f"dronemobile_{sensor}",
            name=f"{coordinator.data['vehicle_name']}_{sensor}",
            coordinator=coordinator,
        )
        self._sensor = sensor
        self.options = options
        self._attr = {}
        # Required for HA 2022.7
        self.coordinator_context = object()

    def get_value(self, ftype: str) -> StateType | dict | None:
        """Get sensor value based on type."""
        # Get the status object if available
        status = self.coordinator.data.get("_status")

        if ftype == "state":
            if self._sensor == "odometer":
                if not status or status.odometer is None:
                    return None
                mileage = status.odometer
                if self.options.get(CONF_UNIT) == "Metric":
                    return round(mileage * 1.60934, 1)
                return mileage

            elif self._sensor == "battery":
                if not status:
                    return None
                return status.battery_voltage

            elif self._sensor == "temperature":
                if not status or status.interior_temperature is None:
                    return "Unsupported"
                temp_c = status.interior_temperature
                if self.options.get(CONF_UNIT) == "Imperial":
                    return round((temp_c * 9 / 5) + 32, 1)
                return temp_c

            elif self._sensor == "gps":
                # GPS direction not available in new API
                return "N/A"

            elif self._sensor == "alarm":
                if not status:
                    return None
                return "Armed" if status.is_locked else "Disarmed"

            elif self._sensor == "ignitionStatus":
                if not status:
                    return None
                return "On" if status.is_running else "Off"

            elif self._sensor == "engineStatus":
                if not status:
                    return None
                if status.is_running:
                    return "Running"
                # Update remote start status
                if self.coordinator.data.get("remote_start_status"):
                    self.coordinator.data["remote_start_status"] = False
                return "Off"

            elif self._sensor == "doorStatus":
                # Door status inferred from lock state
                if not status:
                    return None
                return "Closed" if status.is_locked else "Unknown"

            elif self._sensor == "trunkStatus":
                # Trunk status not directly available in new API
                return "Unknown"

            elif self._sensor == "hoodStatus":
                # Hood status not directly available in new API
                return "Unknown"

            elif self._sensor == "lastRefresh":
                if not status or not status.last_updated:
                    return None
                return dt.as_local(status.last_updated)

        elif ftype == "measurement":
            if self._sensor == "odometer":
                return "mi" if self.options.get(CONF_UNIT) == "Imperial" else "km"
            elif self._sensor == "battery":
                return "V"
            elif self._sensor == "temperature":
                return "°F" if self.options.get(CONF_UNIT) == "Imperial" else "°C"
            return None

        elif ftype == "attribute":
            if self._sensor == "battery" and status:
                return {"Battery Voltage": status.battery_voltage}
            elif self._sensor in ["odometer", "temperature", "gps", "alarm", "ignitionStatus",
                                   "engineStatus", "doorStatus", "trunkStatus", "hoodStatus"]:
                # Return raw data for debugging
                return {"raw_data": self.coordinator.data} if status else None
            return None

        return None

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.get_value("state")

    @property
    def extra_state_attributes(self) -> dict | None:
        """Return the state attributes."""
        return self.get_value("attribute")

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        return self.get_value("measurement")

    @property
    def icon(self) -> str:
        """Return the icon."""
        return SENSORS[self._sensor]["icon"]