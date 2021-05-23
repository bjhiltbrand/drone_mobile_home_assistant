import logging

from homeassistant.components.switch import SwitchEntity

from . import DroneMobileEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Switch from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]

    switches = [Switch(entry)]
    async_add_entities(switches, False)


class Switch(DroneMobileEntity, SwitchEntity):
    """Define the Switch for turning ignition off/on"""

    def __init__(self, coordinator):
        super().__init__(
            device_id="dronemobile_remotestart",
            name=coordinator.data["vehicle_name"] + "_remoteStart",
            coordinator=coordinator,
        )

    async def async_turn_on(self, **kwargs):
        response = await self.coordinator.hass.async_add_executor_job(
            self.coordinator.vehicle.start, self.coordinator.data["device_key"]
        )
        self.coordinator.update_data_from_response(response)

    async def async_turn_off(self, **kwargs):
        response = await self.coordinator.hass.async_add_executor_job(
            self.coordinator.vehicle.stop, self.coordinator.data["device_key"]
        )
        self.coordinator.update_data_from_response(response)

    @property
    def is_on(self):
        """Determine if the vehicle is started."""
        if (
            self.coordinator.data is None
            or self.coordinator.data["remote_start_status"] is None
        ):
            return None
        return self.coordinator.data["remote_start_status"]

    @property
    def icon(self):
        return "mdi:key-star"
