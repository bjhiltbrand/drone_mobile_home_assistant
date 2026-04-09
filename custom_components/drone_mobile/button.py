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