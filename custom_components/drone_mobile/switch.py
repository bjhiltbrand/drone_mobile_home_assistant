"""Support for DroneMobile switches."""
import logging

from drone_mobile.exceptions import CommandFailedError, DroneMobileException

from homeassistant.components.switch import SwitchEntity

from . import DroneMobileEntity
from .const import DOMAIN, SWITCHES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Switch Entities from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    entities = []

    for key, value in SWITCHES.items():
        entities.append(Switch(entry, key, config_entry.options))

    async_add_entities(entities, True)


class Switch(DroneMobileEntity, SwitchEntity):
    """Representation of a DroneMobile switch."""

    def __init__(self, coordinator, switch: str, options: dict):
        """Initialize the switch."""
        super().__init__(
            device_id=f"dronemobile_{switch}",
            name=f"{coordinator.data['vehicle_name']}_{switch}_Switch",
            coordinator=coordinator,
        )
        self.switch = switch
        self._state = self.is_on
        # Required for HA 2022.7
        self.coordinator_context = object()

    async def async_turn_on(self, **kwargs):
        """Turn on the switch."""
        if self.is_on:
            _LOGGER.debug("Switch already on, skipping")
            return

        _LOGGER.debug("Turning on %s for %s", self.switch, self.coordinator.data["vehicle_name"])

        try:
            if self.switch == "remoteStart":
                response = await self.coordinator.hass.async_add_executor_job(
                    self.coordinator.vehicle.start
                )
            elif self.switch == "panic":
                response = await self.coordinator.hass.async_add_executor_job(
                    self.coordinator.vehicle.panic_on
                )
            elif self.switch == "aux1":
                response = await self.coordinator.hass.async_add_executor_job(
                    self.coordinator.vehicle.aux1
                )
            elif self.switch == "aux2":
                response = await self.coordinator.hass.async_add_executor_job(
                    self.coordinator.vehicle.aux2
                )
            else:
                _LOGGER.warning("Unknown switch type: %s", self.switch)
                return

            _LOGGER.info("Turn on command result: %s", response.message)

            # Update state flags
            if self.switch == "remoteStart":
                self.coordinator.data["remote_start_status"] = True
            elif self.switch == "panic":
                self.coordinator.data["panic_status"] = True

            # Refresh coordinator data
            await self.coordinator.async_refresh()
            self._state = self.get_is_on_value(True, True)
            self.async_write_ha_state()

        except CommandFailedError as err:
            _LOGGER.error("Failed to turn on %s: %s", self.switch, err)
        except DroneMobileException as err:
            _LOGGER.error("Error turning on %s: %s", self.switch, err)

    async def async_turn_off(self, **kwargs):
        """Turn off the switch."""
        if not self.is_on:
            _LOGGER.debug("Switch already off, skipping")
            return

        _LOGGER.debug("Turning off %s for %s", self.switch, self.coordinator.data["vehicle_name"])

        try:
            if self.switch == "remoteStart":
                response = await self.coordinator.hass.async_add_executor_job(
                    self.coordinator.vehicle.stop
                )
            elif self.switch == "panic":
                response = await self.coordinator.hass.async_add_executor_job(
                    self.coordinator.vehicle.panic_off
                )
            else:
                _LOGGER.warning("Cannot turn off %s", self.switch)
                return

            _LOGGER.info("Turn off command result: %s", response.message)

            # Update state flags
            if self.switch == "remoteStart":
                self.coordinator.data["remote_start_status"] = False
            elif self.switch == "panic":
                self.coordinator.data["panic_status"] = False

            # Refresh coordinator data
            await self.coordinator.async_refresh()
            self._state = self.get_is_on_value(True, False)
            self.async_write_ha_state()

        except CommandFailedError as err:
            _LOGGER.error("Failed to turn off %s: %s", self.switch, err)
        except DroneMobileException as err:
            _LOGGER.error("Error turning off %s: %s", self.switch, err)

    async def async_toggle(self, **kwargs):
        """Toggle the switch."""
        _LOGGER.debug("Toggling %s for %s", self.switch, self.coordinator.data["vehicle_name"])

        try:
            manual_value = False

            if self.switch == "remoteStart":
                if self.is_on:
                    response = await self.coordinator.hass.async_add_executor_job(
                        self.coordinator.vehicle.stop
                    )
                else:
                    response = await self.coordinator.hass.async_add_executor_job(
                        self.coordinator.vehicle.start
                    )
                    manual_value = True
            elif self.switch == "panic":
                if self.is_on:
                    response = await self.coordinator.hass.async_add_executor_job(
                        self.coordinator.vehicle.panic_off
                    )
                else:
                    response = await self.coordinator.hass.async_add_executor_job(
                        self.coordinator.vehicle.panic_on
                    )
                    manual_value = True
            elif self.switch == "aux1":
                response = await self.coordinator.hass.async_add_executor_job(
                    self.coordinator.vehicle.aux1
                )
            elif self.switch == "aux2":
                response = await self.coordinator.hass.async_add_executor_job(
                    self.coordinator.vehicle.aux2
                )
            else:
                _LOGGER.warning("Unknown switch type: %s", self.switch)
                return

            _LOGGER.info("Toggle command result: %s", response.message)

            # Update state flags
            if self.switch == "remoteStart":
                self.coordinator.data["remote_start_status"] = manual_value
            elif self.switch == "panic":
                self.coordinator.data["panic_status"] = manual_value

            # Refresh coordinator data
            await self.coordinator.async_refresh()
            self._state = self.get_is_on_value(True, manual_value)
            self.async_write_ha_state()

        except CommandFailedError as err:
            _LOGGER.error("Failed to toggle %s: %s", self.switch, err)
        except DroneMobileException as err:
            _LOGGER.error("Error toggling %s: %s", self.switch, err)

    def get_is_on_value(self, called_from_action: bool = False, manual_value: bool = False) -> bool | None:
        """Determine if the switch is on."""
        status = self.coordinator.data.get("_status")

        if self.switch == "remoteStart":
            if not status:
                return None
            if called_from_action:
                return self.coordinator.data.get("remote_start_status") == manual_value
            return status.is_running

        elif self.switch == "panic":
            if called_from_action:
                return self.coordinator.data.get("panic_status") == manual_value
            return self.coordinator.data.get("panic_status", False)

        # Aux1 and Aux2 are momentary switches
        elif self.switch in ["aux1", "aux2"]:
            return manual_value

        _LOGGER.error("Unknown switch type: %s", self.switch)
        return None

    @property
    def is_on(self) -> bool | None:
        """Return true if switch is on."""
        return self.get_is_on_value()

    @property
    def icon(self) -> str:
        """Return the icon."""
        return SWITCHES[self.switch]["icon"]