"""The DroneMobile integration."""
import asyncio
from datetime import timedelta
import logging
from typing import Any

from drone_mobile import DroneMobileClient
from drone_mobile.exceptions import (
    AuthenticationError,
    DroneMobileException,
    VehicleNotFoundError,
)
from drone_mobile.vehicle import Vehicle
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_UNIT,
    CONF_UPDATE_INTERVAL,
    CONF_VEHICLE_ID,
    CONF_OVERRIDE_LOCK_STATE_CHECK,
    DEFAULT_UNIT,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_OVERRIDE_LOCK_STATE_CHECK,
    DOMAIN,
    MANUFACTURER,
)

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

PLATFORMS = [
    Platform.LOCK,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.DEVICE_TRACKER,
]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the DroneMobile component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up DroneMobile from a config entry."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    vehicle_id = entry.data[CONF_VEHICLE_ID]
    update_interval = timedelta(
        minutes=entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    )
    override_lock_state_check = entry.options.get(
        CONF_OVERRIDE_LOCK_STATE_CHECK, DEFAULT_OVERRIDE_LOCK_STATE_CHECK
    )

    coordinator = DroneMobileDataUpdateCoordinator(
        hass, username, password, update_interval, override_lock_state_check, vehicle_id
    )

    if not entry.options:
        await async_update_options(hass, entry)

    try:
        await coordinator.async_config_entry_first_refresh()
    except AuthenticationError as err:
        raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
    except DroneMobileException as err:
        raise ConfigEntryNotReady(f"Failed to connect: {err}") from err

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    vehicle_name_safe = coordinator.vehicle.name.replace(" ", "_")

    async def async_refresh_device_status_service(call):
        """Refresh device status."""
        await hass.async_add_executor_job(coordinator.refresh_device_status)
        await coordinator.async_refresh()

    async def async_dump_device_data_service(call):
        """Dump device data."""
        await hass.async_add_executor_job(coordinator.dump_device_data)

    hass.services.async_register(
        DOMAIN,
        f"refresh_device_status_{vehicle_name_safe}",
        async_refresh_device_status_service,
    )

    hass.services.async_register(
        DOMAIN,
        f"dump_device_data_{vehicle_name_safe}",
        async_dump_device_data_service,
    )

    return True


async def async_update_options(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Update options."""
    options = {
        CONF_UNIT: config_entry.options.get(CONF_UNIT, DEFAULT_UNIT),
        CONF_UPDATE_INTERVAL: config_entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        ),
        CONF_OVERRIDE_LOCK_STATE_CHECK: config_entry.options.get(
            CONF_OVERRIDE_LOCK_STATE_CHECK, DEFAULT_OVERRIDE_LOCK_STATE_CHECK
        ),
    }
    hass.config_entries.async_update_entry(config_entry, options=options)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        # Close the client session
        await hass.async_add_executor_job(coordinator.client.close)

    return unload_ok


class DroneMobileDataUpdateCoordinator(DataUpdateCoordinator):
    """DataUpdateCoordinator to handle fetching new data about the vehicle."""

    def __init__(
        self,
        hass: HomeAssistant,
        username: str,
        password: str,
        update_interval: timedelta,
        override_lock_state_check: bool,
        vehicle_id: str,
    ):
        """Initialize the coordinator."""
        self._hass = hass
        self.username = username
        self.password = password
        self._vehicle_id = vehicle_id
        self._override_lock_state_check = override_lock_state_check
        self._available = True

        # Create the client
        self.client = DroneMobileClient(username, password)
        self.vehicle: Vehicle | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self._async_update_data,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from DroneMobile."""
        _LOGGER.debug("Retrieving vehicle status for DroneMobile")

        try:
            # Get the vehicle if we don't have it yet
            if self.vehicle is None:
                self.vehicle = await self._hass.async_add_executor_job(
                    self.client.get_vehicle, self._vehicle_id
                )

            # Get fresh status
            status = await self._hass.async_add_executor_job(
                self.vehicle.get_status, False  # use_cache=False
            )

            # Convert to dictionary format for backward compatibility
            data = self._build_data_dict(status)

            # Mark as available
            if not self._available:
                _LOGGER.info("Restored connection to DroneMobile")
                self._available = True

            return data

        except VehicleNotFoundError as err:
            self._available = False
            raise UpdateFailed(f"Vehicle {self._vehicle_id} not found") from err
        except AuthenticationError as err:
            self._available = False
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except DroneMobileException as err:
            self._available = False
            _LOGGER.warning("Error communicating with DroneMobile: %s", err)
            raise UpdateFailed(f"Error communicating with DroneMobile") from err

    def _build_data_dict(self, status) -> dict[str, Any]:
        """Build data dictionary from VehicleStatus object."""
        # Build a dictionary that maintains backward compatibility
        # with the old data structure while using new typed objects
        data = {
            "id": self.vehicle.vehicle_id,
            "vehicle_id": self.vehicle.vehicle_id,
            "device_key": self.vehicle.device_key,
            "vehicle_name": self.vehicle.name,
            "last_known_state": {
                "mileage": status.odometer or 0,
                "latitude": status.location.latitude if status.location else None,
                "longitude": status.location.longitude if status.location else None,
                "gps_direction": None,  # Not available in new API
                "timestamp": status.last_updated.isoformat() if status.last_updated else None,
                "controller": {
                    "main_battery_voltage": status.battery_voltage,
                    "current_temperature": status.interior_temperature,
                    "armed": status.is_locked,
                    "ignition_on": status.is_running,
                    "engine_on": status.is_running,
                    "door_open": False,  # Derived from lock state if available
                    "trunk_open": False,  # Not directly available
                    "hood_open": False,  # Not directly available
                    "controller_model": self.vehicle.info.make or "Unknown",
                },
            },
            # Store the actual objects for new code
            "_vehicle": self.vehicle,
            "_status": status,
            # Maintain flags for switch states
            "remote_start_status": status.is_running,
            "panic_status": False,
        }
        return data

    def refresh_device_status(self) -> None:
        """Refresh device status from the vehicle."""
        _LOGGER.debug("Refreshing Device Status")
        try:
            response = self.vehicle.poll_status()
            _LOGGER.debug("Device status refreshed: %s", response.message)
        except DroneMobileException as err:
            _LOGGER.error("Failed to refresh device status: %s", err)

    def dump_device_data(self) -> None:
        """Dump device data to file."""
        import json
        from pathlib import Path

        _LOGGER.debug("Dumping Device Data")
        filename = f"drone_mobile_device_data_{self.vehicle.name.replace(' ', '_')}.json"
        filepath = Path(self._hass.config.config_dir) / filename

        try:
            data = {
                "vehicle_info": self.vehicle.info.raw_data,
                "vehicle_status": self.data.get("_status").raw_data if "_status" in self.data else {},
            }
            with open(filepath, "w") as outfile:
                json.dump(data, outfile, indent=2, default=str)
            _LOGGER.info("Device data dumped to %s", filepath)
        except Exception as err:
            _LOGGER.error("Failed to dump device data: %s", err)


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
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the entity."""
        return f"{self.coordinator.data['id']}-{self._device_id}"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information about this device."""
        if self._device_id is None:
            return None

        vehicle = self.coordinator.vehicle
        return {
            "identifiers": {(DOMAIN, self.coordinator.data["id"])},
            "name": vehicle.name,
            "model": f"{vehicle.info.make} {vehicle.info.model}" if vehicle.info.make else "Unknown",
            "manufacturer": MANUFACTURER,
        }