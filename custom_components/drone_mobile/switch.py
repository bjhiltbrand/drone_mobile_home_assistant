"""Switch platform for DroneMobile integration."""
from datetime import datetime, timedelta
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
        self._manual_state_expiry = None  # When to expire manual state
        self._attr_should_poll = False  # We'll handle updates via coordinator

    @property
    def is_on(self) -> bool:
        """Return true if vehicle is running."""
        # Check if manual state has expired
        if self._manual_state is not None and self._manual_state_expiry is not None:
            if datetime.now() > self._manual_state_expiry:
                self._manual_state = None
                self._manual_state_expiry = None

        # If we have a manual state override, use it for immediate feedback
        if self._manual_state is not None:
            return self._manual_state

        status = self.coordinator.data["status"]
        return status.is_running

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Only clear manual state if it matches the real state now
        # or if manual state has expired
        if self._manual_state is not None:
            status = self.coordinator.data["status"]
            if self._manual_state == status.is_running:
                # State matches, clear manual override
                self._manual_state = None
                self._manual_state_expiry = None

        super()._handle_coordinator_update()

    async def async_turn_on(self, **kwargs) -> None:
        """Start the vehicle."""
        status = self.coordinator.data["status"]
        if status.is_running and self._manual_state is None:
            _LOGGER.debug("Vehicle already running, skipping command")
            return

        _LOGGER.debug("Starting vehicle %s", self.coordinator.vehicle.name)

        # Set manual state for immediate UI feedback
        self._manual_state = True
        self._manual_state_expiry = datetime.now() + timedelta(seconds=15)
        self.async_write_ha_state()

        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.start)
            await self.coordinator.async_request_refresh()
        except CommandFailedError as err:
            _LOGGER.error("Failed to start vehicle: %s", err)
            self._manual_state = None
            self._manual_state_expiry = None
            self.async_write_ha_state()
        except DroneMobileException as err:
            _LOGGER.error("Error starting vehicle: %s", err)
            self._manual_state = None
            self._manual_state_expiry = None
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Stop the vehicle."""
        status = self.coordinator.data["status"]
        if not status.is_running and self._manual_state is None:
            _LOGGER.debug("Vehicle already stopped, skipping command")
            return

        _LOGGER.debug("Stopping vehicle %s", self.coordinator.vehicle.name)

        # Set manual state for immediate UI feedback
        self._manual_state = False
        self._manual_state_expiry = datetime.now() + timedelta(seconds=15)
        self.async_write_ha_state()

        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.stop)
            await self.coordinator.async_request_refresh()
        except CommandFailedError as err:
            _LOGGER.error("Failed to stop vehicle: %s", err)
            self._manual_state = None
            self._manual_state_expiry = None
            self.async_write_ha_state()
        except DroneMobileException as err:
            _LOGGER.error("Error stopping vehicle: %s", err)
            self._manual_state = None
            self._manual_state_expiry = None
            self.async_write_ha_state()


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
        self._manual_state_expiry = None  # When to expire manual state
        self._attr_should_poll = False  # We'll handle updates via coordinator

    @property
    def is_on(self) -> bool:
        """Return true if panic is active."""
        # Check if manual state has expired
        if self._manual_state is not None and self._manual_state_expiry is not None:
            if datetime.now() > self._manual_state_expiry:
                self._manual_state = None
                self._manual_state_expiry = None

        # If we have a manual state override, use it for immediate feedback
        if self._manual_state is not None:
            return self._manual_state

        # Panic state is tracked manually since API doesn't report it
        return False

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Clear manual state when we get real data from coordinator
        self._manual_state = None
        self._manual_state_expiry = None
        super()._handle_coordinator_update()

    async def async_turn_on(self, **kwargs) -> None:
        """Activate panic alarm."""
        _LOGGER.debug("Activating panic for %s", self.coordinator.vehicle.name)

        self._manual_state = True
        self._manual_state_expiry = datetime.now() + timedelta(seconds=15)
        self.async_write_ha_state()

        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.panic_on)
        except CommandFailedError as err:
            _LOGGER.error("Failed to activate panic: %s", err)
            self._manual_state = None
            self._manual_state_expiry = None
            self.async_write_ha_state()
        except DroneMobileException as err:
            _LOGGER.error("Error activating panic: %s", err)
            self._manual_state = None
            self._manual_state_expiry = None
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Deactivate panic alarm."""
        _LOGGER.debug("Deactivating panic for %s", self.coordinator.vehicle.name)

        self._manual_state = False
        self._manual_state_expiry = datetime.now() + timedelta(seconds=15)
        self.async_write_ha_state()

        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.panic_off)
        except CommandFailedError as err:
            _LOGGER.error("Failed to deactivate panic: %s", err)
            self._manual_state = None
            self._manual_state_expiry = None
            self.async_write_ha_state()
        except DroneMobileException as err:
            _LOGGER.error("Error deactivating panic: %s", err)
            self._manual_state = None
            self._manual_state_expiry = None
            self.async_write_ha_state()