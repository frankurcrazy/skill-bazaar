---
name: android-setup
description: Use when connecting to an Android device, setting up droidrun-portal, installing the portal APK, enabling accessibility services, or troubleshooting ADB device connections
---

# Android Device Setup for droidrun-portal

One-time setup for controlling Android devices via droidrun-portal. Requires ADB on the host machine and the droidrun-portal APK installed on the Android device. No Python environment or droidrun framework is needed.

## Prerequisites

- **ADB installed** on the host machine:
  - macOS: `brew install android-platform-tools`
  - Linux: `apt install adb`
- **USB debugging enabled** on the Android device:
  1. Go to Settings > About phone
  2. Tap "Build Number" 7 times to unlock Developer Options
  3. Go to Settings > Developer Options > enable USB Debugging
- **Device connected** via USB cable or wireless ADB

## Quick Reference

| Step | Command |
|------|---------|
| Check device connected | `adb devices` |
| Install portal APK | `adb install droidrun-portal.apk` |
| Enable accessibility | `adb shell settings put secure enabled_accessibility_services com.droidrun.portal/.service.DroidrunAccessibilityService` |
| Verify connection | `adb shell content query --uri content://com.droidrun.portal/ping` |
| Check version | `adb shell content query --uri content://com.droidrun.portal/version` |

## Installation Steps

1. Download the latest portal APK from https://github.com/droidrun/droidrun-portal/releases

2. Install the APK:
   ```bash
   adb install droidrun-portal.apk
   ```

3. Enable the accessibility service (choose one method):
   - **Via ADB (recommended):**
     ```bash
     adb shell settings put secure enabled_accessibility_services com.droidrun.portal/.service.DroidrunAccessibilityService
     ```
     **Warning:** This replaces all existing accessibility services. If the device has other services enabled (e.g., TalkBack), append instead:
     ```bash
     # Read current services first
     adb shell settings get secure enabled_accessibility_services
     # Append with colon separator
     adb shell settings put secure enabled_accessibility_services \
       <existing_services>:com.droidrun.portal/.service.DroidrunAccessibilityService
     ```
   - **Manually (safest):** Settings > Accessibility > Droidrun Portal > Enable

4. Grant the overlay permission when prompted on the device screen.

5. Verify the setup:
   ```bash
   adb shell content query --uri content://com.droidrun.portal/ping
   ```
   Expected response: `{"status":"success","result":"pong"}`

## Overlay Configuration

```bash
# Show overlay (highlights interactive elements on screen)
adb shell content insert --uri content://com.droidrun.portal/overlay_visible --bind visible:b:true

# Hide overlay
adb shell content insert --uri content://com.droidrun.portal/overlay_visible --bind visible:b:false

# Adjust vertical offset (in pixels)
adb shell content insert --uri content://com.droidrun.portal/overlay_offset --bind offset:i:50
```

## Wireless ADB Setup (Android 11+)

1. Enable wireless debugging: Settings > Developer Options > Wireless debugging
2. Pair with the device:
   ```bash
   adb pair <ip>:<port>
   ```
   Enter the pairing code shown on the device screen.
3. Connect to the device:
   ```bash
   adb connect <ip>:<port>
   ```
   Use the **connection** port displayed under wireless debugging, which is different from the pairing port.

## Multiple Devices

When multiple devices are connected, target a specific device with `-s <serial>`:

```bash
# List all connected devices
adb devices

# Target a specific device
adb -s DEVICE_SERIAL shell content query --uri content://com.droidrun.portal/ping
```

Add `-s <serial>` before any subcommand in all `adb` commands throughout this guide.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "device not found" | Check USB cable, re-enable USB debugging, run `adb kill-server && adb start-server` |
| Portal not responding | Ensure the accessibility service is enabled, restart the portal app on the device |
| "permission denied" | Accept the USB debugging authorization prompt on the device screen |
| APK install fails | Enable "Install from unknown sources" in device settings, or use `adb install -r` to reinstall |
