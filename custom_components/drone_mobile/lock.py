"""Represents the primary lock of the vehicle."""
import logging

from homeassistant.components.lock import LockEntity

from . import DroneMobileEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the lock from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]

    locks = [Lock(entry)]
    async_add_entities(locks, False)


class Lock(DroneMobileEntity, LockEntity):
    """Defines the vehicle's lock."""

    def __init__(self, coordinator):
        """Initialize."""
        super().__init__(
            device_id="dronemobile_doorlock",
            name=coordinator.data["vehicle_name"] + "_doorLock",
            coordinator=coordinator,
        )

    async def async_lock(self, **kwargs):
        """Locks the vehicle."""
        #if self.is_locked:
        #    return
        _LOGGER.debug("Locking %s", self.coordinator.data['vehicle_name'])
        response = await self.coordinator.hass.async_add_executor_job(
            self.coordinator.vehicle.lock, self.coordinator.data["device_key"]
        )
        self.coordinator.update_data_from_response(self.coordinator, response)

    async def async_unlock(self, **kwargs):
        """Unlocks the vehicle."""
        #if not self.is_locked:
        #    return
        _LOGGER.debug("Unlocking %s", self.coordinator.data['vehicle_name'])
        response = await self.coordinator.hass.async_add_executor_job(
            self.coordinator.vehicle.unlock, self.coordinator.data["device_key"]
        )
        self.coordinator.update_data_from_response(self.coordinator, response)

    @property
    def is_locked(self):
        """Determine if the lock is locked."""
        if (
            self.coordinator.data is None
            or self.coordinator.data["last_known_state"]["controller"]["armed"] is None
        ):
            return None
        return self.coordinator.data["last_known_state"]["controller"]["armed"] == "true"

    @property
    def icon(self):
        return "mdi:car-door-lock"
