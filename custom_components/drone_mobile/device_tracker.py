"""Support for DroneMobile device tracking."""
import logging

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity

from . import DroneMobileEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Entities from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    
    # Check if vehicle has location data
    status = entry.data.get("_status")
    if status and status.location:
        async_add_entities([CarTracker(entry, "gps")], True)
    else:
        _LOGGER.debug("Vehicle does not support GPS tracking")


class CarTracker(DroneMobileEntity, TrackerEntity):
    """Representation of a DroneMobile device tracker."""

    def __init__(self, coordinator, sensor: str):
        """Initialize the tracker."""
        super().__init__(
            device_id="dronemobile_tracker",
            name="dronemobile_tracker",
            coordinator=coordinator,
        )
        self._attr = {}
        self.sensor = sensor
        # Required for HA 2022.7
        self.coordinator_context = object()

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        status = self.coordinator.data.get("_status")
        if status and status.location:
            return status.location.latitude
        return None

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        status = self.coordinator.data.get("_status")
        if status and status.location:
            return status.location.longitude
        return None

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.GPS

    @property
    def location_accuracy(self) -> int:
        """Return the location accuracy."""
        status = self.coordinator.data.get("_status")
        if status and status.location and status.location.accuracy:
            return int(status.location.accuracy)
        return 0

    @property
    def extra_state_attributes(self) -> dict | None:
        """Return device state attributes."""
        status = self.coordinator.data.get("_status")
        if not status or not status.location:
            return None

        attrs = {
            "latitude": status.location.latitude,
            "longitude": status.location.longitude,
        }

        if status.location.accuracy:
            attrs["accuracy"] = status.location.accuracy

        if status.location.timestamp:
            attrs["last_updated"] = status.location.timestamp

        return attrs

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:radar"