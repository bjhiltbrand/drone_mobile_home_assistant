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
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_UNIT_SYSTEM,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_UNIT_SYSTEM,
    DOMAIN,
    ERROR_AUTH,
    ERROR_CANNOT_CONNECT,
    ERROR_UNKNOWN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    UNIT_SYSTEM_IMPERIAL,
    UNIT_SYSTEM_METRIC,
)

_LOGGER = logging.getLogger(__name__)

CONF_VEHICLE = "vehicle"


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.
    
    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    try:
        client = DroneMobileClient(data[CONF_USERNAME], data[CONF_PASSWORD])
        # Client authenticates automatically in 0.3.0
    except AuthenticationError as err:
        raise ValueError(ERROR_AUTH) from err
    except DroneMobileException as err:
        raise ValueError(ERROR_CANNOT_CONNECT) from err

    # Get vehicles to verify connection
    try:
        vehicles = await hass.async_add_executor_job(client.get_vehicles)
    except DroneMobileException as err:
        raise ValueError(ERROR_CANNOT_CONNECT) from err
    
    if not vehicles:
        raise ValueError("No vehicles found")

    return {
        "title": f"DroneMobile ({data[CONF_USERNAME]})",
        "vehicles": vehicles,
    }


class DroneMobileConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DroneMobile."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._vehicles: list | None = None
        self._username: str | None = None
        self._password: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                
                # Store credentials and vehicles for vehicle selection step
                self._username = user_input[CONF_USERNAME]
                self._password = user_input[CONF_PASSWORD]
                self._vehicles = info["vehicles"]
                
                # If only one vehicle, skip selection and configure directly
                if len(self._vehicles) == 1:
                    vehicle = self._vehicles[0]
                    
                    # Check if already configured
                    await self.async_set_unique_id(vehicle.vehicle_id)
                    self._abort_if_unique_id_configured()
                    
                    return self.async_create_entry(
                        title=f"{vehicle.name}",
                        data={
                            CONF_USERNAME: self._username,
                            CONF_PASSWORD: self._password,
                            CONF_VEHICLE: vehicle.vehicle_id,
                        },
                        options={
                            CONF_UNIT_SYSTEM: DEFAULT_UNIT_SYSTEM,
                            CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
                        },
                    )
                
                # Multiple vehicles, show selection step
                return await self.async_step_vehicle()
                
            except ValueError as err:
                if str(err) == ERROR_AUTH:
                    errors["base"] = ERROR_AUTH
                elif str(err) == ERROR_CANNOT_CONNECT:
                    errors["base"] = ERROR_CANNOT_CONNECT
                else:
                    errors["base"] = ERROR_UNKNOWN
                    _LOGGER.exception("Unexpected exception: %s", err)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = ERROR_UNKNOWN

        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_vehicle(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle vehicle selection step."""
        if user_input is not None:
            vehicle_id = user_input[CONF_VEHICLE]
            
            # Find the selected vehicle
            vehicle = next(
                (v for v in self._vehicles if v.vehicle_id == vehicle_id), 
                None
            )
            
            if vehicle is None:
                return self.async_abort(reason="vehicle_not_found")
            
            # Check if already configured
            await self.async_set_unique_id(vehicle.vehicle_id)
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(
                title=f"{vehicle.name}",
                data={
                    CONF_USERNAME: self._username,
                    CONF_PASSWORD: self._password,
                    CONF_VEHICLE: vehicle.vehicle_id,
                },
                options={
                    CONF_UNIT_SYSTEM: DEFAULT_UNIT_SYSTEM,
                    CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
                },
            )
        
        # Build vehicle choices
        vehicle_choices = {
            vehicle.vehicle_id: f"{vehicle.name} ({vehicle.info.make} {vehicle.info.model})"
            for vehicle in self._vehicles
        }
        
        data_schema = vol.Schema(
            {
                vol.Required(CONF_VEHICLE): vol.In(vehicle_choices),
            }
        )
        
        return self.async_show_form(
            step_id="vehicle",
            data_schema=data_schema,
            description_placeholders={
                "num_vehicles": str(len(self._vehicles)),
            },
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Handle reauthorization request."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reauthorization confirmation."""
        errors: dict[str, str] = {}

        if user_input is not None:
            entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
            assert entry is not None

            data = {**entry.data, CONF_PASSWORD: user_input[CONF_PASSWORD]}

            try:
                await validate_input(self.hass, data)
            except ValueError as err:
                if str(err) == ERROR_AUTH:
                    errors["base"] = ERROR_AUTH
                else:
                    errors["base"] = ERROR_CANNOT_CONNECT
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = ERROR_UNKNOWN
            else:
                self.hass.config_entries.async_update_entry(entry, data=data)
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> DroneMobileOptionsFlowHandler:
        """Get the options flow for this handler."""
        return DroneMobileOptionsFlowHandler(config_entry)


class DroneMobileOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle DroneMobile options."""

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
                    vol.Required(
                        CONF_UNIT_SYSTEM,
                        default=self.config_entry.options.get(
                            CONF_UNIT_SYSTEM, DEFAULT_UNIT_SYSTEM
                        ),
                    ): vol.In([UNIT_SYSTEM_IMPERIAL, UNIT_SYSTEM_METRIC]),
                    vol.Required(
                        CONF_UPDATE_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                        ),
                    ): vol.All(
                        cv.positive_int,
                        vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                    ),
                }
            ),
        )