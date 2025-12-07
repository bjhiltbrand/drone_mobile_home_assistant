"""Support for DroneMobile switches."""
from __future__ import annotations

import logging
from typing import Any

from drone_mobile.exceptions import CommandFailedError, DroneMobileException

from homeassistant.components.switch import SwitchEntity
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
    """Set up DroneMobile switches based on a config entry."""
    coordinator: DroneMobileDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        DroneMobileRemoteStartSwitch(coordinator),
        DroneMobilePanicSwitch(coordinator),
        DroneMobileAux1Switch(coordinator),
        DroneMobileAux2Switch(coordinator),
    ]

    async_add_entities(entities)


class DroneMobileRemoteStartSwitch(DroneMobileEntity, SwitchEntity):
    """Representation of a DroneMobile remote start switch."""

    _attr_name = "Remote start"
    _attr_icon = "mdi:car-key"

    def __init__(self, coordinator: DroneMobileDataUpdateCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, "remote_start")

    @property
    def is_on(self) -> bool | None:
        """Return true if the engine is running."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.is_running

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start the vehicle."""
        if self.is_on:
            _LOGGER.debug(
                "Vehicle %s is already running, skipping",
                self.coordinator.vehicle.name,
            )
            return

        _LOGGER.debug("Starting vehicle %s", self.coordinator.vehicle.name)
        
        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.start)
            await self.coordinator.async_request_refresh()
        except CommandFailedError as err:
            raise HomeAssistantError(f"Failed to start vehicle: {err}") from err
        except DroneMobileException as err:
            raise HomeAssistantError(f"Error communicating with vehicle: {err}") from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop the vehicle."""
        if not self.is_on:
            _LOGGER.debug(
                "Vehicle %s is already stopped, skipping",
                self.coordinator.vehicle.name,
            )
            return

        _LOGGER.debug("Stopping vehicle %s", self.coordinator.vehicle.name)
        
        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.stop)
            await self.coordinator.async_request_refresh()
        except CommandFailedError as err:
            raise HomeAssistantError(f"Failed to stop vehicle: {err}") from err
        except DroneMobileException as err:
            raise HomeAssistantError(f"Error communicating with vehicle: {err}") from err


class DroneMobilePanicSwitch(DroneMobileEntity, SwitchEntity):
    """Representation of a DroneMobile panic switch."""

    _attr_name = "Panic alarm"
    _attr_icon = "mdi:alarm-light"

    def __init__(self, coordinator: DroneMobileDataUpdateCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, "panic")
        self._panic_active = False

    @property
    def is_on(self) -> bool:
        """Return true if panic is active."""
        return self._panic_active

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Activate panic alarm."""
        _LOGGER.debug("Activating panic for vehicle %s", self.coordinator.vehicle.name)
        
        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.panic_on)
            self._panic_active = True
            self.async_write_ha_state()
        except CommandFailedError as err:
            raise HomeAssistantError(f"Failed to activate panic: {err}") from err
        except DroneMobileException as err:
            raise HomeAssistantError(f"Error communicating with vehicle: {err}") from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Deactivate panic alarm."""
        _LOGGER.debug("Deactivating panic for vehicle %s", self.coordinator.vehicle.name)
        
        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.panic_off)
            self._panic_active = False
            self.async_write_ha_state()
        except CommandFailedError as err:
            raise HomeAssistantError(f"Failed to deactivate panic: {err}") from err
        except DroneMobileException as err:
            raise HomeAssistantError(f"Error communicating with vehicle: {err}") from err


class DroneMobileAux1Switch(DroneMobileEntity, SwitchEntity):
    """Representation of a DroneMobile auxiliary 1 switch."""

    _attr_name = "Auxiliary 1"
    _attr_icon = "mdi:numeric-1-box"

    def __init__(self, coordinator: DroneMobileDataUpdateCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, "aux1")

    @property
    def is_on(self) -> bool:
        """Return false - this is a momentary switch."""
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Trigger auxiliary 1."""
        _LOGGER.debug("Triggering AUX1 for vehicle %s", self.coordinator.vehicle.name)
        
        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.aux1)
            # Momentary switch - immediately return to off state
            self.async_write_ha_state()
        except CommandFailedError as err:
            raise HomeAssistantError(f"Failed to trigger AUX1: {err}") from err
        except DroneMobileException as err:
            raise HomeAssistantError(f"Error communicating with vehicle: {err}") from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off - no-op for momentary switch."""
        pass


class DroneMobileAux2Switch(DroneMobileEntity, SwitchEntity):
    """Representation of a DroneMobile auxiliary 2 switch."""

    _attr_name = "Auxiliary 2"
    _attr_icon = "mdi:numeric-2-box"

    def __init__(self, coordinator: DroneMobileDataUpdateCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, "aux2")

    @property
    def is_on(self) -> bool:
        """Return false - this is a momentary switch."""
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Trigger auxiliary 2."""
        _LOGGER.debug("Triggering AUX2 for vehicle %s", self.coordinator.vehicle.name)
        
        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.aux2)
            # Momentary switch - immediately return to off state
            self.async_write_ha_state()
        except CommandFailedError as err:
            raise HomeAssistantError(f"Failed to trigger AUX2: {err}") from err
        except DroneMobileException as err:
            raise HomeAssistantError(f"Error communicating with vehicle: {err}") from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off - no-op for momentary switch."""
        pass