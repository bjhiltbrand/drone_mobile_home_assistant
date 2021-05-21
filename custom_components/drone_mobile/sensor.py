import logging
from datetime import datetime, timedelta

from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle, dt

from . import DroneMobileEntity
from .const import CONF_UNIT, DOMAIN, SENSORS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Entities from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    sensors = []
    for key, value in SENSORS.items():
        async_add_entities([CarSensor(entry, key, config_entry.options)], True)
        
class CarSensor(DroneMobileEntity,Entity,):
    def __init__(self, coordinator, sensor, options):
        self.sensor = sensor
        self.options = options
        self._attr = {}
        self.coordinator = coordinator
        self._device_id = "dronemobile_" + sensor

    def get_value(self, ftype):
        if ftype == "state":
            if self.sensor == "odometer":
                if self.options[CONF_UNIT] == "imperial":
                    return round(
                        float(self.coordinator.data["last_known_state"]["mileage"]) / 1.60934
                    )
                else:
                    return self.coordinator.data["last_known_state"]["mileage"]
            elif self.sensor == "battery":
                return self.coordinator.data["last_known_state"]["controller"]["main_battery_voltage"]
            elif self.sensor == "temperature":
                if self.options[CONF_UNIT] == "imperial":
                    return round(
                        float((self.coordinator.data["last_known_state"]["controller"]["current_temperature"]) * (9/5)) + 32
                    )
                else:
                    return self.coordinator.data["last_known_state"]["controller"]["current_temperature"]
            elif self.sensor == "gps":
                if self.coordinator.data["last_known_state"]["gps_direction"] == None:
                    return "Unsupported"
                return self.coordinator.data["last_known_state"]["gps_direction"]
            elif self.sensor == "alarm":
                return self.coordinator.data["last_known_state"]["controller"]["armed"]
            elif self.sensor == "ignitionStatus":
                return self.coordinator.data["last_known_state"]["controller"]["ignition_on"]
            elif self.sensor == "doorStatus":
                if self.coordinator.data["last_known_state"]["controller"]["door_open"] == "true":
                    return "Open"
                return "Closed"
            elif self.sensor == "lastRefresh":
                return dt.as_local(
                    datetime.strptime(
                        self.coordinator.data["update_date"], "%Y-%m-%dT%H:%M:%S%z"
                    )
                )
        elif ftype == "measurement":
            if self.sensor == "odometer":
                if self.options[CONF_UNIT] == "imperial":
                    return "mi"
                else:
                    return "km"
            elif self.sensor == "battery":
                return "V"
            elif self.sensor == "temperature":
                if self.options[CONF_UNIT] == "imperial":
                    return "°F"
                else:
                    return "°C"
            elif self.sensor == "gps":
                return None
            elif self.sensor == "alarm":
                return None
            elif self.sensor == "ignitionStatus":
                return None
            elif self.sensor == "doorStatus":
                return None
            elif self.sensor == "lastRefresh":
                return None
        elif ftype == "attribute":
            if self.sensor == "odometer":
                return self.coordinator.data.items()
            elif self.sensor == "battery":
                return {
                    "Battery Voltage": self.coordinator.data["last_known_state"]["controller"]["main_battery_voltage"]
                }
            elif self.sensor == "temperature":
                return self.coordinator.data.items()
            elif self.sensor == "gps":
                if self.coordinator.data["last_known_state"]["gps_direction"] == None:
                    return None
                return self.coordinator.data.items()
            elif self.sensor == "alarm":
                return self.coordinator.data.items()
            elif self.sensor == "ignitionStatus":
                return self.coordinator.data.items()
            elif self.sensor == "doorStatus":
                return self.coordinator.data.items()
            elif self.sensor == "lastRefresh":
                return None
            else:
                return None

    @property
    def name(self):
        return self.coordinator.data["vehicle_name"] + "_" + self.sensor

    @property
    def state(self):
        return self.get_value("state")

    @property
    def device_id(self):
        return self.device_id

    @property
    def device_state_attributes(self):
        return self.get_value("attribute")

    @property
    def unit_of_measurement(self):
        return self.get_value("measurement")

    @property
    def icon(self):
        return SENSORS[self.sensor]["icon"]
