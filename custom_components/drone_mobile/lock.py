"""Lock platform for DroneMobile integration."""
import logging

from drone_mobile.exceptions import CommandFailedError, DroneMobileException

from homeassistant.components.lock import LockEntity, LockEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DroneMobileEntity
from .const import CONF_OVERRIDE_LOCK_STATE_CHECK, DEFAULT_OVERRIDE_LOCK_STATE_CHECK, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DroneMobile lock entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    override_lock_check = config_entry.options.get(
        CONF_OVERRIDE_LOCK_STATE_CHECK, DEFAULT_OVERRIDE_LOCK_STATE_CHECK
    )

    entities = [
        DroneMobileDoorLock(coordinator, override_lock_check),
        DroneMobileTrunk(coordinator, override_lock_check),
    ]

    async_add_entities(entities, True)


class DroneMobileDoorLock(DroneMobileEntity, LockEntity):
    """Representation of a DroneMobile door lock."""

    def __init__(self, coordinator, override_lock_check: bool) -> None:
        """Initialize the lock."""
        super().__init__(
            coordinator=coordinator,
            device_id="door_lock",
            name=f"{coordinator.vehicle.name} Door Lock",
        )
        self._override_lock_check = override_lock_check
        self._attr_icon = "mdi:car-door-lock"

    @property
    def is_locked(self) -> bool | None:
        """Return true if lock is locked."""
        status = self.coordinator.data["status"]
        return status.is_locked

    async def async_lock(self, **kwargs) -> None:
        """Lock the doors."""
        if self.is_locked and not self._override_lock_check:
            _LOGGER.debug("Doors already locked, skipping command")
            return

        _LOGGER.debug("Locking %s", self.coordinator.vehicle.name)
        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.lock)
            await self.coordinator.async_request_refresh()
        except CommandFailedError as err:
            _LOGGER.error("Failed to lock doors: %s", err)
        except DroneMobileException as err:
            _LOGGER.error("Error locking doors: %s", err)

    async def async_unlock(self, **kwargs) -> None:
        """Unlock the doors."""
        if not self.is_locked and not self._override_lock_check:
            _LOGGER.debug("Doors already unlocked, skipping command")
            return

        _LOGGER.debug("Unlocking %s", self.coordinator.vehicle.name)
        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.unlock)
            await self.coordinator.async_request_refresh()
        except CommandFailedError as err:
            _LOGGER.error("Failed to unlock doors: %s", err)
        except DroneMobileException as err:
            _LOGGER.error("Error unlocking doors: %s", err)


class DroneMobileTrunk(DroneMobileEntity, LockEntity):
    """Representation of a DroneMobile trunk."""

    _attr_supported_features = LockEntityFeature.OPEN

    def __init__(self, coordinator, override_lock_check: bool) -> None:
        """Initialize the trunk."""
        super().__init__(
            coordinator=coordinator,
            device_id="trunk",
            name=f"{coordinator.vehicle.name} Trunk",
        )
        self._override_lock_check = override_lock_check
        self._attr_icon = "mdi:car-back"

    @property
    def is_locked(self) -> bool | None:
        """Return true if trunk is closed."""
        # Note: The trunk state is inverted - trunk_open means unlocked
        status = self.coordinator.data["status"]
        # Access nested structure: raw_data.last_known_state.controller.trunk_open
        if "last_known_state" in status.raw_data:
            controller = status.raw_data["last_known_state"].get("controller", {})
            trunk_open = controller.get("trunk_open")
            if trunk_open is not None:
                return not trunk_open
        return None

    async def async_unlock(self, **kwargs) -> None:
        """Open the trunk."""
        _LOGGER.debug("Opening trunk for %s", self.coordinator.vehicle.name)
        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.trunk)
            await self.coordinator.async_request_refresh()
        except CommandFailedError as err:
            _LOGGER.error("Failed to open trunk: %s", err)
        except DroneMobileException as err:
            _LOGGER.error("Error opening trunk: %s", err)

    async def async_open(self, **kwargs) -> None:
        """Open the trunk."""
        await self.async_unlock(**kwargs)

    async def async_lock(self, **kwargs) -> None:
        """Lock is not supported for trunk."""
        _LOGGER.warning("Trunk cannot be locked remotely")