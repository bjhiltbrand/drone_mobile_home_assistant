"""Config flow for DroneMobile integration."""
from __future__ import annotations

import logging
from typing import Any

from drone_mobile import DroneMobileClient
from drone_mobile.exceptions import AuthenticationError, DroneMobileException
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_OVERRIDE_LOCK_STATE_CHECK,
    CONF_UNIT,
    CONF_UNITS,
    CONF_UPDATE_INTERVAL,
    CONF_VEHICLE_ID,
    DEFAULT_OVERRIDE_LOCK_STATE_CHECK,
    DEFAULT_UNIT,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class DroneMobileConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DroneMobile."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._username: str | None = None
        self._password: str | None = None
        self._unit: str = DEFAULT_UNIT
        self._update_interval: int = DEFAULT_UPDATE_INTERVAL
        self._override_lock_state_check: bool = DEFAULT_OVERRIDE_LOCK_STATE_CHECK
        self._vehicles: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate credentials
                await self._async_validate_credentials(
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )

                # Store credentials
                self._username = user_input[CONF_USERNAME]
                self._password = user_input[CONF_PASSWORD]
                self._unit = user_input[CONF_UNIT]
                self._update_interval = user_input[CONF_UPDATE_INTERVAL]
                self._override_lock_state_check = user_input[CONF_OVERRIDE_LOCK_STATE_CHECK]

                # Move to vehicle selection
                return await self.async_step_select_vehicle()

            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except DroneMobileException:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during authentication")
                errors["base"] = "unknown"

        # Show form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Required(CONF_UNIT, default=DEFAULT_UNIT): vol.In(CONF_UNITS),
                    vol.Required(
                        CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                    ): vol.All(vol.Coerce(int), vol.Range(min=2, max=60)),
                    vol.Required(
                        CONF_OVERRIDE_LOCK_STATE_CHECK,
                        default=DEFAULT_OVERRIDE_LOCK_STATE_CHECK,
                    ): bool,
                }
            ),
            errors=errors,
        )

    async def async_step_select_vehicle(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle vehicle selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            vehicle_id = user_input[CONF_VEHICLE_ID]
            vehicle_name = self._vehicles[vehicle_id]

            # Set unique ID and check if already configured
            await self.async_set_unique_id(f"{DOMAIN}_{vehicle_id}")
            self._abort_if_unique_id_configured()

            # Create entry
            return self.async_create_entry(
                title=vehicle_name,
                data={
                    CONF_USERNAME: self._username,
                    CONF_PASSWORD: self._password,
                    CONF_VEHICLE_ID: vehicle_id,
                },
                options={
                    CONF_UNIT: self._unit,
                    CONF_UPDATE_INTERVAL: self._update_interval,
                    CONF_OVERRIDE_LOCK_STATE_CHECK: self._override_lock_state_check,
                },
            )

        # Get list of vehicles
        try:
            self._vehicles = await self._async_get_vehicles(
                self._username, self._password
            )

            # Filter out already configured vehicles
            configured_vehicles = {
                entry.data[CONF_VEHICLE_ID]
                for entry in self._async_current_entries()
            }
            available_vehicles = {
                vid: name
                for vid, name in self._vehicles.items()
                if vid not in configured_vehicles
            }

            if not available_vehicles:
                return self.async_abort(reason="no_vehicles_available")

            self._vehicles = available_vehicles

        except DroneMobileException:
            errors["base"] = "cannot_connect"
            return self.async_show_form(
                step_id="select_vehicle",
                errors=errors,
            )

        # Show vehicle selection form
        return self.async_show_form(
            step_id="select_vehicle",
            data_schema=vol.Schema(
                {vol.Required(CONF_VEHICLE_ID): vol.In(self._vehicles)}
            ),
            errors=errors,
        )

    async def _async_validate_credentials(
        self, username: str, password: str
    ) -> None:
        """Validate the user credentials."""

        def _validate() -> bool:
            """Validate credentials synchronously."""
            client = DroneMobileClient(username, password)
            try:
                # Try to get vehicles to validate credentials
                vehicles = client.get_vehicles()
                return len(vehicles) >= 0
            finally:
                client.close()

        await self.hass.async_add_executor_job(_validate)

    async def _async_get_vehicles(
        self, username: str, password: str
    ) -> dict[str, str]:
        """Get list of vehicles from DroneMobile."""

        def _get_vehicles() -> dict[str, str]:
            """Get vehicles synchronously."""
            client = DroneMobileClient(username, password)
            try:
                vehicles = client.get_vehicles()
                return {vehicle.vehicle_id: vehicle.name for vehicle in vehicles}
            finally:
                client.close()

        return await self.hass.async_add_executor_job(_get_vehicles)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> DroneMobileOptionsFlow:
        """Get the options flow for this handler."""
        return DroneMobileOptionsFlow(config_entry)


class DroneMobileOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for DroneMobile."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_UNIT,
                        default=self.config_entry.options.get(CONF_UNIT, DEFAULT_UNIT),
                    ): vol.In(CONF_UNITS),
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=2, max=60)),
                    vol.Optional(
                        CONF_OVERRIDE_LOCK_STATE_CHECK,
                        default=self.config_entry.options.get(
                            CONF_OVERRIDE_LOCK_STATE_CHECK,
                            DEFAULT_OVERRIDE_LOCK_STATE_CHECK,
                        ),
                    ): bool,
                }
            ),
        )