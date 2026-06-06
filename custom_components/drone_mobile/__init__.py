"""The DroneMobile integration."""
import asyncio
from datetime import timedelta
import logging

import voluptuous as vol
from drone_mobile import DroneMobileClient
from drone_mobile.exceptions import (
    AuthenticationError,
    DroneMobileException,
    MFARequiredError,
)
from drone_mobile.models import VehicleInfo

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
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MANUFACTURER,
    token_storage_dir,
)

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

PLATFORMS = [
    Platform.BUTTON,
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

    coordinator = DroneMobileDataUpdateCoordinator(
        hass, username, password, vehicle_id, update_interval
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryAuthFailed:
        # Re-raise so HA can start the re-auth flow.
        raise
    except AuthenticationError as err:
        raise ConfigEntryAuthFailed from err
    except DroneMobileException as err:
        raise ConfigEntryNotReady from err

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    vehicle_name_slug = coordinator.vehicle.name.replace(" ", "_").lower()

    async def async_refresh_device_status(call: ServiceCall) -> None:
        """Service to refresh device status."""
        await hass.async_add_executor_job(coordinator.refresh_device_status)
        await coordinator.async_refresh()

    hass.services.async_register(
        DOMAIN,
        f"refresh_device_status_{vehicle_name_slug}",
        async_refresh_device_status,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await hass.async_add_executor_job(coordinator.client.close)

    return unload_ok


class DroneMobileDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching DroneMobile data."""

    def __init__(
        self,
        hass: HomeAssistant,
        username: str,
        password: str,
        vehicle_id: str,
        update_interval: timedelta,
    ) -> None:
        """Initialize the coordinator.

        Note: No mfa_callback is passed to DroneMobileClient here.  After a
        successful initial config flow the library caches a token on disk, so
        subsequent refreshes use REFRESH_TOKEN_AUTH which bypasses MFA.  If
        the refresh token itself ever expires, Cognito would require MFA again;
        in that case MFARequiredError is treated as an authentication failure
        and HA will start its standard re-auth flow (which does include the MFA
        step via config_flow.async_step_mfa).
        """
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.vehicle_id = vehicle_id
        self.client = DroneMobileClient(
            username, password, token_dir=token_storage_dir(hass)
        )
        self.vehicle = None
        self._available = True

    async def _async_update_data(self):
        """Fetch data from DroneMobile API."""
        try:
            # Get vehicle if not cached
            if self.vehicle is None:
                self.vehicle = await self.hass.async_add_executor_job(
                    self.client.get_vehicle, self.vehicle_id
                )

            # Get current status
            status = await self.hass.async_add_executor_job(
                self.vehicle.get_status, False  # Don't use cache
            )

            if not self._available:
                _LOGGER.info("Restored connection to DroneMobile")
                self._available = True

            return {
                "vehicle": self.vehicle,
                "status": status,
                "info": self.vehicle.info,
            }

        except MFARequiredError as err:
            # The cached refresh token has expired and Cognito is asking for a
            # second factor again.  We cannot complete MFA headlessly here, so
            # treat this as an authentication failure and let HA's re-auth flow
            # handle it (which will route through config_flow.async_step_mfa).
            _LOGGER.warning(
                "MFA challenge '%s' required during token refresh for vehicle %s. "
                "Re-authentication is needed.",
                err.challenge_name,
                self.vehicle_id,
            )
            raise ConfigEntryAuthFailed(
                "MFA re-authentication required. Please re-authenticate the integration."
            ) from err

        except AuthenticationError as err:
            raise ConfigEntryAuthFailed("Authentication failed") from err

        except DroneMobileException as err:
            self._available = False
            _LOGGER.warning(
                "Error communicating with DroneMobile for %s: %s",
                self.vehicle_id,
                err,
            )
            raise UpdateFailed(f"Error communicating with DroneMobile: {err}") from err

    def refresh_device_status(self) -> None:
        """Poll the device for status updates."""
        if self.vehicle:
            _LOGGER.debug("Polling device status for %s", self.vehicle.name)
            self.vehicle.poll_status()


class DroneMobileEntity(CoordinatorEntity):
    """Defines a base DroneMobile entity."""

    def __init__(
        self,
        coordinator: DroneMobileDataUpdateCoordinator,
        device_id: str,
        name: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.vehicle_id}_{device_id}"

    @property
    def device_info(self):
        """Return device information about this entity."""
        info = self.coordinator.data["info"]
        model = (
            f"{info.year} {info.make} {info.model}"
            if info.year and info.make and info.model
            else "Unknown Model"
        )

        return {
            "identifiers": {(DOMAIN, self.coordinator.vehicle_id)},
            "name": info.name,
            "manufacturer": MANUFACTURER,
            "model": model,
        }