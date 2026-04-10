# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project uses [CalVer](https://calver.org/) versioning (`YYYY.M.D`).

---

## [2026.4.10] - 2026-04-10

### Added
- Multi-factor authentication (MFA) support in the config flow
  - Handles both `SMS_MFA` and `SOFTWARE_TOKEN_MFA` Cognito challenge types
  - Dedicated `async_step_mfa` config flow step collects the OTP from the user
  - Human-readable prompt tells the user whether to check their SMS or authenticator app
  - If a cached refresh token later expires and Cognito re-requires MFA, Home Assistant
    will automatically start the re-auth flow rather than silently failing

### Fixed
- `DroneMobilePanic` switch: missing top-level `datetime`/`timedelta` imports caused
  a `NameError` at runtime when the panic alarm was triggered
- `DroneMobilePanic.is_on` now correctly honours `_manual_state_expiry`, matching
  the behaviour of `DroneMobileRemoteStart`
- `DroneMobilePanic._handle_coordinator_update` now also clears `_manual_state_expiry`

### Changed
- Removed empty `"dependencies": []` from `manifest.json` (no functional impact;
  Home Assistant treats absence and an empty list identically)
- Added explicit `"filename": "drone_mobile.zip"` to `hacs.json` for clarity
- Bumped all GitHub Actions `actions/checkout` steps to `v4` for consistency

---

## [2026.4.9] - 2026-04-09

### Added
- Complete refactor targeting `drone_mobile==0.3.3`
- Modern Home Assistant integration patterns (coordinator, config entries, options flow)
- New `button` platform for Aux 1 and Aux 2 controls (replaces old switches)
- Improved sensor data parsing against updated data models
  (`VehicleInfo`, `VehicleStatus`, etc.)
- Better error handling with typed exceptions (`AuthenticationError`,
  `CommandFailedError`, `DroneMobileException`)
- Immediate UI feedback for switches via `_manual_state` override pattern
- HACS support (`hacs.json`, `info.md`, GitHub Actions workflows)
- Options flow for post-setup reconfiguration (units, update interval, lock override)

### Breaking Changes
- `Aux1` and `Aux2` are now `button` entities instead of `switch` entities
- Entity IDs have changed to snake_case format (e.g. `lock.my_car_door_lock`
  instead of `lock.my_car_doorLock`)
- Integration must be removed and re-added after upgrading

See `custom_components/drone_mobile/MIGRATION_GUIDE.md` for full details.