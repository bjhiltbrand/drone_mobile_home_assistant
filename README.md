# DroneMobile Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/bjhiltbrand/drone_mobile_home_assistant.svg)](https://github.com/bjhiltbrand/drone_mobile_home_assistant/releases)
[![License](https://img.shields.io/github/license/bjhiltbrand/drone_mobile_home_assistant.svg)](LICENSE)

Control your vehicle's remote start system through Home Assistant using the DroneMobile API.

<img src="https://brands.home-assistant.io/_/drone_mobile/logo.png" alt="DroneMobile" width="200"/>

## 🚗 Overview

This integration allows you to control your Firstech/Compustar remote start system through Home Assistant. Monitor your vehicle's status, remotely start/stop the engine, lock/unlock doors, and track your vehicle's location—all from your Home Assistant dashboard.

## ⚠️ Disclaimer

This integration uses an **unofficial API** from [DroneMobile](https://www.dronemobile.com/) and is **not affiliated with or endorsed by** DroneMobile, Firstech, or Compustar. The API is subject to change without notice. 

**The authors assume no responsibility for any damages to your vehicle or account resulting from the use of this integration.**

## ✨ Features

### Status Monitoring
- 📍 **GPS Location Tracking** - Real-time vehicle location on the map
- 🔋 **Battery Level** - Monitor your vehicle's battery voltage and percentage
- 🌡️ **Temperature Sensors** - Interior and exterior temperature (if supported)
- ⛽ **Fuel Level** - Current fuel level percentage (if supported)
- 📏 **Odometer** - Track mileage in miles or kilometers
- 🔔 **Alarm Status** - Armed/disarmed state
- 🚪 **Door/Trunk/Hood Status** - Open/closed states
- ⚙️ **Engine & Ignition Status** - Running/stopped and on/off states
- 🕐 **Last Update Timestamp** - When data was last refreshed

### Vehicle Control
- 🔑 **Remote Start/Stop** - Start and stop your engine remotely
- 🔒 **Lock/Unlock Doors** - Control door locks (arms/disarms alarm)
- 🚪 **Trunk Release** - Open the trunk remotely
- 🚨 **Panic Alarm** - Activate/deactivate panic mode
- 🔘 **Auxiliary Controls** - Trigger AUX1 and AUX2 functions (if configured)

### Services
- 🔄 **Manual Status Refresh** - Force poll vehicle for latest data
- 💾 **Data Export** - Dump all vehicle data to JSON file for debugging

## 📋 Requirements

- **Home Assistant** 2023.1 or newer
- **DroneMobile Account** with active subscription
- **Compatible Vehicle** with DroneMobile-enabled remote start system (Firstech/Compustar)
- **drone_mobile Python Package** 0.3.0 or newer (installed automatically)

## 📦 Installation

### HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed
2. Add this repository as a custom repository:
   - HACS → Integrations → ⋮ (top right) → Custom repositories
   - Repository: `https://github.com/bjhiltbrand/drone_mobile_home_assistant`
   - Category: Integration
3. Click **Install**
4. Restart Home Assistant
5. Continue to [Configuration](#-configuration)

### Manual Installation

1. Download the latest release from [GitHub](https://github.com/bjhiltbrand/drone_mobile_home_assistant/releases)
2. Extract the `drone_mobile` folder from the archive
3. Copy to your Home Assistant `custom_components` directory:
   ```
   config/
   └── custom_components/
       └── drone_mobile/
           ├── __init__.py
           ├── config_flow.py
           ├── const.py
           ├── device_tracker.py
           ├── lock.py
           ├── manifest.json
           ├── sensor.py
           ├── services.yaml
           ├── strings.json
           ├── switch.py
           └── translations/
   ```
4. Restart Home Assistant
5. Continue to [Configuration](#-configuration)

## ⚙️ Configuration

### Initial Setup

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **DroneMobile**
4. Enter your credentials:
   - **Email Address** - Your DroneMobile account email
   - **Password** - Your DroneMobile account password
   - **Units** - Choose Imperial (miles, °F) or Metric (km, °C)
   - **Update Interval** - How often to fetch data (2-60 minutes, default: 5)
   - **Override Lock State Check** - Send lock/unlock commands even if already in that state
5. Click **Submit** and wait for authentication (may take 30 seconds)
6. **Select your vehicle** from the list
7. Click **Submit** to complete setup

### Options

To modify settings after initial setup:

1. Go to **Settings** → **Devices & Services**
2. Find **DroneMobile** integration
3. Click **Configure**
4. Adjust settings:
   - Change units (Imperial ↔ Metric)
   - Modify update interval
   - Toggle override lock state check

Changes take effect immediately (no restart required).

### Multiple Vehicles

To add multiple vehicles:

1. Repeat the configuration process
2. Select a different vehicle each time
3. Each vehicle appears as a separate integration instance

## 📱 Usage

### Entities Created

For each vehicle, the following entities are created:

#### Sensors
- `sensor.{vehicle}_odometer` - Mileage reading
- `sensor.{vehicle}_battery_voltage` - Battery voltage (V)
- `sensor.{vehicle}_battery_level` - Battery percentage (%)
- `sensor.{vehicle}_interior_temperature` - Interior temp (°F or °C)
- `sensor.{vehicle}_fuel_level` - Fuel level (%)
- `sensor.{vehicle}_alarm_status` - Armed/Disarmed
- `sensor.{vehicle}_last_update` - Last data refresh timestamp

#### Locks
- `lock.{vehicle}_door_lock` - Lock/unlock doors (arms/disarms alarm)
- `lock.{vehicle}_trunk` - Open trunk (unlock only)

#### Switches
- `switch.{vehicle}_remote_start` - Start/stop engine
- `switch.{vehicle}_panic_alarm` - Activate/deactivate panic
- `switch.{vehicle}_auxiliary_1` - Trigger AUX1 (momentary)
- `switch.{vehicle}_auxiliary_2` - Trigger AUX2 (momentary)

#### Device Tracker
- `device_tracker.{vehicle}_location` - GPS location tracker

> **Note**: Some entities may not appear if your vehicle doesn't support the feature (e.g., GPS, fuel level, temperature).

### Automation Examples

#### Start car on cold mornings
```yaml
automation:
  - alias: "Warm up car on cold days"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: numeric_state
        entity_id: sensor.my_car_interior_temperature
        below: 40
      - condition: state
        entity_id: binary_sensor.workday_sensor
        state: "on"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.my_car_remote_start
      - service: notify.mobile_app
        data:
          message: "Your car is warming up!"
```

#### Lock car when leaving home
```yaml
automation:
  - alias: "Lock car when leaving"
    trigger:
      - platform: zone
        entity_id: person.me
        zone: zone.home
        event: leave
    action:
      - service: lock.lock
        target:
          entity_id: lock.my_car_door_lock
```

#### Alert on low battery
```yaml
automation:
  - alias: "Car battery low alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.my_car_battery_level
        below: 20
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ Car Battery Low"
          message: "Your car battery is at {{ states('sensor.my_car_battery_level') }}%"
```

### Dashboard Card Example

```yaml
type: entities
title: My Car
entities:
  - entity: sensor.my_car_odometer
  - entity: sensor.my_car_battery_level
  - entity: sensor.my_car_interior_temperature
  - entity: sensor.my_car_fuel_level
  - entity: lock.my_car_door_lock
  - entity: switch.my_car_remote_start
  - type: divider
  - entity: sensor.my_car_alarm_status
  - entity: sensor.my_car_last_update
```

### Services

#### Refresh Device Status
Manually poll the vehicle for the latest status. **Use sparingly** as it consumes cellular data and drains the vehicle battery.

```yaml
service: drone_mobile.refresh_device_status_{vehicle_name}
```

Example:
```yaml
service: drone_mobile.refresh_device_status_my_car
```

#### Dump Device Data
Export all cached vehicle data to a JSON file in your Home Assistant config directory. Useful for debugging or sharing with support.

```yaml
service: drone_mobile.dump_device_data_{vehicle_name}
```

Example:
```yaml
service: drone_mobile.dump_device_data_my_car
```

Output: `config/drone_mobile_data_my_car.json`

## 🔧 Advanced Configuration

### Update Interval Recommendations

- **5 minutes** (default) - Good balance for most users
- **10-15 minutes** - Better for battery conservation
- **2-3 minutes** - For active monitoring (higher battery drain)

> **Important**: Frequent polling drains your vehicle's battery and uses cellular data from your DroneMobile subscription. The DroneMobile device has usage limits.

### Override Lock State Check

When **enabled**, lock/unlock commands are sent regardless of the current state. Useful for:
- Ensuring commands execute even if state is out of sync
- Automations that need guaranteed execution

When **disabled** (default), commands are skipped if already in the desired state.

## 🐛 Troubleshooting

### Authentication Issues

**Problem**: "Invalid email or password" error

**Solutions**:
1. Verify credentials in the DroneMobile mobile app
2. Check for special characters in password
3. Remove and re-add the integration
4. Check logs: Settings → System → Logs

### Entities Not Updating

**Problem**: Sensor values are stale or not changing

**Solutions**:
1. Check update interval (may be too long)
2. Use the refresh service manually:
   ```yaml
   service: drone_mobile.refresh_device_status_my_car
   ```
3. Check vehicle has cellular connectivity
4. Verify DroneMobile subscription is active
5. Check logs for API errors

### Missing Entities

**Problem**: Some sensors or controls don't appear

**Explanation**: Not all vehicles support all features. GPS tracking, temperature sensors, and fuel level require specific hardware support.

**To verify**: Check the DroneMobile mobile app to see which features are available for your vehicle.

### Commands Not Working

**Problem**: Remote start, lock, or other commands fail

**Solutions**:
1. Ensure vehicle is within cellular range
2. Check DroneMobile subscription is active
3. Verify commands work in mobile app
4. Check logs for specific error messages:
   - `CommandFailedError` - Vehicle didn't respond
   - `AuthenticationError` - Re-authentication needed
5. Try reloading the integration

### Integration Won't Load

**Problem**: Integration fails to set up

**Solutions**:
1. Check Home Assistant version (requires 2023.1+)
2. Verify `drone_mobile` Python package is installed:
   ```bash
   pip list | grep drone_mobile
   ```
   Should show version 0.3.0 or higher
3. Check logs for Python errors
4. Try reinstalling the integration

## 📊 Data Usage & Battery Impact

### Cellular Data
- Each status update: ~1-2 KB
- Each command: ~1-2 KB
- Daily usage (5-min interval): ~300-600 KB

### Vehicle Battery
- Status updates drain battery minimally
- Frequent polling (every 2-3 minutes) can impact battery over weeks
- Commands (start, lock) use negligible power

**Recommendation**: Use 5-10 minute intervals and avoid constant polling.

## 🔐 Privacy & Security

- **Credentials**: Stored encrypted in Home Assistant's configuration
- **Tokens**: Cached securely in `~/.config/drone_mobile/`
- **Data**: All communication uses HTTPS
- **Local only**: No data sent to third parties beyond DroneMobile API

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone repository
git clone https://github.com/bjhiltbrand/drone_mobile_home_assistant.git
cd drone_mobile_home_assistant

# Link to Home Assistant for testing
ln -s $(pwd)/custom_components/drone_mobile \
      ~/.homeassistant/custom_components/

# Restart Home Assistant
# Test your changes
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and migration guides.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Original API reverse engineering by the community
- Built on the [drone_mobile Python package](https://github.com/bjhiltbrand/drone_mobile_python)
- Thanks to all contributors and users

## 🆘 Support

- 🐛 [Report bugs](https://github.com/bjhiltbrand/drone_mobile_home_assistant/issues)
- 💡 [Request features](https://github.com/bjhiltbrand/drone_mobile_home_assistant/issues)
- 💬 [Community forum](https://community.home-assistant.io/) (tag: `drone_mobile`)
- 📖 [Home Assistant Docs](https://www.home-assistant.io/integrations/)

## ⚖️ Legal Disclaimer

This is an **unofficial integration** and is **not affiliated with, endorsed by, or connected to** DroneMobile, Firstech, or Compustar in any way. All product names, logos, and brands are property of their respective owners.

Use at your own risk. The authors are not responsible for:
- Damage to your vehicle
- Battery drain issues
- Account suspension
- Data usage charges
- Loss of DroneMobile service
- Any other issues arising from use of this integration

Always ensure commands are safe before executing. Do not rely solely on this integration for vehicle security.

---

**Made with ❤️ for the Home Assistant community**

If this integration is helpful, consider:
- ⭐ Starring the repository
- 🐛 Reporting issues you find
- 💡 Suggesting improvements
- 📖 Improving documentation
- 🤝 Contributing code