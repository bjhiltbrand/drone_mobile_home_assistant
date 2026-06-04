"""Button platform for DroneMobile integration."""
import logging

from drone_mobile.exceptions import CommandFailedError, DroneMobileException

from homeassistant.components.button import ButtonEntity
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
    """Set up DroneMobile button entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        DroneMobileAux1Button(coordinator),
        DroneMobileAux2Button(coordinator),
        DroneMobileTrunkButton(coordinator),
        DroneMobileLocateButton(coordinator),
    ]

    async_add_entities(entities, True)


class DroneMobileAux1Button(DroneMobileEntity, ButtonEntity):
    """Auxiliary 1 button."""

    def __init__(self, coordinator) -> None:
        """Initialize the button."""
        super().__init__(
            coordinator=coordinator,
            device_id="aux1",
            name=f"{coordinator.vehicle.name} Aux 1",
        )
        self._attr_icon = "mdi:numeric-1-box-multiple"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.debug("Triggering Aux1 for %s", self.coordinator.vehicle.name)
        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.aux1)
        except CommandFailedError as err:
            _LOGGER.error("Failed to trigger Aux1: %s", err)
        except DroneMobileException as err:
            _LOGGER.error("Error triggering Aux1: %s", err)


class DroneMobileAux2Button(DroneMobileEntity, ButtonEntity):
    """Auxiliary 2 button."""

    def __init__(self, coordinator) -> None:
        """Initialize the button."""
        super().__init__(
            coordinator=coordinator,
            device_id="aux2",
            name=f"{coordinator.vehicle.name} Aux 2",
        )
        self._attr_icon = "mdi:numeric-2-box-multiple"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.debug("Triggering Aux2 for %s", self.coordinator.vehicle.name)
        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.aux2)
        except CommandFailedError as err:
            _LOGGER.error("Failed to trigger Aux2: %s", err)
        except DroneMobileException as err:
            _LOGGER.error("Error triggering Aux2: %s", err)


class DroneMobileTrunkButton(DroneMobileEntity, ButtonEntity):
    """Trunk release button."""

    def __init__(self, coordinator) -> None:
        """Initialize the button."""
        super().__init__(
            coordinator=coordinator,
            device_id="trunk_release",
            name=f"{coordinator.vehicle.name} Trunk",
        )
        self._attr_icon = "mdi:car-back"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.debug("Opening trunk for %s", self.coordinator.vehicle.name)
        try:
            await self.hass.async_add_executor_job(self.coordinator.vehicle.trunk)
        except CommandFailedError as err:
            _LOGGER.error("Failed to open trunk: %s", err)
        except DroneMobileException as err:
            _LOGGER.error("Error opening trunk: %s", err)


class DroneMobileLocateButton(DroneMobileEntity, ButtonEntity):
    """Request a fresh GPS location from the vehicle."""

    def __init__(self, coordinator) -> None:
        """Initialize the button."""
        super().__init__(
            coordinator=coordinator,
            device_id="locate",
            name=f"{coordinator.vehicle.name} Locate",
        )
        self._attr_icon = "mdi:crosshairs-gps"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.debug("Requesting location for %s", self.coordinator.vehicle.name)
        try:
            await self.hass.async_add_executor_job(
                self.coordinator.vehicle.get_location
            )
        except CommandFailedError as err:
            _LOGGER.error("Failed to request location: %s", err)
        except DroneMobileException as err:
            _LOGGER.error("Error requesting location: %s", err)