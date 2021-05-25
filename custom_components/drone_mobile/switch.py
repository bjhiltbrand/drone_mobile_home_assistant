import logging

from homeassistant.components.switch import SwitchEntity

from . import DroneMobileEntity
from .const import DOMAIN, SWITCHES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Switch Entities from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    switches = []
    for key, value in SWITCHES.items():
        async_add_entities([Switch(entry, key)], True)
        
class Switch(DroneMobileEntity,SwitchEntity):
    def __init__(self, coordinator, switch):
        """Initialize."""
        super().__init__(
            device_id="dronemobile_" + switch,
            name=coordinator.data["vehicle_name"] + "_" + switch,
            coordinator=coordinator,
        )
        self.switch = switch
    
    async def async_turn_on(self, **kwargs):
        """switches on the vehicle device."""
        if self.is_on:
            return
        _LOGGER.debug("switching on %s " + self.switch, self.coordinator.data['vehicle_name'])
        command_call = None
        if self.switch == "remoteStart":
            command_call = self.coordinator.vehicle.start
        elif self.switch == "panic":
            command_call = self.coordinator.vehicle.panic
        elif self.switch == "aux1":
            command_call = self.coordinator.vehicle.remote_aux1
        elif self.switch == "aux2":
            command_call = self.coordinator.vehicle.remote_aux2
        else:
            return
        response = await self.coordinator.hass.async_add_executor_job(
            command_call, self.coordinator.data["device_key"]
        )
        self.coordinator.update_data_from_response(self.coordinator, response)

    async def async_turn_off(self, **kwargs):
        """switches off the vehicle device."""
        if not self.is_on:
            return
        _LOGGER.debug("Switching off %s " + self.switch, self.coordinator.data['vehicle_name'])
        command_call = None
        if self.switch == "remoteStart":
            command_call = self.coordinator.vehicle.stop
        elif self.switch == "panic":
            command_call = self.coordinator.vehicle.panic
        elif self.switch == "aux1":
            command_call = self.coordinator.vehicle.remote_aux1
        elif self.switch == "aux2":
            command_call = self.coordinator.vehicle.remote_aux2
        else:
            return
        response = await self.coordinator.hass.async_add_executor_job(
            command_call, self.coordinator.data["device_key"]
        )
        self.coordinator.update_data_from_response(self.coordinator, response)

    async def async_toggle(self, **kwargs):
        """Toggles the vehicle switch."""
        _LOGGER.debug("Toggling %s " + self.switch, self.coordinator.data['vehicle_name'])
        command_call = None
        if self.switch == "remoteStart":
            if self.is_on:
                command_call = self.coordinator.vehicle.remoteStop
            else:
                command_call = self.coordinator.vehicle.remoteStart
        elif self.switch == "panic":
            command_call = self.coordinator.vehicle.panic
        elif self.switch == "aux1":
            command_call = self.coordinator.vehicle.remote_aux1
        elif self.switch == "aux2":
            command_call = self.coordinator.vehicle.remote_aux2
            return
        response = await self.coordinator.hass.async_add_executor_job(
            command_call, self.coordinator.data["device_key"]
        )
        self.coordinator.update_data_from_response(self.coordinator, response)

    @property
    def is_on(self):
        """Determine if the switch is switched."""
        if self.switch == "remoteStart":
            if (self.coordinator.data is None or self.coordinator.data["remote_start_status"] is None):
                return None
            return self.coordinator.data["remote_start_status"] == "true"
        elif self.switch == "panic":
            if (self.coordinator.data is None or self.coordinator.data["panic_status"] is None):
                return None
            return self.coordinator.data["panic_status"] == "true"
        #These will need their own check for status, as they don't have values in the payload (most likely will depend on individual button mappings for various cars.)
        elif self.switch == "aux1":
            if (self.coordinator.data is None or self.coordinator.data["last_known_state"]["controller"]["trunk_open"] is None):
                return None
            return self.coordinator.data["last_known_state"]["controller"]["trunk_open"] == "false"
        elif self.switch == "aux2":
            if (self.coordinator.data is None or self.coordinator.data["last_known_state"]["controller"]["trunk_open"] is None):
                return None
            return self.coordinator.data["last_known_state"]["controller"]["trunk_open"] == "false"
        else:
            _LOGGER.error("Entry not found in SWITCHES: " + self.switch)

    @property
    def icon(self):
        return SWITCHES[self.switch]["icon"]
