"""Support for DroneMobile device tracker."""
from __future__ import annotations

import logging

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DroneMobileDataUpdateCoordinator, DroneMobileEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DroneMobile device tracker based on a config entry."""
    coordinator: DroneMobileDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Only add tracker if vehicle has GPS location
    if coordinator.data and coordinator.data.location:
        async_add_entities([DroneMobileDeviceTracker(coordinator)])
    else:
        _LOGGER.debug("Vehicle %s does not have GPS location", coordinator.vehicle.name)


class DroneMobileDeviceTracker(DroneMobileEntity, TrackerEntity):
    """Representation of a DroneMobile device tracker."""

    _attr_name = "Location"
    _attr_icon = "mdi:map-marker"

    def __init__(self, coordinator: DroneMobileDataUpdateCoordinator) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator, "location")

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        if not self.coordinator.data or not self.coordinator.data.location:
            return None
        return self.coordinator.data.location.latitude

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        if not self.coordinator.data or not self.coordinator.data.location:
            return None
        return self.coordinator.data.location.longitude

    @property
    def source_type(self) -> SourceType:
        """Return the source type of the device."""
        return SourceType.GPS

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and self.coordinator.data is not None
            and self.coordinator.data.location is not None
        )

    @property
    def extra_state_attributes(self) -> dict[str, any] | None:
        """Return entity specific state attributes."""
        if not self.coordinator.data or not self.coordinator.data.location:
            return None

        attrs = {}
        
        location = self.coordinator.data.location
        
        if location.accuracy:
            attrs["gps_accuracy"] = location.accuracy
        
        if location.timestamp:
            attrs["last_gps_update"] = location.timestamp
        
        # Add raw GPS data from API if available
        if self.coordinator.data.raw_data:
            raw_location = self.coordinator.data.raw_data.get("last_known_state", {})
            if "gps_direction" in raw_location and raw_location["gps_direction"]:
                attrs["gps_direction"] = raw_location["gps_direction"]

        return attrs