"""Support for DroneMobile locks."""
import logging

from drone_mobile.exceptions import CommandFailedError, DroneMobileException

from homeassistant.components.lock import LockEntity, LockEntityFeature

from . import DroneMobileEntity
from .const import DOMAIN, LOCKS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Lock Entities from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    entities = []

    for key, value in LOCKS.items():
        entities.append(Lock(entry, key))

    async_add_entities(entities, True)


class Lock(DroneMobileEntity, LockEntity):
    """Representation of a DroneMobile lock."""

    def __init__(self, coordinator, lock: str):
        """Initialize the lock."""
        super().__init__(
            device_id=f"dronemobile_{lock}",
            name=f"{coordinator.data['vehicle_name']}_{lock}",
            coordinator=coordinator,
        )
        self._lock = lock
        self._state = self.is_locked

    async def async_lock(self, **kwargs):
        """Lock the vehicle device."""
        if self.is_locked and not self.coordinator._override_lock_state_check:
            _LOGGER.debug("Vehicle already locked, skipping command")
            return

        _LOGGER.debug("Locking %s", self.coordinator.data["vehicle_name"])

        try:
            if self._lock == "doorLock":
                response = await self.coordinator.hass.async_add_executor_job(
                    self.coordinator.vehicle.lock
                )
                _LOGGER.info("Lock command result: %s", response.message)
            else:
                _LOGGER.warning("Unknown lock type: %s", self._lock)
                return

            # Refresh coordinator data
            await self.coordinator.async_refresh()
            self._state = self.is_locked
            self.async_write_ha_state()

        except CommandFailedError as err:
            _LOGGER.error("Failed to lock %s: %s", self.coordinator.data["vehicle_name"], err)
        except DroneMobileException as err:
            _LOGGER.error("Error locking %s: %s", self.coordinator.data["vehicle_name"], err)

    async def async_unlock(self, **kwargs):
        """Unlock the vehicle device."""
        if not self.is_locked and not self.coordinator._override_lock_state_check:
            _LOGGER.debug("Vehicle already unlocked, skipping command")
            return

        _LOGGER.debug("Unlocking %s", self.coordinator.data["vehicle_name"])

        try:
            if self._lock == "doorLock":
                response = await self.coordinator.hass.async_add_executor_job(
                    self.coordinator.vehicle.unlock
                )
                _LOGGER.info("Unlock command result: %s", response.message)
            elif self._lock == "trunk":
                response = await self.coordinator.hass.async_add_executor_job(
                    self.coordinator.vehicle.trunk
                )
                _LOGGER.info("Trunk command result: %s", response.message)
            else:
                _LOGGER.warning("Unknown lock type: %s", self._lock)
                return

            # Refresh coordinator data
            await self.coordinator.async_refresh()
            self._state = self.is_locked
            self.async_write_ha_state()

        except CommandFailedError as err:
            _LOGGER.error("Failed to unlock %s: %s", self.coordinator.data["vehicle_name"], err)
        except DroneMobileException as err:
            _LOGGER.error("Error unlocking %s: %s", self.coordinator.data["vehicle_name"], err)

    async def async_open(self, **kwargs):
        """Open the trunk."""
        if self._lock != "trunk":
            _LOGGER.warning("Open only supported for trunk")
            return

        _LOGGER.debug("Opening trunk for %s", self.coordinator.data["vehicle_name"])

        try:
            response = await self.coordinator.hass.async_add_executor_job(
                self.coordinator.vehicle.trunk
            )
            _LOGGER.info("Trunk command result: %s", response.message)

            # Refresh coordinator data
            await self.coordinator.async_refresh()
            self._state = self.is_locked
            self.async_write_ha_state()

        except CommandFailedError as err:
            _LOGGER.error("Failed to open trunk for %s: %s", 
                         self.coordinator.data["vehicle_name"], err)
        except DroneMobileException as err:
            _LOGGER.error("Error opening trunk for %s: %s", 
                         self.coordinator.data["vehicle_name"], err)

    @property
    def is_locked(self) -> bool | None:
        """Determine if the lock is locked."""
        status = self.coordinator.data.get("_status")
        
        if not status:
            return None

        if self._lock == "doorLock":
            return status.is_locked
        elif self._lock == "trunk":
            # Trunk locked status not directly available in new API
            # We assume locked by default for safety
            return True
        else:
            _LOGGER.error("Unknown lock type: %s", self._lock)
            return None

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        if self._lock == "trunk":
            return LockEntityFeature.OPEN
        return 0

    @property
    def icon(self) -> str:
        """Return the icon."""
        return LOCKS[self._lock]["icon"]