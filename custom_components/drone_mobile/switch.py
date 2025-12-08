"""Switch platform for DroneMobile integration."""
import logging

from drone_mobile.exceptions import CommandFailedError, DroneMobileException

from homeassistant.components.switch import SwitchEntity
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
    """Set up DroneMobile switch entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        DroneMobileRemoteStart(coordinator),
        DroneMobilePanic(coordinator),
    ]

    async_add_entities(entities, True)


class DroneMobileRemoteStart(DroneMobileEntity, SwitchEntity):
    """Remote start switch."""

    def __init__(self, coordinator) -> None:
        """Initialize the switch."""
        super().__init__(
            coordinator=coordinator,
            device_id="remote_start",
            name=f"{coordinator.vehicle.name} Remote Start",
        )
        self._attr_icon = "mdi:car-key"
        self._manual_state = None  # Track manual state changes

    @property
    def is_on(self) -> bool:
        """Return true if vehicle is running."""
        # If we have a manual state override, use it for immediate feedback
        if self._manual_state is not None:
            return self._manual_state
        
        status = self.coordinator.data["status"]
        return status.is_running

    async def async_turn_on(self, **kwargs) -> None:
        """Start the vehicle."""
        if self.is_on and self._manual_state is None:
            _LOGGER.debug("Vehicle already running, skipping command")
            return

        _LOGGER.debug("Starting vehicle %s", self.coordinator.vehicle.name)
        
        # Set manual state for immediate UI feedback
        self._manual_state = True
        self.async_write_ha_state()
        
        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.start)
            await self.coordinator.async_request_refresh()
        except CommandFailedError as err:
            _LOGGER.error("Failed to start vehicle: %s", err)
            # Revert manual state on failure
            self._manual_state = None
            self.async_write_ha_state()
        except DroneMobileException as err:
            _LOGGER.error("Error starting vehicle: %s", err)
            self._manual_state = None
            self.async_write_ha_state()
        finally:
            # Clear manual state after refresh
            self._manual_state = None

    async def async_turn_off(self, **kwargs) -> None:
        """Stop the vehicle."""
        if not self.is_on and self._manual_state is None:
            _LOGGER.debug("Vehicle already stopped, skipping command")
            return

        _LOGGER.debug("Stopping vehicle %s", self.coordinator.vehicle.name)
        
        # Set manual state for immediate UI feedback
        self._manual_state = False
        self.async_write_ha_state()
        
        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.stop)
            await self.coordinator.async_request_refresh()
        except CommandFailedError as err:
            _LOGGER.error("Failed to stop vehicle: %s", err)
            # Revert manual state on failure
            self._manual_state = None
            self.async_write_ha_state()
        except DroneMobileException as err:
            _LOGGER.error("Error stopping vehicle: %s", err)
            self._manual_state = None
            self.async_write_ha_state()
        finally:
            # Clear manual state after refresh
            self._manual_state = None


class DroneMobilePanic(DroneMobileEntity, SwitchEntity):
    """Panic alarm switch."""

    def __init__(self, coordinator) -> None:
        """Initialize the switch."""
        super().__init__(
            coordinator=coordinator,
            device_id="panic",
            name=f"{coordinator.vehicle.name} Panic",
        )
        self._attr_icon = "mdi:alarm-light"
        self._manual_state = None  # Track manual state changes

    @property
    def is_on(self) -> bool:
        """Return true if panic is active."""
        # If we have a manual state override, use it for immediate feedback
        if self._manual_state is not None:
            return self._manual_state
        
        # Panic state is tracked manually since API doesn't report it
        # Default to False (off)
        return False

    async def async_turn_on(self, **kwargs) -> None:
        """Activate panic alarm."""
        _LOGGER.debug("Activating panic for %s", self.coordinator.vehicle.name)
        
        # Set manual state for immediate UI feedback
        self._manual_state = True
        self.async_write_ha_state()
        
        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.panic_on)
        except CommandFailedError as err:
            _LOGGER.error("Failed to activate panic: %s", err)
            # Revert manual state on failure
            self._manual_state = None
            self.async_write_ha_state()
        except DroneMobileException as err:
            _LOGGER.error("Error activating panic: %s", err)
            self._manual_state = None
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Deactivate panic alarm."""
        _LOGGER.debug("Deactivating panic for %s", self.coordinator.vehicle.name)
        
        # Set manual state for immediate UI feedback
        self._manual_state = False
        self.async_write_ha_state()
        
        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.panic_off)
        except CommandFailedError as err:
            _LOGGER.error("Failed to deactivate panic: %s", err)
            # Revert manual state on failure
            self._manual_state = None
            self.async_write_ha_state()
        except DroneMobileException as err:
            _LOGGER.error("Error deactivating panic: %s", err)
            self._manual_state = None
            self.async_write_ha_state()
        finally:
            # Clear manual state after a delay to ensure panic is off
            self._manual_state = None