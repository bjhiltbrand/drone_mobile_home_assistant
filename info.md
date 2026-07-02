# DroneMobile Home Assistant Integration

[![hacs_badge][hacsbadge]][hacs]
[![hainstall][hainstallbadge]][hainstall]
[![PayPal][paypalbadge]][paypal]
[![github][ghsbadge]][ghs]
[![Version](https://img.shields.io/badge/version-2026.7.2-blue.svg?style=for-the-badge&logo=homeassistantcommunitystore&logoColor=ccc)](https://github.com/bjhiltbrand/drone_mobile_home_assistant)

[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-default-blue.svg?style=for-the-badge&logo=homeassistantcommunitystore&logoColor=ccc

[hainstall]: https://my.home-assistant.io/redirect/config_flow_start/?domain=drone_mobile
[hainstallbadge]: https://img.shields.io/badge/dynamic/json?style=for-the-badge&logo=home-assistant&logoColor=ccc&label=usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.drone_mobile.total

[ghs]: https://github.com/sponsors/bjhiltbrand
[ghsbadge]: https://img.shields.io/github/sponsors/bjhiltbrand?style=for-the-badge&logo=github&logoColor=ccc&link=https%3A%2F%2Fgithub.com%2Fsponsors%2Fbjhiltbrand&label=Sponsors

[paypal]: https://paypal.me/bjhiltbrand
[paypalbadge]: https://img.shields.io/badge/paypal-me-blue.svg?style=for-the-badge&logo=paypal&logoColor=ccc

Home Assistant integration for DroneMobile connected vehicles (Firstech/Compustar remote start systems).

## ⚠️ Disclaimer

This integration uses an **unofficial API** from [DroneMobile](https://www.dronemobile.com/) that is subject to change without notice. The authors claim no responsibility for any damages to your vehicle resulting from the use of this integration.

## Features

### Sensors
- 🛣️ **Odometer** - Current mileage
- 🔋 **Battery** - Voltage and percentage
- 🌡️ **Temperature** - Interior and exterior temperatures
- 📍 **GPS** - Current location coordinates
- 📶 **Cellular Signal** - Device signal strength (diagnostic)
- 🔋 **Backup Battery** - Backup battery voltage (diagnostic)
- 📡 **Carrier** - Cellular carrier name (diagnostic)
- 🔧 **Firmware Version** - Device firmware version (diagnostic)
- 🖥️ **Controller Model** - Vehicle controller model (diagnostic)
- 🕐 **Last Refresh** - Timestamp of last update

### Binary Sensors
- 🚗 **Engine** - Running/Off
- 🔑 **Ignition** - On/Off
- 🔒 **Lock** - Locked/Unlocked
- 🚪 **Doors** - Open/Closed
- 🎒 **Trunk** - Open/Closed
- 🚗 **Hood** - Open/Closed
- 🔋 **Low Battery** - Low battery alert (uses API flag or ≤ 11.8 V threshold)
- 🚨 **Panic** - Panic alarm active/inactive
- 🚛 **Towing** - Towing detected
- Diagnostic read-only flags: Valet Mode, Turbo Timer, Drive Lock, Passive Arming, Auto Lock/Arm

### Controls
- 🔒 **Door Lock** - Lock/Unlock doors
- 🎒 **Trunk** - Open trunk
- 🏁 **Remote Start** - Start/Stop engine
- 🚨 **Panic Alarm** - Activate/Deactivate panic
- 🔧 **Auxiliary 1 & 2** - Trigger auxiliary functions
- 📍 **Locate** - Request a fresh GPS fix from the vehicle
- 🔊 **Siren** - Enable/Disable siren
- ⚡ **Shock Sensor** - Enable/Disable shock sensor

### Device Tracker
- 📍 **GPS Tracker** - Real-time location tracking

## Requirements

- Home Assistant 2023.1 or newer
- DroneMobile subscription and compatible vehicle system
- Account credentials for DroneMobile

## Installation

### HACS (Recommended)

DroneMobile is now part of the **HACS default integrations list**, so there's no need to add a custom repository anymore.

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click **"Explore & Download Repositories"** (top right)
4. Search for **"DroneMobile"**
5. Click **"Download"**
6. Restart Home Assistant

> **Already had this added as a custom repository?** You can safely remove the old custom repository entry (HACS → Integrations → DroneMobile → three-dot menu → **Remove**), then re-download it — HACS will now serve it from the default list automatically. Your existing configuration and entities are unaffected either way.

### Manual Installation

1. Download the latest release from GitHub
2. Copy the `custom_components/drone_mobile` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

### Setup via UI

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **DroneMobile**
4. Enter your credentials:
   - **Username** - Your DroneMobile email address
   - **Password** - Your DroneMobile password
   - **Units** - Imperial (miles/°F) or Metric (km/°C)
   - **Update Interval** - How often to poll for updates (2-60 minutes)
   - **Override Lock State Check** - Send lock commands regardless of current state
5. If your DroneMobile account has **two-factor authentication (MFA)** enabled, you will be prompted to enter a one-time verification code. Depending on your account settings, this will be delivered via SMS or your authenticator app (TOTP).
6. Select your vehicle from the list
7. Click **Submit**

### Multiple Vehicles

To add multiple vehicles:
1. Complete the setup process for your first vehicle
2. Repeat the setup process
3. Select a different vehicle from the list

Each vehicle will be added as a separate integration instance with its own entities.

## Usage

### Entity Naming

All entities follow the pattern: `{domain}.{vehicle_name}_{entity_name}`

Example for a vehicle named "My Car":
- `sensor.my_car_odometer`
- `lock.my_car_door_lock`
- `switch.my_car_remote_start`
- `binary_sensor.my_car_engine`
- `device_tracker.my_car_location`

### Services

#### Refresh Device Status

Manually poll the vehicle for the latest status. Use sparingly as it consumes cellular data and vehicle battery.

```yaml
service: drone_mobile.refresh_device_status_{vehicle_name}
```

Replace `{vehicle_name}` with your vehicle name (spaces replaced with underscores, lowercase).

Example:
```yaml
service: drone_mobile.refresh_device_status_my_car
```

### Example Automations

#### Auto-Start When Cold

```yaml
automation:
  - alias: "Start car when cold in the morning"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: numeric_state
        entity_id: sensor.my_car_temperature
        below: 40
      - condition: state
        entity_id: switch.my_car_remote_start
        state: 'off'
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.my_car_remote_start
      - service: notify.mobile_app
        data:
          message: "Car started automatically - it's {{ states('sensor.my_car_temperature') }}°F outside"
```

#### Lock Reminder

```yaml
automation:
  - alias: "Notify if car left unlocked at night"
    trigger:
      - platform: time
        at: "22:00:00"
    condition:
      - condition: state
        entity_id: binary_sensor.my_car_lock
        state: 'on'
    action:
      - service: notify.mobile_app
        data:
          message: "⚠️ Your car is unlocked!"
          data:
            actions:
              - action: "LOCK_CAR"
                title: "Lock Now"
      - wait_for_trigger:
          - platform: event
            event_type: mobile_app_notification_action
            event_data:
              action: "LOCK_CAR"
        timeout: "00:05:00"
      - service: lock.lock
        target:
          entity_id: lock.my_car_door_lock
```

#### Low Battery Alert

```yaml
automation:
  - alias: "Alert on low car battery"
    trigger:
      - platform: state
        entity_id: binary_sensor.my_car_low_battery
        to: 'on'
    action:
      - service: notify.mobile_app
        data:
          message: "⚠️ Car battery is low: {{ states('sensor.my_car_battery') }}V"
```

#### Location-Based Actions

```yaml
automation:
  - alias: "Start car when arriving at work"
    trigger:
      - platform: zone
        entity_id: device_tracker.my_phone
        zone: zone.work
        event: enter
    condition:
      - condition: numeric_state
        entity_id: sensor.my_car_temperature
        below: 50
      - condition: state
        entity_id: binary_sensor.my_car_engine
        state: 'off'
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.my_car_remote_start
```

### Lovelace Cards

#### Simple Vehicle Status Card

```yaml
type: entities
title: My Car
entities:
  - entity: binary_sensor.my_car_engine
    name: Engine
  - entity: binary_sensor.my_car_ignition
    name: Ignition
  - entity: lock.my_car_door_lock
    name: Doors
  - entity: sensor.my_car_battery
    name: Battery
  - entity: sensor.my_car_temperature
    name: Temperature
  - entity: sensor.my_car_odometer
    name: Odometer
```

#### Control Card

```yaml
type: glance
title: Car Controls
entities:
  - entity: switch.my_car_remote_start
    name: Start/Stop
  - entity: lock.my_car_door_lock
    name: Lock/Unlock
  - entity: lock.my_car_trunk
    name: Trunk
  - entity: switch.my_car_panic
    name: Panic
  - entity: button.my_car_locate
    name: Locate
```

#### Map Card

```yaml
type: map
entities:
  - device_tracker.my_car_location
default_zoom: 15
```

## Configuration Options

### Units
- **Imperial** - Miles, MPH, °F (default)
- **Metric** - Kilometers, KPH, °C

### Update Interval
- Range: 2-60 minutes
- Default: 5 minutes
- Note: More frequent updates consume more cellular data and vehicle battery

### Override Lock State Check
- **Disabled** (default) - Only send lock/unlock commands if state differs
- **Enabled** - Always send commands regardless of current state

## Troubleshooting

### Enable Debug Logging

Add to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.drone_mobile: debug
    drone_mobile: debug
```

### Common Issues

#### "Unable to connect"
- Verify your DroneMobile credentials
- Check that your DroneMobile subscription is active
- Ensure you can log in to the DroneMobile app

#### MFA code not accepted
- Codes are time-sensitive; make sure your device clock is accurate
- Re-enter your credentials to trigger a fresh code to be sent
- Ensure you are reading from the correct SMS thread or authenticator app entry

#### Entities show "Unavailable"
- Check Home Assistant logs for errors
- Try removing and re-adding the integration
- Verify your internet connection

#### GPS not showing
- Ensure your vehicle hardware supports GPS
- GPS entities only appear if your system reports location data

#### Commands not working
- Some commands may not be supported by your vehicle hardware
- Check that your vehicle is within cellular range
- Wait a few moments and try again

### Getting Help

1. Check the [GitHub Issues](https://github.com/bjhiltbrand/drone_mobile_home_assistant/issues)
2. Enable debug logging (see above)
3. Review Home Assistant logs: Settings → System → Logs
4. Use **Download diagnostics** (Settings → Devices & Services → DroneMobile → three-dot menu) to capture a redacted snapshot for bug reports
5. Open a new issue with:
   - Your Home Assistant version
   - Integration version
   - Relevant log entries
   - Description of the problem

## Privacy & Security

- Your DroneMobile credentials are stored securely in Home Assistant's encrypted configuration
- Authentication tokens are cached in `/config/drone_mobile/` so they persist across Home Assistant Core updates and are included in HA backups — you will not be asked to re-authenticate after every upgrade
- No data is sent to third parties
- All communication is with DroneMobile's official API
- The **Download diagnostics** feature automatically redacts all sensitive fields (credentials, VIN, location, tokens, IMEI, etc.) before the file is saved

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Credits

- Original integration: [@bjhiltbrand](https://github.com/bjhiltbrand)
- Python package: [drone_mobile](https://github.com/bjhiltbrand/drone_mobile_python)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This integration is not affiliated with, endorsed by, or connected to DroneMobile, Firstech, or Compustar in any way. Use at your own risk.
