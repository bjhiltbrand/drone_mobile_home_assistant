"""Config flow for DroneMobile integration."""
import logging

from drone_mobile import DroneMobileClient
from drone_mobile.exceptions import AuthenticationError, DroneMobileException, MFARequiredError
import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback

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
    token_storage_dir,
)

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_UNIT, default=DEFAULT_UNIT): vol.In(CONF_UNITS),
        vol.Required(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=2, max=60)
        ),
        vol.Required(
            CONF_OVERRIDE_LOCK_STATE_CHECK, default=DEFAULT_OVERRIDE_LOCK_STATE_CHECK
        ): bool,
    }
)

MFA_SCHEMA = vol.Schema(
    {
        vol.Required("mfa_code"): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DroneMobile."""

    VERSION = 1

    def __init__(self):
        """Create a new instance of the flow handler."""
        self.username = None
        self.password = None
        self.unit = None
        self.update_interval = None
        self.override_lock_state_check = None
        self.vehicle_id = None
        self.vehicles_options = None
        self._mfa_challenge_name: str | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlow(config_entry)

    async def async_step_import(self, user_input=None):
        """Occurs when a previously setup entry fails and is re-initiated."""
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None):
        """Handle the initial step - collect credentials."""
        errors = {}
        if user_input is not None:
            try:
                # First attempt: no MFA callback. If Cognito requires a second factor,
                # MFARequiredError is raised after the initial InitiateAuth call has
                # already dispatched the SMS / TOTP prompt to the user's device.
                await validate_input(self.hass, user_input)

                # Credentials valid and no MFA required — proceed to vehicle selection.
                self.username = user_input[CONF_USERNAME]
                self.password = user_input[CONF_PASSWORD]
                self.unit = user_input[CONF_UNIT]
                self.update_interval = user_input[CONF_UPDATE_INTERVAL]
                self.override_lock_state_check = user_input[CONF_OVERRIDE_LOCK_STATE_CHECK]
                return await self.async_step_select_vehicle(user_input)

            except MFARequiredError as err:
                # Cognito returned a challenge (SMS_MFA or SOFTWARE_TOKEN_MFA).
                # Store credentials so async_step_mfa can retry with the OTP code.
                # For SMS_MFA the code has already been dispatched to the user's phone.
                # For SOFTWARE_TOKEN_MFA the user opens their authenticator app.
                self.username = user_input[CONF_USERNAME]
                self.password = user_input[CONF_PASSWORD]
                self.unit = user_input[CONF_UNIT]
                self.update_interval = user_input[CONF_UPDATE_INTERVAL]
                self.override_lock_state_check = user_input[CONF_OVERRIDE_LOCK_STATE_CHECK]
                self._mfa_challenge_name = err.challenge_name
                _LOGGER.debug(
                    "MFA challenge '%s' required for %s, redirecting to MFA step",
                    err.challenge_name,
                    user_input[CONF_USERNAME],
                )
                return await self.async_step_mfa()

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during credential validation")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_mfa(self, user_input=None):
        """Collect the one-time MFA code from the user.

        This step is reached when Cognito signals that a second factor is
        required.  We show a simple form with a single text field for the OTP.
        On submission we re-run authentication — this makes a fresh
        InitiateAuth call which causes Cognito to re-send the SMS (or the user
        reads the current TOTP from their authenticator app) — then pass the
        submitted code via mfa_callback to complete the RespondToAuthChallenge
        round-trip.
        """
        errors = {}

        if user_input is not None:
            submitted_code = user_input.get("mfa_code", "").strip()
            if not submitted_code:
                errors["mfa_code"] = "mfa_code_required"
            else:
                try:
                    await validate_input(
                        self.hass,
                        {
                            CONF_USERNAME: self.username,
                            CONF_PASSWORD: self.password,
                        },
                        mfa_callback=lambda _challenge: submitted_code,
                    )
                    # MFA passed — proceed to vehicle selection.
                    return await self.async_step_select_vehicle({})

                except MFARequiredError:
                    # Shouldn't happen since we supplied a callback, but guard anyway.
                    errors["base"] = "mfa_failed"
                except InvalidAuth:
                    # Cognito returned CodeMismatchException or similar.
                    errors["mfa_code"] = "invalid_mfa_code"
                except CannotConnect:
                    errors["base"] = "cannot_connect"
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("Unexpected exception during MFA validation")
                    errors["base"] = "unknown"

        # Build a human-readable description that tells the user where to find
        # their code, since the challenge name alone is not user-friendly.
        if self._mfa_challenge_name == "SMS_MFA":
            challenge_description = "SMS text message"
        elif self._mfa_challenge_name == "SOFTWARE_TOKEN_MFA":
            challenge_description = "authenticator app (TOTP)"
        else:
            challenge_description = "authentication device"

        return self.async_show_form(
            step_id="mfa",
            data_schema=MFA_SCHEMA,
            description_placeholders={"challenge_description": challenge_description},
            errors=errors,
        )

    async def async_step_select_vehicle(self, user_input=None):
        """Ask user to select the vehicle to setup."""
        errors = {}
        if user_input is None or CONF_VEHICLE_ID not in user_input:
            # Get available vehicles
            existing_vehicles = [
                entry.data[CONF_VEHICLE_ID] for entry in self._async_current_entries()
            ]
            vehicles = await get_vehicles(self.hass, self.username, self.password)

            # Build vehicle options dict
            vehicles_options = {}
            for vehicle in vehicles:
                if vehicle.vehicle_id not in existing_vehicles:
                    raw = vehicle.info.raw_data

                    _LOGGER.debug(
                        "Vehicle %s - raw name: %s, raw make: %s, raw model: %s, raw year: %s",
                        vehicle.vehicle_id,
                        raw.get("vehicle_name"),
                        raw.get("vehicle_make"),
                        raw.get("vehicle_model"),
                        raw.get("vehicle_year"),
                    )

                    parts = []
                    if raw.get("vehicle_year"):
                        parts.append(str(raw["vehicle_year"]))
                    if raw.get("vehicle_make"):
                        parts.append(raw["vehicle_make"])
                    if raw.get("vehicle_model"):
                        parts.append(raw["vehicle_model"])

                    if parts:
                        display_name = " ".join(parts)
                    elif raw.get("vehicle_name"):
                        display_name = raw["vehicle_name"]
                    else:
                        display_name = f"Vehicle {vehicle.vehicle_id}"

                    vehicles_options[vehicle.vehicle_id] = display_name

            if not vehicles_options:
                return self.async_abort(reason="no_available_vehicles")

            self.vehicles_options = vehicles_options

            return self.async_show_form(
                step_id="select_vehicle",
                data_schema=vol.Schema(
                    {vol.Required(CONF_VEHICLE_ID): vol.In(vehicles_options)}
                ),
                errors=errors,
            )

        self.vehicle_id = user_input[CONF_VEHICLE_ID]
        return await self.async_step_install()

    async def async_step_install(self, data=None):
        """Create a config entry at completion of the flow."""
        data = {
            CONF_USERNAME: self.username,
            CONF_PASSWORD: self.password,
            CONF_VEHICLE_ID: self.vehicle_id,
        }
        options = {
            CONF_UNIT: self.unit,
            CONF_UPDATE_INTERVAL: self.update_interval,
            CONF_OVERRIDE_LOCK_STATE_CHECK: self.override_lock_state_check,
        }

        await self.async_set_unique_id("drone_mobile_vehicle_" + str(self.vehicle_id))
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=self.vehicles_options[self.vehicle_id], data=data, options=options
        )


class OptionsFlow(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
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
                    CONF_OVERRIDE_LOCK_STATE_CHECK, DEFAULT_OVERRIDE_LOCK_STATE_CHECK
                ),
            ): bool,
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def validate_input(
    hass: core.HomeAssistant,
    data: dict,
    mfa_callback=None,
) -> bool:
    """Validate the user input allows us to connect.

    Args:
        hass: Home Assistant instance
        data: dict with CONF_USERNAME and CONF_PASSWORD
        mfa_callback: Optional callable ``(challenge_name: str) -> str`` for MFA.
            When None, MFARequiredError is propagated to the caller so the config
            flow can redirect to async_step_mfa.

    Raises:
        CannotConnect: If the API is unreachable or returns no vehicles.
        InvalidAuth: If credentials are rejected or MFA code is wrong.
        MFARequiredError: If MFA is required and no mfa_callback was provided.
    """
    client = DroneMobileClient(
        data[CONF_USERNAME],
        data[CONF_PASSWORD],
        token_dir=token_storage_dir(hass),
        mfa_callback=mfa_callback,
    )

    try:
        vehicles = await hass.async_add_executor_job(client.get_vehicles)
        if not vehicles:
            raise CannotConnect
    except MFARequiredError:
        # Re-raise as-is so the config flow can handle it with a dedicated step.
        raise
    except AuthenticationError as ex:
        _LOGGER.error("Authentication failed: %s", ex)
        raise InvalidAuth from ex
    except DroneMobileException as ex:
        _LOGGER.error("Connection failed: %s", ex)
        raise CannotConnect from ex
    finally:
        await hass.async_add_executor_job(client.close)

    return True


async def get_vehicles(hass: core.HomeAssistant, username: str, password: str):
    """Get list of vehicles from DroneMobile.

    Token is already valid at this point (validate_input succeeded), so no
    MFA callback is needed here.
    """
    client = DroneMobileClient(username, password, token_dir=token_storage_dir(hass))
    try:
        vehicles = await hass.async_add_executor_job(client.get_vehicles)
        if not vehicles:
            _LOGGER.error("No vehicles found in DroneMobile account")
            raise CannotConnect
        return vehicles
    except MFARequiredError:
        # A valid token is cached from the earlier validate_input call, so this
        # path should not be reached.  If it somehow is, treat it as auth failure.
        raise InvalidAuth
    except AuthenticationError as ex:
        _LOGGER.error("Authentication failed: %s", ex)
        raise InvalidAuth from ex
    except DroneMobileException as ex:
        _LOGGER.error("Failed to get vehicles: %s", ex)
        raise CannotConnect from ex
    finally:
        await hass.async_add_executor_job(client.close)