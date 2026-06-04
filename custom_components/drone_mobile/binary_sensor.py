"""Binary sensor platform for DroneMobile integration.

These are the automation-friendly, device-class counterparts to the existing
string status sensors (Doors, Hood, Trunk, Ignition, Engine, Lock), plus a
derived Low Battery sensor. They read only fields already present in the
coordinator's status object and the raw controller payload, so no change to the
``drone_mobile`` package is required.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DroneMobileEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# A 12V vehicle battery at or below this resting voltage is considered low.
# Used only as a fallback when the API does not report a low_battery flag.
LOW_BATTERY_VOLTAGE = 11.8


def _raw(status: Any) -> dict:
    """Return the raw status payload dict, or {}."""
    return getattr(status, "raw_data", None) or {}


def _controller(status: Any) -> dict:
    """Return the controller block from the raw status payload, or {}."""
    last_known = _raw(status).get("last_known_state") or {}
    return last_known.get("controller") or {}


def _low_battery(status: Any) -> bool | None:
    """Prefer the API low_battery flag; fall back to a voltage threshold."""
    flag = _raw(status).get("low_battery")
    if flag is not None:
        return bool(flag)
    voltage = getattr(status, "battery_voltage", None)
    if voltage is None:
        return None
    return voltage <= LOW_BATTERY_VOLTAGE


@dataclass(frozen=True, kw_only=True)
class DroneMobileBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a DroneMobile binary sensor."""

    # Maps the coordinator's status object to True / False / None.
    value_fn: Callable[[Any], bool | None]


BINARY_SENSORS: tuple[DroneMobileBinarySensorDescription, ...] = (
    DroneMobileBinarySensorDescription(
        key="doors",
        name="Doors",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:car-door",
        value_fn=lambda s: _controller(s).get("door_open"),
    ),
    DroneMobileBinarySensorDescription(
        key="hood",
        name="Hood",
        device_class=BinarySensorDeviceClass.OPENING,
        icon="mdi:car-info",
        value_fn=lambda s: _controller(s).get("hood_open"),
    ),
    DroneMobileBinarySensorDescription(
        key="trunk",
        name="Trunk",
        device_class=BinarySensorDeviceClass.OPENING,
        icon="mdi:car-back",
        value_fn=lambda s: _controller(s).get("trunk_open"),
    ),
    DroneMobileBinarySensorDescription(
        key="ignition",
        name="Ignition",
        device_class=BinarySensorDeviceClass.POWER,
        icon="mdi:key-variant",
        value_fn=lambda s: _controller(s).get("ignition_on"),
    ),
    DroneMobileBinarySensorDescription(
        key="engine_running",
        name="Engine",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:engine",
        value_fn=lambda s: getattr(s, "is_running", None),
    ),
    DroneMobileBinarySensorDescription(
        key="lock",
        name="Lock",
        # device_class LOCK: on = unlocked / disarmed, off = locked / armed.
        device_class=BinarySensorDeviceClass.LOCK,
        icon="mdi:lock",
        value_fn=lambda s: (
            None
            if getattr(s, "is_locked", None) is None
            else not s.is_locked
        ),
    ),
    DroneMobileBinarySensorDescription(
        key="low_battery",
        name="Low Battery",
        device_class=BinarySensorDeviceClass.BATTERY,
        icon="mdi:car-battery",
        value_fn=_low_battery,
    ),
    DroneMobileBinarySensorDescription(
        key="panic",
        name="Panic",
        device_class=BinarySensorDeviceClass.SAFETY,
        icon="mdi:alarm-light",
        value_fn=lambda s: _raw(s).get("panic_status"),
    ),
    DroneMobileBinarySensorDescription(
        key="towing",
        name="Towing",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:tow-truck",
        value_fn=lambda s: _raw(s).get("towing_detected"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DroneMobile binary sensor entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        DroneMobileBinarySensor(coordinator, description)
        for description in BINARY_SENSORS
    )


class DroneMobileBinarySensor(DroneMobileEntity, BinarySensorEntity):
    """A DroneMobile binary sensor backed by an entity description."""

    entity_description: DroneMobileBinarySensorDescription

    def __init__(
        self,
        coordinator,
        description: DroneMobileBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(
            coordinator=coordinator,
            device_id=description.key,
            name=f"{coordinator.vehicle.name} {description.name}",
        )
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return True/False, or None when the value is unavailable."""
        status = self.coordinator.data["status"]
        value = self.entity_description.value_fn(status)
        if value is None:
            return None
        return bool(value)
