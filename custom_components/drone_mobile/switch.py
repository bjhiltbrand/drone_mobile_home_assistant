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

# Controller feature flags managed together by the /features endpoint.
# The API expects the full object, so a toggle sends all of them with the
# target flag changed. Only the user-settable ones are exposed as switches;
# the dealer-gated ones (e.g. valet mode) are read-only elsewhere.
FEATURE_FLAGS = (
    "siren_enabled",
    "valet_mode_enabled",
    "shock_sensor_enabled",
    "drive_lock_enabled",
    "turbo_timer_start_enabled",
    "passive_arming_enabled",
)


def _controller(status) -> dict:
    """Return the controller block from the raw status payload, or {}."""
    raw = getattr(status, "raw_data", None) or {}
    return (raw.get("last_known_state") or {}).get("controller") or {}


def _current_features(status) -> dict:
    """Current values of all feature flags, for a full-object PATCH."""
    controller = _controller(status)
    return {flag: bool(controller.get(flag, False)) for flag in FEATURE_FLAGS}


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
        DroneMobileFeatureSwitch(
            coordinator, "siren_enabled", "Siren", "mdi:bullhorn"
        ),
        DroneMobileFeatureSwitch(
            coordinator, "shock_sensor_enabled", "Shock Sensor", "mdi:vibrate"
        ),
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


class DroneMobileFeatureSwitch(DroneMobileEntity, SwitchEntity):
    """A user-settable controller feature (e.g. siren, shock sensor).

    State is read from the controller block in the status payload. Toggling
    sends the full feature object via set_features with the one flag changed,
    so dealer-gated flags ride along at their current value and do not trip
    the installer error.
    """

    _attr_should_poll = False

    def __init__(self, coordinator, feature_key: str, label: str, icon: str) -> None:
        """Initialize the switch."""
        super().__init__(
            coordinator=coordinator,
            device_id=feature_key,
            name=f"{coordinator.vehicle.name} {label}",
        )
        self._feature_key = feature_key
        self._attr_icon = icon
        self._manual_state = None
        self._manual_state_expiry = None

    @property
    def is_on(self) -> bool | None:
        """Return true if the feature is enabled."""
        if self._manual_state is not None and self._manual_state_expiry is not None:
            if datetime.now() > self._manual_state_expiry:
                self._manual_state = None
                self._manual_state_expiry = None
        if self._manual_state is not None:
            return self._manual_state

        value = _controller(self.coordinator.data["status"]).get(self._feature_key)
        return bool(value) if value is not None else None

    def _handle_coordinator_update(self) -> None:
        """Clear the manual override once the real state catches up."""
        if self._manual_state is not None:
            controller = _controller(self.coordinator.data["status"])
            if self._manual_state == bool(controller.get(self._feature_key, False)):
                self._manual_state = None
                self._manual_state_expiry = None
        super()._handle_coordinator_update()

    async def _apply(self, target: bool) -> None:
        """Send the full feature object with this flag set to target."""
        features = _current_features(self.coordinator.data["status"])
        features[self._feature_key] = target

        # Optimistic UI; reverts on error or once the coordinator catches up.
        self._manual_state = target
        self._manual_state_expiry = datetime.now() + timedelta(seconds=15)
        self.async_write_ha_state()

        try:
            await self.hass.async_add_executor_job(
                lambda: self.coordinator.vehicle.set_features(**features)
            )
            await self.coordinator.async_request_refresh()
        except (CommandFailedError, DroneMobileException) as err:
            _LOGGER.error(
                "Failed to set %s for %s: %s",
                self._feature_key,
                self.coordinator.vehicle.name,
                err,
            )
            self._manual_state = None
            self._manual_state_expiry = None
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """Enable the feature."""
        await self._apply(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Disable the feature."""
        await self._apply(False)