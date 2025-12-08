"""Device tracker platform for DroneMobile integration."""
import logging

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DroneMobileEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DroneMobile device tracker."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Only add tracker if location is available
    status = coordinator.data["status"]
    if status.location is not None:
        async_add_entities([DroneMobileDeviceTracker(coordinator)], True)
    else:
        _LOGGER.debug("Vehicle does not support GPS tracking")


class DroneMobileDeviceTracker(DroneMobileEntity, TrackerEntity):
    """Representation of a DroneMobile device tracker."""

    _attr_icon = "mdi:car"

    def __init__(self, coordinator) -> None:
        """Initialize the device tracker."""
        super().__init__(
            coordinator=coordinator,
            device_id="gps_tracker",
            name=f"{coordinator.vehicle.name} Location",
        )

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        status = self.coordinator.data["status"]
        if status.location:
            return status.location.latitude
        return None

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        status = self.coordinator.data["status"]
        if status.location:
            return status.location.longitude
        return None

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.GPS

    @property
    def extra_state_attributes(self) -> dict:
        """Return device specific attributes."""
        status = self.coordinator.data["status"]
        attrs = {}
        
        if status.location:
            if status.location.accuracy is not None:
                attrs["gps_accuracy"] = status.location.accuracy
            if status.location.timestamp:
                attrs["last_gps_update"] = status.location.timestamp.isoformat()
        
        return attrs