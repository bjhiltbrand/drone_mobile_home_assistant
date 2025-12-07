"""Support for DroneMobile locks."""
from __future__ import annotations

import logging
from typing import Any

from drone_mobile.exceptions import CommandFailedError, DroneMobileException

from homeassistant.components.lock import LockEntity, LockEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DroneMobileDataUpdateCoordinator, DroneMobileEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DroneMobile locks based on a config entry."""
    coordinator: DroneMobileDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        DroneMobileDoorLock(coordinator),
        DroneMobileTrunkLock(coordinator),
    ]

    async_add_entities(entities)


class DroneMobileDoorLock(DroneMobileEntity, LockEntity):
    """Representation of a DroneMobile door lock."""

    _attr_name = "Door lock"

    def __init__(self, coordinator: DroneMobileDataUpdateCoordinator) -> None:
        """Initialize the lock."""
        super().__init__(coordinator, "door_lock")
        self._attr_icon = "mdi:car-door-lock"

    @property
    def is_locked(self) -> bool | None:
        """Return true if the lock is locked."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.is_locked

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the vehicle."""
        if self.is_locked and not self.coordinator.override_lock_state_check:
            _LOGGER.debug(
                "Vehicle %s is already locked, skipping",
                self.coordinator.vehicle.name,
            )
            return

        _LOGGER.debug("Locking vehicle %s", self.coordinator.vehicle.name)
        
        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.lock)
            await self.coordinator.async_request_refresh()
        except CommandFailedError as err:
            raise HomeAssistantError(f"Failed to lock vehicle: {err}") from err
        except DroneMobileException as err:
            raise HomeAssistantError(f"Error communicating with vehicle: {err}") from err

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the vehicle."""
        if not self.is_locked and not self.coordinator.override_lock_state_check:
            _LOGGER.debug(
                "Vehicle %s is already unlocked, skipping",
                self.coordinator.vehicle.name,
            )
            return

        _LOGGER.debug("Unlocking vehicle %s", self.coordinator.vehicle.name)
        
        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.unlock)
            await self.coordinator.async_request_refresh()
        except CommandFailedError as err:
            raise HomeAssistantError(f"Failed to unlock vehicle: {err}") from err
        except DroneMobileException as err:
            raise HomeAssistantError(f"Error communicating with vehicle: {err}") from err


class DroneMobileTrunkLock(DroneMobileEntity, LockEntity):
    """Representation of a DroneMobile trunk lock."""

    _attr_name = "Trunk"
    _attr_supported_features = LockEntityFeature.OPEN

    def __init__(self, coordinator: DroneMobileDataUpdateCoordinator) -> None:
        """Initialize the lock."""
        super().__init__(coordinator, "trunk")
        self._attr_icon = "mdi:car-back"

    @property
    def is_locked(self) -> bool | None:
        """Return true if the trunk is closed."""
        # Note: The trunk "locked" state represents if it's closed
        # We don't have specific trunk lock status, just open/closed
        if not self.coordinator.data or not self.coordinator.data.raw_data:
            return None
        
        # Check if trunk is open in raw data (API specific field)
        trunk_status = self.coordinator.data.raw_data.get("last_known_state", {}).get(
            "controller", {}
        ).get("trunk_open")
        
        if trunk_status is None:
            return None
        
        # Locked = closed, Unlocked = open
        return not trunk_status

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock (close) the trunk - not supported."""
        raise HomeAssistantError("Closing the trunk remotely is not supported")

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock (open) the trunk."""
        _LOGGER.debug("Opening trunk for vehicle %s", self.coordinator.vehicle.name)
        
        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.trunk)
            await self.coordinator.async_request_refresh()
        except CommandFailedError as err:
            raise HomeAssistantError(f"Failed to open trunk: {err}") from err
        except DroneMobileException as err:
            raise HomeAssistantError(f"Error communicating with vehicle: {err}") from err

    async def async_open(self, **kwargs: Any) -> None:
        """Open the trunk."""
        await self.async_unlock(**kwargs)