"""The DroneMobile integration."""
import asyncio
import logging
from datetime import timedelta

import async_timeout
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_UNIT,
    DEFAULT_UNIT,
    DOMAIN,
    VEHICLE,
    CONF_VEHICLE_ID,
    CONF_UPDATE_INTERVAL,
    MANUFACTURER,
)
from .droneMobile_new import Vehicle

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

PLATFORMS = ["lock", "sensor", "switch", "device_tracker"]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the DroneMobile component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up DroneMobile from a config entry."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    vehicleID = entry.data[CONF_VEHICLE_ID]
    updateInterval = timedelta(seconds=(entry.data[CONF_UPDATE_INTERVAL] * 60))

    coordinator = DroneMobileDataUpdateCoordinator(
        hass, username, password, updateInterval, vehicleID
    )

    await coordinator.async_refresh()  # Get initial data

    if not entry.options:
        await async_update_options(hass, entry)

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    async def async_refresh_status_service(service_call):
        await hass.async_add_executor_job(
            refresh_status, hass, service_call, coordinator
        )

    async def async_clear_tokens_service(service_call):
        await hass.async_add_executor_job(clear_tokens, hass, service_call, coordinator)

    hass.services.async_register(
        DOMAIN,
        "refresh_status",
        async_refresh_status_service,
    )
    hass.services.async_register(
        DOMAIN,
        "clear_tokens",
        async_clear_tokens_service,
    )

    return True


async def async_update_options(hass, config_entry):
    options = {CONF_UNIT: config_entry.data.get(CONF_UNIT, DEFAULT_UNIT)}
    hass.config_entries.async_update_entry(config_entry, options=options)


def refresh_status(service, hass, coordinator):
    _LOGGER.debug("Running Service")
    coordinator.vehicle.requestUpdate()


def clear_tokens(service, hass, coordinator):
    _LOGGER.debug("Clearing Tokens")
    coordinator.vehicle.clearToken()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class DroneMobileDataUpdateCoordinator(DataUpdateCoordinator):
    """DataUpdateCoordinator to handle fetching new data about the vehicle."""

    def __init__(self, hass, username, password, updateInterval, vehicleID):
        """Initialize the coordinator and set up the Vehicle object."""
        self._hass = hass
        self.vehicle = Vehicle(username, password)
        self._vehicleID = vehicleID
        self._available = True

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=updateInterval,
        )

    async def _async_update_data(self):
        """Fetch data from DroneMobile."""

        _LOGGER.debug(f"Retrieving vehicles for account {self.vehicle.username}")
        
        try:
            async with async_timeout.timeout(30):
                vehicles = await self._hass.async_add_executor_job(
                    self.vehicle.status  # Fetch new status
                )

                # If data has now been fetched but was previously unavailable, log and reset
                if not self._available:
                    _LOGGER.info(f"Restored connection to DroneMobile for {self.vehicle.username}")
                    self._available = True
                for vehicle in vehicles:
                    if vehicle["id"] == self._vehicleID:
                        return vehicle
        except Exception as ex:
            self._available = False  # Mark as unavailable
            _LOGGER.warning(str(ex))
            _LOGGER.warning(
                "Error communicating with DroneMobile for %s", self.vehicle.username
            )
            raise UpdateFailed(
                f"Error communicating with DroneMobile for {self.vehicle.username}"
            ) from ex


class DroneMobileEntity(CoordinatorEntity):
    """Defines a base DroneMobile entity."""

    def __init__(
        self,
        *,
        device_id: str,
        name: str,
        coordinator: DroneMobileDataUpdateCoordinator,
    ):
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._name = name

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID of the entity."""
        return f"{self.coordinator.data['id']}-{self._device_id}"

    @property
    def device_info(self):
        """Return device information about this device."""
        if self._device_id is None:
            return None

        return {
            "identifiers": {(DOMAIN, self.coordinator.data["id"])},
            "name": self.coordinator.data["vehicle_name"],
            "model": self.coordinator.data["last_known_state"]["controller_model"],
            "manufacturer": MANUFACTURER,
        }
