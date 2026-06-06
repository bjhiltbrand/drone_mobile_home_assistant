"""Constants for the DroneMobile integration."""
from pathlib import Path
from typing import Final

DOMAIN: Final = "drone_mobile"
MANUFACTURER: Final = "DroneMobile"


def token_storage_dir(hass) -> Path:
    """Persistent token and device-remembering storage under ``/config``.

    The library defaults to ``~/.config/drone_mobile`` which, on Home Assistant
    OS, lives inside the Core container and is wiped on every Core update.
    Storing under ``/config`` keeps the cached token and the remembered device
    across updates, so MFA is not re-triggered after each upgrade.
    """
    return Path(hass.config.path(DOMAIN))

# Configuration
CONF_VEHICLE_ID: Final = "vehicle_id"
CONF_UNIT: Final = "units"
CONF_UNITS: Final = ["Imperial", "Metric"]
CONF_UPDATE_INTERVAL: Final = "update_interval"
CONF_OVERRIDE_LOCK_STATE_CHECK: Final = "override_lock_state_check"

# Defaults
DEFAULT_UNIT: Final = "Imperial"
DEFAULT_UPDATE_INTERVAL: Final = 5  # minutes
DEFAULT_OVERRIDE_LOCK_STATE_CHECK: Final = False

# Sensors
SENSOR_ODOMETER: Final = "odometer"
SENSOR_BATTERY: Final = "battery"
SENSOR_TEMPERATURE: Final = "temperature"
SENSOR_GPS: Final = "gps"
SENSOR_ALARM: Final = "alarm"
SENSOR_IGNITION_STATUS: Final = "ignition_status"
SENSOR_ENGINE_STATUS: Final = "engine_status"
SENSOR_DOOR_STATUS: Final = "door_status"
SENSOR_TRUNK_STATUS: Final = "trunk_status"
SENSOR_HOOD_STATUS: Final = "hood_status"
SENSOR_LAST_REFRESH: Final = "last_refresh"

# Locks
LOCK_DOOR: Final = "door_lock"
LOCK_TRUNK: Final = "trunk"

# Switches
SWITCH_REMOTE_START: Final = "remote_start"
SWITCH_PANIC: Final = "panic"

# Buttons
BUTTON_AUX1: Final = "aux1"
BUTTON_AUX2: Final = "aux2"