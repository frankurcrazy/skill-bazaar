---
name: android-apps
description: Use when needing to launch apps, stop apps, list installed applications, install APKs, or find package names on an Android device
---

# Android Apps

Manage app lifecycle on Android devices. List installed apps to find package names, launch apps, stop them, and install new APKs.

## Quick Reference

| Action | Command |
|--------|---------|
| List apps | `adb shell content query --uri content://com.droidrun.portal/packages` |
| Launch app | `adb shell monkey -p <package> -c android.intent.category.LAUNCHER 1` |
| Launch with activity | `adb shell am start -n <package>/<activity>` |
| Stop app | `adb shell am force-stop <package>` |
| Install APK | `adb install <path>` |
| Install with permissions | `adb install -g <path>` |
| Reinstall | `adb install -r <path>` |

## Listing Installed Apps

```bash
# List all launchable apps (via portal — returns JSON with package names and labels)
adb shell content query --uri content://com.droidrun.portal/packages

# List all packages (via pm — package names only, no labels)
adb shell pm list packages -3
```

The portal's `/packages` command returns JSON with both package names and human-readable labels, which is more useful for finding the right app.

## Launching Apps

```bash
# Launch by package name (finds launcher activity automatically)
adb shell monkey -p com.android.chrome -c android.intent.category.LAUNCHER 1

# Launch with specific activity
adb shell am start -n com.android.settings/.Settings

# Launch and wait for it to fully start
adb shell am start -W -n com.android.settings/.Settings
```

After launching, always wait and verify:
```bash
sleep 2
adb shell content query --uri content://com.droidrun.portal/phone_state
```
Check that `current_activity` matches the expected app.

## Stopping Apps

```bash
# Force stop an app
adb shell am force-stop com.android.chrome
```

## Installing APKs

```bash
# Install an APK
adb install /path/to/app.apk

# Install and auto-grant runtime permissions
adb install -g /path/to/app.apk

# Reinstall (keep data)
adb install -r /path/to/app.apk

# Install from device path (if APK is already on device)
adb shell pm install /sdcard/Download/app.apk
```

## Common Package Names

| App | Package |
|-----|---------|
| Settings | `com.android.settings` |
| Chrome | `com.android.chrome` |
| Camera | `com.android.camera2` or `com.google.android.GoogleCamera` |
| Phone/Dialer | `com.android.dialer` or `com.google.android.dialer` |
| Messages | `com.google.android.apps.messaging` |
| Gmail | `com.google.android.gm` |
| Google Maps | `com.google.android.apps.maps` |
| YouTube | `com.google.android.youtube` |
| Play Store | `com.android.vending` |
| Files | `com.google.android.apps.nbu.files` |
| Clock | `com.google.android.deskclock` |
| Calculator | `com.google.android.calculator` |
| Calendar | `com.google.android.calendar` |
| Contacts | `com.google.android.contacts` |

Note: Package names vary by manufacturer. Always use `packages` query to find the exact package name on the device.

## Common Mistakes

- Using wrong package name — always list packages first to find the exact name
- Not waiting after launch — app needs time to start; use `sleep 2` then verify with `phone_state`
- Trying to launch with wrong activity — use `monkey` command which auto-finds the launcher activity
- Installing unsigned APK — device may need "Install from unknown sources" enabled
