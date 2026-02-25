---
name: android-observe
description: Use when needing to see what is on an Android device screen, read UI elements, get the accessibility tree, take screenshots, check which app is running, or determine keyboard visibility
---

# Observing Android Device State

Read Android device state via droidrun-portal's ContentProvider. Always observe before interacting — get the screen state to understand what elements are available and where they are.

## Helper Scripts (Recommended)

Helper scripts in `droidrun-portal/scripts/` simplify common operations. Use these instead of raw commands when possible.

```bash
# See all meaningful UI elements on screen (clean flat list)
python3 scripts/droid-observe.py

# Include current activity and keyboard status
python3 scripts/droid-observe.py --phone-state

# Include layout containers (normally filtered out)
python3 scripts/droid-observe.py --all

# Multi-device: specify serial
python3 scripts/droid-observe.py -s SERIAL
```

Output format (one line per element):
```
[3] "Settings" center=(540,150) bounds=(0,100,1080,200) class=TextView
[7] "Wi-Fi" center=(540,350) bounds=(0,300,1080,400) class=TextView id=title
```

The scripts directory also contains `droid-tap.py`, `droid-wait.py`, and `droid-type.py` — see the android-interact skill for details.

## Quick Reference

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `state_full` | Full UI tree + phone state + device info | Default starting point |
| `state` | UI tree + phone state | When you don't need device info |
| `a11y_tree` | Visible interactive elements with indices | Quick element lookup |
| `a11y_tree_full` | Complete accessibility tree, all properties | Debugging UI issues |
| `phone_state` | Current activity, focused element, keyboard | Check app/keyboard status only |
| `packages` | Installed launchable apps | Finding package names |
| `version` | Portal app version | Verify portal is installed |
| Screenshot | Screen capture as PNG | Visual verification |

## Commands

```bash
# Get full device state (recommended first call)
adb shell content query --uri content://com.droidrun.portal/state_full

# Get combined tree + phone state
adb shell content query --uri content://com.droidrun.portal/state

# Get visible elements with overlay indices
adb shell content query --uri content://com.droidrun.portal/a11y_tree

# Get complete accessibility tree (all properties)
adb shell content query --uri content://com.droidrun.portal/a11y_tree_full

# Get complete tree without filtering small elements
adb shell content query --uri "content://com.droidrun.portal/a11y_tree_full?filter=false"

# Get phone state only
adb shell content query --uri content://com.droidrun.portal/phone_state

# List installed launchable apps
adb shell content query --uri content://com.droidrun.portal/packages

# Get portal app version
adb shell content query --uri content://com.droidrun.portal/version

# Take screenshot (save locally)
adb exec-out screencap -p > /tmp/android-screenshot.png
```

## Parsing Responses

ContentProvider responses come as:

```
Row: 0 result=<JSON_STRING>
```

Strip the `Row: 0 result=` prefix to get the JSON.

The `state_full` response contains:

```json
{
  "a11y_tree": [
    {
      "index": 1,
      "resourceId": "",
      "className": "android.widget.TextView",
      "text": "Settings",
      "bounds": "0, 100, 1080, 200",
      "children": []
    }
  ],
  "phone_state": {
    "currentApp": "Settings",
    "packageName": "com.android.settings",
    "activityName": "com.android.settings/.Settings",
    "keyboardVisible": false,
    "isEditable": false,
    "focusedElement": {"resourceId": ""}
  }
}
```

## Extracting Element Coordinates from Bounds

Bounds format is `"left, top, right, bottom"` — four comma-separated integers in a string. The tree is nested with a `children` array on each node.

To get the center point for tapping:

- `center_x = (left + right) / 2`
- `center_y = (top + bottom) / 2`

Example: bounds `"0, 100, 1080, 200"` gives center `(540, 150)`.

## Finding Elements by Text

Use the helper script for a one-liner: `python3 scripts/droid-tap.py "Submit"`

Or manually:

1. Run `state_full`
2. Parse the JSON (response is double-encoded: strip `Row: 0 result=`, parse outer JSON, then parse `result` string)
3. Recursively walk the `a11y_tree` tree (each node has a `children` array)
4. Find elements where `text` contains "Submit"
5. Parse its `bounds` string: `"left, top, right, bottom"`
6. Calculate center coordinates
7. Use the android-interact skill to tap those coordinates

## The Observe-Act-Verify Pattern

1. **Observe** -- Call `state_full` to see the current screen
2. **Identify** -- Find the target element in the tree
3. **Act** -- Use the android-interact skill to tap/type/swipe
4. **Verify** -- Call `state_full` again to confirm the action worked

Always verify after acting. Screens can change unexpectedly.

## Common Mistakes

- **Tapping without observing first** -- always get state before interacting
- **Using stale state** -- re-observe after every action
- **Ignoring `keyboard_shown`** -- when the keyboard is up, some elements may be hidden
- **Not checking `current_activity`** -- make sure you are on the expected screen
