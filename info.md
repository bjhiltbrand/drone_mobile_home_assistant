# DroneMobile Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

Control your DroneMobile connected vehicle (Firstech/Compustar remote start systems) from Home Assistant.

## Features

### 🚗 Vehicle Controls
- **Remote Start/Stop** - Start and stop your engine remotely
- **Lock/Unlock** - Control door locks
- **Trunk** - Open trunk remotely
- **Panic Alarm** - Activate/deactivate panic alarm
- **Auxiliary Functions** - Trigger Aux 1 and Aux 2

### 📊 Sensors
- **Odometer** - Current mileage
- **Battery** - Voltage and percentage
- **Temperature** - Interior temperature
- **GPS Location** - Real-time location tracking
- **Engine Status** - Running or off
- **Lock Status** - Locked or unlocked
- **Door/Trunk/Hood Status** - Open or closed
- And more!

## Installation

### HACS (Recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed
2. In HACS, go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/bjhiltbrand/drone_mobile_home_assistant`
6. Select category: "Integration"
7. Click "Install"
8. Restart Home Assistant

### Manual Installation

1. Download the latest release
2. Copy `custom_components/drone_mobile` to your `custom_components` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **DroneMobile**
4. Enter your credentials:
   - **Username** - Your DroneMobile email
   - **Password** - Your DroneMobile password
   - **Units** - Imperial or Metric
   - **Update Interval** - 2-60 minutes
5. Select your vehicle
6. Done!

## Requirements

- Active DroneMobile subscription
- Compatible vehicle system (Firstech/Compustar)

## Support

- [Report Issues](https://github.com/bjhiltbrand/drone_mobile_home_assistant/issues)
- [Documentation](https://github.com/bjhiltbrand/drone_mobile_home_assistant#readme)

---

⚠️ **Disclaimer**: This integration uses an unofficial API and is not affiliated with DroneMobile. Use at your own risk.

[commits-shield]: https://img.shields.io/github/commit-activity/y/bjhiltbrand/drone_mobile_home_assistant.svg
[commits]: https://github.com/bjhiltbrand/drone_mobile_home_assistant/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg
[license-shield]: https://img.shields.io/github/license/bjhiltbrand/drone_mobile_home_assistant.svg
[releases-shield]: https://img.shields.io/github/release/bjhiltbrand/drone_mobile_home_assistant.svg
[releases]: https://github.com/bjhiltbrand/drone_mobile_home_assistant/releases