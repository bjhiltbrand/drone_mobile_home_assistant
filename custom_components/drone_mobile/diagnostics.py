"""Diagnostics support for the DroneMobile integration.

Provides a downloadable snapshot (Settings -> Devices & Services -> the entry ->
the three-dot menu -> Download diagnostics) of the config entry and the latest
vehicle status, with sensitive fields redacted. Useful for bug reports.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

# Keys redacted anywhere they appear (account, identity, and location data).
TO_REDACT = {
    "username",
    "password",
    "email",
    "vin",
    "esn",
    "serial",
    "serial_number",
    "phone",
    "phone_number",
    "address",
    "latitude",
    "longitude",
    "lat",
    "lng",
    "lon",
    "accuracy",
    "imei",
    "iccid",
    "device_key",
    "access_token",
    "refresh_token",
    "id_token",
    "token",
    "vehicle_id",
    "device_id",
    "subscriber_id",
    "ble_mac_address",
    # The vehicle/plan image fields are AWS presigned URLs that embed a
    # temporary X-Amz-Security-Token, so redact the whole value.
    "image",
}


def _vehicle_info(info: Any) -> dict[str, Any]:
    """Pull the basic vehicle info fields defensively."""
    if info is None:
        return {}
    return {
        "name": getattr(info, "name", None),
        "year": getattr(info, "year", None),
        "make": getattr(info, "make", None),
        "model": getattr(info, "model", None),
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}
    status = data.get("status")
    raw = getattr(status, "raw_data", None)

    return {
        "entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
        },
        "vehicle_info": async_redact_data(_vehicle_info(data.get("info")), TO_REDACT),
        "status_raw": (
            async_redact_data(raw, TO_REDACT) if isinstance(raw, dict) else None
        ),
    }
