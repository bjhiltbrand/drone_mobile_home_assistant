# DroneMobile Home Assistant Integration

## Install
Place the "drone_mobile" folder in the "custom_components" folder of your Home Assistant instance. Once the integration is installed go to your integrations and follow the configuration options to specify the below:
- Username (DroneMobile - This should be an email address)
- Password (DroneMobile)
- Units (Imperial or Metric. The default is Imperial [MPH, miles, farenheit])
- Update Interval (In Minutes)

## Usage
Your car must have a DroneMobile Remote Start system installed (from Firstech, Compustar, etc.) and you must be subscribed to a DroneMobile Plan.

### Car Refresh
I have added a service to poll the car for updates, due to the battery drain I have left this up to you to set the interval. The service to be called is "refresh_status" and can be accessed in home assistant using "drone_mobile.refresh_status" with no parameters.

**This will take up to 5 mins to update from the car once the service has been run**

###
Click on options and choose imperial or metric to display in km/miles. Takes effect on next restart of home assistant. Default is Imperial

### Clear Tokens
If you are experiencing any sign in issues, please trying clearing your tokens using the "clear_tokens" service call.


## Currently Working

Status Sensors:
- Odometer
- Last known GPS Coordinates/Map
- Temperature Status
- Battery Status
- Ignition Status
- Alarm Status
- Door Status
- Last Car Refresh status
- Car Tracker

Triggers:
- Remote Start
- Lock/Unlock (This also counts as arming the alarm)


## Coming Soon

- Trunk Trigger
- Panic Trigger
- Aux1 Trigger
- Aux2 Trigger