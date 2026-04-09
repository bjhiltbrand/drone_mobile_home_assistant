# Migration Guide: DroneMobile Home Assistant Integration v1.0.0

This guide covers the migration from the old integration (using drone_mobile 0.2.30) to the new version (using drone_mobile 0.3.3).

## What Changed

### Major Updates

1. **Updated to drone_mobile 0.3.3** - The underlying Python package has been completely refactored with:
   - Modern type hints
   - Better error handling
   - Improved authentication
   - Data models (VehicleInfo, VehicleStatus, etc.)

2. **Modernized Home Assistant Integration**
   - Updated to current HA best practices
   - Better error handling with proper exception types
   - Improved configuration flow
   - Enhanced logging

3. **API Changes** - The new drone_mobile package uses different method names:
   - `Vehicle` → `DroneMobileClient`
   - `getAllVehicles()` → `get_vehicles()`
   - `vehicle_status()` → `get_vehicle_status()`
   - `sendCommand()` → `send_command()`

## Installation

### Fresh Installation

1. Copy the entire `custom_components/drone_mobile` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Configuration → Integrations → Add Integration
4. Search for "DroneMobile" and follow the setup wizard

### Upgrading from Old Version

**IMPORTANT**: You will need to remove and re-add the integration.

1. **Backup your configuration** (optional but recommended)
   
2. **Remove the old integration**:
   - Go to Configuration → Integrations
   - Find your DroneMobile integration(s)
   - Click the three dots and select "Delete"

3. **Update the integration files**:
   - Replace the entire `custom_components/drone_mobile` folder with the new version
   
4. **Restart Home Assistant**

5. **Re-add the integration**:
   - Go to Configuration → Integrations → Add Integration
   - Search for "DroneMobile"
   - Enter your credentials
   - Select your vehicle(s)

6. **Update automations** (if needed):
   - Entity IDs may have changed slightly
   - Service names remain the same format

## Key Differences

### Entity Naming

The entity naming has been improved for consistency:

**Old Format:**
```
sensor.my_vehicle_odometer
lock.my_vehicle_doorLock
switch.my_vehicle_remoteStart_Switch
```

**New Format:**
```
sensor.my_vehicle_odometer
lock.my_vehicle_door_lock
switch.my_vehicle_remote_start
```

### Service Names

Service names follow the same pattern but use lowercase with underscores:

```yaml
# Refresh device status (per vehicle)
service: drone_mobile.refresh_device_status_my_vehicle

# These services have been removed (functionality integrated differently):
# - dump_device_data (use Developer Tools → States instead)
# - clear_temp_token (token management is automatic now)
# - replace_token (token management is automatic now)
```

### Available Entities

All original entities are still available:

**Sensors:**
- Odometer
- Battery (voltage + percentage)
- Temperature (interior + exterior)
- GPS Location
- Alarm Status
- Ignition Status
- Engine Status
- Door Status
- Trunk Status
- Hood Status
- Last Refresh Timestamp

**Locks:**
- Door Lock
- Trunk (with open support)

**Switches:**
- Remote Start
- Panic Alarm

**Buttons:**
- Auxiliary 1 (momentary)
- Auxiliary 2 (momentary)

**Device Tracker:**
- GPS Location Tracker

## Configuration Options

The same configuration options are available:

- **Units**: Imperial or Metric
- **Update Interval**: 2-60 minutes
- **Override Lock State Check**: Send lock commands regardless of current state

## Error Handling

The new version has significantly improved error handling:

- Better authentication error messages
- Clearer command failure reasons
- Automatic token refresh
- Network error recovery

## Breaking Changes

### 1. Entity ID Format Changes

Some entity IDs have changed format. Update your automations:

```yaml
# OLD
entity_id: lock.my_vehicle_doorLock
entity_id: switch.my_vehicle_remoteStart_Switch

# NEW
entity_id: lock.my_vehicle_door_lock
entity_id: switch.my_vehicle_remote_start
```

### 2. Removed Services

These services have been removed as they're no longer needed:

- `drone_mobile.dump_device_data_*` - Use Developer Tools → States to view entity data
- `drone_mobile.clear_temp_token` - Token management is now automatic
- `drone_mobile.replace_token` - Token management is now automatic

### 3. Token Storage Location

Tokens are now stored in `~/.config/.storage/core.config_entries` instead of the HA config directory. This is handled automatically by the new package.

## Troubleshooting

### Authentication Issues

If you experience authentication problems:

1. Check your credentials are correct
2. Remove and re-add the integration
3. Check the Home Assistant logs for detailed error messages

### Missing Entities

Some entities only appear if your vehicle supports them:

- **GPS entities** only appear if your vehicle reports location
- **Temperature** shows "Unsupported" if not available

### Service Not Found

If `drone_mobile.refresh_device_status_*` isn't working:

1. Check the exact service name in Developer Tools → Services
2. The vehicle name is converted to lowercase with underscores
3. Example: "My Vehicle" → `refresh_device_status_my_vehicle`

## Support

For issues:

1. Check the [GitHub Issues](https://github.com/bjhiltbrand/drone_mobile_home_assistant/issues)
2. Enable debug logging:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.drone_mobile: debug
       drone_mobile: debug
   ```
3. Check Home Assistant logs for detailed error messages

## Benefits of Upgrading

1. **Better Reliability** - Improved error handling and automatic token refresh
2. **Better Performance** - More efficient API usage
3. **Better Diagnostics** - Enhanced logging and error messages
4. **Future-Proof** - Built on modern, maintainable codebase
5. **Type Safety** - Full type hints for better IDE support during development

## Example Automations

### Remote Start with Temperature Check

```yaml
automation:
  - alias: "Auto-start car when cold"
    trigger:
      - platform: numeric_state
        entity_id: sensor.my_vehicle_temperature
        below: 32
    condition:
      - condition: state
        entity_id: switch.my_vehicle_remote_start
        state: 'off'
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.my_vehicle_remote_start
```

### Lock Reminder

```yaml
automation:
  - alias: "Notify if car left unlocked"
    trigger:
      - platform: state
        entity_id: lock.my_vehicle_door_lock
        to: 'unlocked'
        for:
          minutes: 10
    action:
      - service: notify.mobile_app
        data:
          message: "Your car has been unlocked for 10 minutes"
```

### Refresh Status Before Use

```yaml
automation:
  - alias: "Refresh car status before leaving"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: drone_mobile.refresh_device_status_my_vehicle
      - delay:
          seconds: 30
      - service: notify.mobile_app
        data:
          message: "Car status: {{ states('sensor.my_vehicle_engine') }}"
```