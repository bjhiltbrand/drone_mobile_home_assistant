# DroneMobile Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

A Home Assistant custom integration for DroneMobile-connected vehicles (Firstech/Compustar remote start systems).

## ⚠️ Important Notice - Version 1.0.0 Update

**This version introduces breaking changes!** The integration has been completely rewritten to use the new `drone_mobile` v0.3.0 library.

### What's New
- ✨ **Modern Python Package**: Uses the official `drone_mobile` v0.3.0 from PyPI
- 🔒 **Better Security**: Improved token management and secure storage
- 🎯 **Type Safety**: Full type hints for better reliability
- 🐛 **Improved Error Handling**: Better error messages and recovery
- 🚀 **Performance**: More efficient API calls and caching
- 📝 **Better Logging**: Improved debugging capabilities

### Migration from v0.0.10
If you're upgrading from version 0.0.10 or earlier:

1. **Backup your configuration** before upgrading
2. **Remove the integration** from Home Assistant (Settings → Devices & Services)
3. **Install the new version** (see Installation below)
4. **Re-add the integration** with your credentials
5. Your vehicles will be discovered automatically

The new version will automatically migrate your authentication tokens. No manual token management is needed anymore!

## Disclaimer

The code here is based off of an unsupported API from [DroneMobile](https://www.dronemobile.com/) and is subject to change without notice. The authors claim no responsibility for damages to your vehicle by use of the code within.

## Requirements

- Home Assistant 2022.7 or newer
- DroneMobile account with active subscription
- Vehicle with installed DroneMobile system (Firstech, Compustar, etc.)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/bjhiltbrand/drone_mobile_home_assistant`
6. Select category: "Integration"
7. Click "Add"
8. Find "DroneMobile" in the integration list and click "Download"
9. Restart Home Assistant

### Manual Installation

1. Download the `custom_components/drone_mobile` folder from this repository
2. Copy it to your Home Assistant's `custom_components` directory
3. If the `custom_components` directory doesn't exist, create it in your config folder
4. Restart Home Assistant

## Configuration

### Initial Setup

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "**DroneMobile**"
4. Enter your credentials:
   - **Username**: Your DroneMobile email address
   - **Password**: Your DroneMobile password
   - **Units**: Imperial (MPH, miles, °F) or Metric (km/h, km, °C)
   - **Update Interval**: How often to poll for updates (2-60 minutes, default: 5)
   - **Override Lock State Check**: Send lock commands regardless of current state (default: off)
5. Click **Submit**
6. Select your vehicle from the list
7. Click **Submit** to complete setup

### Configuration Options

After setup, you can modify settings:

1. Go to **Settings** → **Devices & Services**
2. Find **DroneMobile** and click **Configure**
3. Adjust your preferences:
   - **Units**: Switch between Imperial and Metric
   - **Update Interval**: Change polling frequency
   - **Override Lock State Check**: Enable/disable state checking

## Features

### Status Sensors

The integration provides the following sensors:

- **Odometer** - Vehicle mileage (converts to km in Metric mode)
- **Battery** - Main battery voltage
- **Temperature** - Interior temperature (converts to °F in Imperial mode)
- **Alarm Status** - Armed or Disarmed
- **Ignition Status** - On or Off
- **Engine Status** - Running or Off
- **Door Status** - Open or Closed
- **Trunk Status** - Open or Closed
- **Hood Status** - Open or Closed
- **Last Refresh** - Timestamp of last update
- **GPS Location** - Last known coordinates (if available)

### Controls

- **Lock/Unlock** - Control door locks (also arms/disarms alarm)
- **Remote Start/Stop** - Start or stop the engine remotely
- **Trunk** - Open the trunk
- **Panic Alarm** - Activate/deactivate panic alarm
- **Auxiliary Controls** - Trigger Aux1 and Aux2 functions

### Device Tracker

If your vehicle supports GPS, a device tracker entity is automatically created showing the vehicle's location on the map.

### Services

#### Refresh Device Status
Manually poll the vehicle for the latest status. Use sparingly as it consumes vehicle battery and data.

```yaml
service: drone_mobile.refresh_device_status_YOUR_VEHICLE_NAME
```

#### Dump Device Data
Export vehicle data to a JSON file in your Home Assistant config directory for debugging.

```yaml
service: drone_mobile.dump_device_data_YOUR_VEHICLE_NAME
```

**Note**: Service names use your vehicle name with spaces replaced by underscores.

## Usage Examples

### Automation - Start car when leaving work

```yaml
automation:
  - alias: "Start car when leaving work"
    trigger:
      - platform: zone
        entity_id: person.your_name
        zone: zone.work
        event: leave
    condition:
      - condition: numeric_state
        entity_id: sensor.your_vehicle_temperature
        below: 50
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.your_vehicle_remotestart_switch
```

### Automation - Lock car at night

```yaml
automation:
  - alias: "Lock car at night"
    trigger:
      - platform: time
        at: "23:00:00"
    condition:
      - condition: state
        entity_id: lock.your_vehicle_doorlock
        state: "unlocked"
    action:
      - service: lock.lock
        target:
          entity_id: lock.your_vehicle_doorlock
```

### Script - Remote start with climate control

```yaml
script:
  warm_up_car:
    alias: "Warm up car"
    sequence:
      - service: switch.turn_on
        target:
          entity_id: switch.your_vehicle_remotestart_switch
      - delay:
          minutes: 10
      - service: switch.turn_off
        target:
          entity_id: switch.your_vehicle_remotestart_switch
```

## Troubleshooting

### Authentication Issues

If you experience authentication problems:

1. Verify your credentials are correct
2. Check that your DroneMobile subscription is active
3. Try logging into the DroneMobile app to ensure your account is working
4. Remove and re-add the integration
5. Check Home Assistant logs for specific error messages

### Entity Not Updating

If sensors aren't updating:

1. Check your update interval isn't too long
2. Verify your vehicle has cellular connectivity
3. Try manually refreshing using the service call
4. Check Home Assistant logs for API errors

### Commands Not Working

If remote commands fail:

1. Ensure your vehicle is within cellular range
2. Check that your DroneMobile subscription allows remote commands
3. Verify the command works in the DroneMobile mobile app
4. Check Home Assistant logs for error details
5. Try enabling "Override Lock State Check" in configuration

### Getting Debug Logs

To enable detailed logging:

```yaml
logger:
  default: info
  logs:
    custom_components.drone_mobile: debug
    drone_mobile: debug
```

Then check your Home Assistant logs at **Settings** → **System** → **Logs**.

## Known Limitations

1. **Polling Only**: The integration polls for updates at the configured interval. Real-time push notifications are not supported by the DroneMobile API.

2. **Rate Limiting**: Excessive API calls may result in rate limiting. Keep update intervals reasonable (5+ minutes recommended).

3. **Battery Drain**: Frequent status polls and commands can drain your vehicle's battery. Use the manual refresh service sparingly.

4. **Limited Status Data**: Some vehicle status details (door/trunk/hood) may not be available depending on your DroneMobile hardware.

5. **GPS Accuracy**: GPS location may not be available for all vehicles or hardware configurations.

## Support

- **Issues**: [GitHub Issues](https://github.com/bjhiltbrand/drone_mobile_home_assistant/issues)
- **Feature Requests**: [GitHub Issues](https://github.com/bjhiltbrand/drone_mobile_home_assistant/issues)
- **Home Assistant Community**: [Community Forum](https://community.home-assistant.io/)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Credits

- Original integration by [@bjhiltbrand](https://github.com/bjhiltbrand)
- Based on the [drone_mobile Python library](https://github.com/bjhiltbrand/drone_mobile_python)
- Thanks to all contributors and users!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Legal

This is an unofficial integration and is not affiliated with, endorsed by, or connected to DroneMobile, Firstech, or Compustar in any way.