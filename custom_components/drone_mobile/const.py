"""Constants for the DroneMobile integration."""
from typing import Final

DOMAIN: Final = "drone_mobile"
MANUFACTURER: Final = "DroneMobile"

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
SWITCH_AUX1: Final = "aux1"
SWITCH_AUX2: Final = "aux2"