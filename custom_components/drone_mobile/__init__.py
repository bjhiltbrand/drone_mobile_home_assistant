"""The DroneMobile integration for Home Assistant."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

from drone_mobile import DroneMobileClient
from drone_mobile.exceptions import (
    AuthenticationError,
    DroneMobileException,
    NetworkError,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_OVERRIDE_LOCK_STATE_CHECK,
    CONF_UNIT,
    CONF_UPDATE_INTERVAL,
    CONF_VEHICLE_ID,
    DEFAULT_OVERRIDE_LOCK_STATE_CHECK,
    DEFAULT_UNIT,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MANUFACTURER,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.LOCK,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.DEVICE_TRACKER,
]


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

    # Create coordinator
    coordinator = DroneMobileDataUpdateCoordinator(
        hass=hass,
        username=username,
        password=password,
        vehicle_id=vehicle_id,
        update_interval=update_interval,
        override_lock_state_check=override_lock_state_check,
    )

    # Perform initial data fetch
    try:
        await coordinator.async_config_entry_first_refresh()
    except AuthenticationError as err:
        raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
    except DroneMobileException as err:
        raise ConfigEntryNotReady(f"Failed to connect: {err}") from err

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    await _async_register_services(hass, coordinator)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        # Close the client session
        if coordinator.client:
            await hass.async_add_executor_job(coordinator.client.close)

    return unload_ok


async def _async_register_services(
    hass: HomeAssistant, coordinator: DroneMobileDataUpdateCoordinator
) -> None:
    """Register services for the vehicle."""
    vehicle_name = coordinator.vehicle.name.replace(" ", "_").lower()

    async def async_refresh_device_status(call: ServiceCall) -> None:
        """Service to refresh device status."""
        _LOGGER.debug("Refreshing device status for %s", coordinator.vehicle.name)
        try:
            await hass.async_add_executor_job(coordinator.vehicle.poll_status)
            await coordinator.async_request_refresh()
        except DroneMobileException as err:
            _LOGGER.error("Failed to refresh device status: %s", err)

    async def async_dump_device_data(call: ServiceCall) -> None:
        """Service to dump device data to file."""
        _LOGGER.debug("Dumping device data for %s", coordinator.vehicle.name)
        try:
            import json
            from pathlib import Path

            output_file = (
                Path(hass.config.config_dir)
                / f"drone_mobile_data_{vehicle_name}.json"
            )
            
            data = {
                "vehicle_info": coordinator.vehicle.info.raw_data,
                "vehicle_status": coordinator.data.raw_data if coordinator.data else {},
            }
            
            await hass.async_add_executor_job(
                lambda: output_file.write_text(json.dumps(data, indent=2))
            )
            _LOGGER.info("Device data dumped to %s", output_file)
        except Exception as err:
            _LOGGER.error("Failed to dump device data: %s", err)

    # Register services with vehicle-specific names
    hass.services.async_register(
        DOMAIN,
        f"refresh_device_status_{vehicle_name}",
        async_refresh_device_status,
    )

    hass.services.async_register(
        DOMAIN,
        f"dump_device_data_{vehicle_name}",
        async_dump_device_data,
    )


class DroneMobileDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching DroneMobile data."""

    def __init__(
        self,
        hass: HomeAssistant,
        username: str,
        password: str,
        vehicle_id: str,
        update_interval: timedelta,
        override_lock_state_check: bool,
    ) -> None:
        """Initialize the coordinator."""
        self.client: DroneMobileClient | None = None
        self.vehicle = None
        self._username = username
        self._password = password
        self._vehicle_id = vehicle_id
        self.override_lock_state_check = override_lock_state_check

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{vehicle_id}",
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> Any:
        """Fetch data from DroneMobile."""
        try:
            # Initialize client if needed
            if self.client is None:
                self.client = await self.hass.async_add_executor_job(
                    DroneMobileClient, self._username, self._password
                )
                
                # Get the vehicle
                self.vehicle = await self.hass.async_add_executor_job(
                    self.client.get_vehicle, self._vehicle_id
                )
                
                _LOGGER.debug(
                    "Initialized DroneMobile client for vehicle: %s",
                    self.vehicle.name,
                )

            # Fetch vehicle status
            status = await self.hass.async_add_executor_job(
                self.vehicle.get_status, False  # Don't use cache
            )

            _LOGGER.debug(
                "Updated status for %s: Running=%s, Locked=%s",
                self.vehicle.name,
                status.is_running,
                status.is_locked,
            )

            return status

        except AuthenticationError as err:
            raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
        except NetworkError as err:
            raise UpdateFailed(f"Network error: {err}") from err
        except DroneMobileException as err:
            raise UpdateFailed(f"Error communicating with DroneMobile: {err}") from err


class DroneMobileEntity(CoordinatorEntity[DroneMobileDataUpdateCoordinator]):
    """Base class for DroneMobile entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DroneMobileDataUpdateCoordinator,
        entity_type: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        
        self._attr_unique_id = f"{coordinator.vehicle.vehicle_id}_{entity_type}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.vehicle.vehicle_id)},
            "name": coordinator.vehicle.name,
            "manufacturer": MANUFACTURER,
            "model": coordinator.vehicle.info.make or "Unknown",
            "sw_version": coordinator.vehicle.info.year,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None