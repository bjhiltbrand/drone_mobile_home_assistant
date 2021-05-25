"""Constants for the DroneMobile integration."""

DOMAIN = "drone_mobile"
VEHICLE = "DroneMobile Vehicle"
MANUFACTURER = "DroneMobile"

CONF_VEHICLE_ID = "vehicle_id"
CONF_UNIT = "units"
CONF_UNITS = ["imperial", "metric"]
CONF_UPDATE_INTERVAL = "update_interval"

DEFAULT_UNIT = "imperial"
DEFAULT_UPDATE_INTERVAL = 5

AWSCLIENTID = "3l3gtebtua7qft45b4splbeuiu"

URLS = {
    "auth": "https://cognito-idp.us-east-1.amazonaws.com/",
    "user_info": "https://api.dronemobile.com/api/v1/user",
    "vehicle_info": "https://api.dronemobile.com/api/v1/vehicle?limit=",
    "command": "https://accounts.dronemobile.com/api/iot/send-command",
}

AVAILABLE_COMMANDS = {
    "trunk",
    "remote_start",
    "remote_stop",
    "arm",
    "disarm",
    "panic_on",
    "panic_off",
    "remote_aux1",
    "remote_aux2",
    "location",
}

COMMAND_HEADERS = {
    "x-drone-api": None,
    "Content-Type": "application/json;charset=utf-8",
}

AUTH_HEADERS = {
    "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
    "X-Amz-User-Agent": "aws-amplify/0.1.x js",
    "Content-Type": "application/x-amz-json-1.1",
}

TOKEN_FILE_LOCATION = "custom_components/drone_mobile/drone_mobile_token.txt"

SENSORS = {
    "odometer": {"icon": "mdi:counter"},
    "battery": {"icon": "mdi:car-battery"},
    "temperature": {"icon": "mdi:thermometer"},
    "gps": {"icon": "mdi:radar"},
    "alarm": {"icon": "mdi:bell"},
    "ignitionStatus": {"icon": "hass:power"},
    "doorStatus": {"icon": "mdi:car-door"},
    "lastRefresh": {"icon": "mdi:clock"},
}

LOCKS = {
    "doorLock": {"icon": "mdi:car-door-lock"},
    "trunk": {"icon": "mdi:car-wash"},
}

SWITCHES = {
    "remoteStart": {"icon": "mdi:car-key"},
    "panic": {"icon": "mdi:access-point"},
    "aux1": {"icon": "mdi:numeric-1-box-multiple"},
    "aux2": {"icon": "mdi:numeric-2-box-multiple"},
}
