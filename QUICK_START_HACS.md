# Quick Start Guide for HACS

## Immediate Steps (Do This First)

### 1. Add Required Files

Copy these three new files to your repository root:

```bash
# Create these files in your repository root
hacs.json
info.md
.github/workflows/validate.yml
```

### 2. Update manifest.json

Already done! Just verify `requirements` is set to `drone_mobile==0.3.3`

### 3. Commit and Push

```bash
git add hacs.json info.md .github/
git commit -m "Add HACS support"
git push
```

### 4. Create First Release

```bash
# Tag the release
git tag v1.0.0

# Push the tag
git push origin v1.0.0
```

Then on GitHub:
1. Go to your repository
2. Click "Releases" → "Draft a new release"
3. Choose tag: `v1.0.0`
4. Title: `v1.0.0 - Initial HACS Release`
5. Description:
   ```markdown
   ## What's New
   
   - Complete refactor with drone_mobile 0.3.3
   - Modern Home Assistant integration
   - New button platform for Aux controls
   - Improved sensor data parsing
   - Better error handling
   - Immediate UI feedback for switches
   
   ## Breaking Changes
   
   - Aux1 and Aux2 are now buttons instead of switches
   - Entity IDs have changed (snake_case format)
   - Must remove and re-add integration
   
   See MIGRATION_GUIDE.md for details.
   ```
6. Click "Publish release"

### 5. Add Repository Topics

On GitHub:
1. Click the gear icon next to "About"
2. Add topics: `home-assistant`, `hacs`, `homeassistant`, `integration`, `dronemobile`
3. Save

## Users Can Now Install

### As Custom Repository (Available Immediately)

Users can add it right now:

1. HACS → Integrations
2. Three dots (⋮) → Custom repositories
3. URL: `https://github.com/bjhiltbrand/drone_mobile_home_assistant`
4. Category: Integration
5. Click Add
6. Search "DroneMobile" in HACS
7. Click Install

### As Default Repository (Requires Approval)

Submit to HACS default:

1. Fork: https://github.com/hacs/default
2. Edit the `integration` file
3. Add your entry alphabetically:
   ```json
   {
     "name": "DroneMobile",
     "domain": "drone_mobile",
     "owner": "bjhiltbrand",
     "repository": "drone_mobile_home_assistant"
   }
   ```
4. Create PR with title: "Add DroneMobile integration"
5. Wait for review (usually 3-7 days)

## Testing

Test that everything works:

```bash
# In your Home Assistant config directory
cd custom_components/drone_mobile

# Verify all files are present
ls -la

# Should see:
# __init__.py
# button.py
# config_flow.py
# const.py
# device_tracker.py
# lock.py
# manifest.json
# sensor.py
# services.yaml
# strings.json
# switch.py
# translations/en.json
```

## Troubleshooting

### HACS Validation Fails

Check:
- manifest.json is valid JSON
- All required files exist
- No syntax errors in Python files

### Users Can't Find Integration

Make sure:
- Release is published (not draft)
- hacs.json exists in root
- Repository is public

### Installation Errors

Check:
- drone_mobile 0.3.3 is published on PyPI
- manifest.json has correct requirements

## Next Steps

1. ✅ Create release (v1.0.0)
2. ✅ Publish info for users
3. ✅ Test installation as custom repo
4. ⏳ Submit to HACS default (optional)
5. 📢 Announce in Home Assistant community

## Support Users

Update your README with installation instructions:

```markdown
## Installation

### HACS (Recommended)

1. Add as custom repository in HACS:
   - HACS → Integrations → ⋮ → Custom repositories
   - URL: `https://github.com/bjhiltbrand/drone_mobile_home_assistant`
   - Category: Integration
2. Click "Install"
3. Restart Home Assistant
4. Add integration via UI

### Manual

1. Copy `custom_components/drone_mobile` to your config
2. Restart Home Assistant
3. Add integration via UI
```

## You're Done!

Your integration is now HACS-ready. Users can install it as a custom repository immediately, and you can submit to HACS default whenever you're ready.