---
name: android-interact
description: Use when needing to tap, click, swipe, scroll, type text, press keys, or navigate on an Android device — any physical interaction with the phone screen
---

# Android Interact

Perform actions on Android devices via ADB and droidrun-portal's ContentProvider. Always use the android-observe skill first to understand the current screen before interacting.

## Helper Scripts (Recommended)

Helper scripts in `droidrun-portal/scripts/` simplify common operations. Use these instead of raw commands when possible.

```bash
# Tap element by text (finds it in a11y_tree, calculates center, taps)
python3 scripts/droid-tap.py "Submit"
python3 scripts/droid-tap.py "Submit" --exact    # exact text match only
python3 scripts/droid-tap.py "Submit" --avoid-overlap  # find clear tap point

# Tap element by index (faster, from droid-observe output)
python3 scripts/droid-tap-index.py 5             # tap element [5]
python3 scripts/droid-tap-index.py 5 --avoid-overlap  # avoid overlapping elements

# Type text via ContentProvider (supports Unicode)
python3 scripts/droid-type.py "Hello World"
python3 scripts/droid-type.py "replacement" --clear  # clear field first

# Wait for element to appear (polls every 1s)
python3 scripts/droid-wait.py "Submit"
python3 scripts/droid-wait.py "Loading" --timeout 30

# Multi-device: specify serial
python3 scripts/droid-tap.py "OK" -s SERIAL
```

## Quick Reference

| Action | Command | Example |
|--------|---------|---------|
| Tap | `adb shell input tap X Y` | `adb shell input tap 540 150` |
| Swipe | `adb shell input swipe X1 Y1 X2 Y2 MS` | `adb shell input swipe 540 1500 540 500 300` |
| Long press | `adb shell input swipe X Y X Y 1000` | Same start/end, long duration |
| Type text | ContentProvider keyboard/input | See Text Input section |
| Clear field | ContentProvider keyboard/clear | See Text Input section |
| Key event | ContentProvider keyboard/key | See Key Events section |
| Back | `adb shell input keyevent 4` | |
| Home | `adb shell input keyevent 3` | |

## Touch and Gestures

```bash
# Tap at coordinates (get coordinates from android-observe bounds)
adb shell input tap 540 150

# Swipe from point A to point B over duration in milliseconds
adb shell input swipe 540 1500 540 500 300

# Long press (swipe with same start and end coordinates, long duration)
adb shell input swipe 540 960 540 960 1000
```

## Calculating Tap Coordinates

From android-observe, elements have bounds `"left, top, right, bottom"` (four comma-separated integers in a string).

```
center_x = (left + right) / 2
center_y = (top + bottom) / 2
```

Example: element with bounds `"100, 400, 980, 500"` → tap at `(540, 450)`.

## Common Swipe Patterns

| Gesture | Command | Notes |
|---------|---------|-------|
| Scroll down | `adb shell input swipe 540 1500 540 500 300` | Finger moves up |
| Scroll up | `adb shell input swipe 540 500 540 1500 300` | Finger moves down |
| Swipe left | `adb shell input swipe 900 960 100 960 300` | For next page |
| Swipe right | `adb shell input swipe 100 960 900 960 300` | For previous page |

Adjust coordinates for device screen size. These examples assume 1080x1920 resolution.

## Text Input

Use droidrun-portal's ContentProvider for text input — it supports Unicode and special characters (unlike `adb shell input text` which only handles ASCII).

```bash
# Type text (base64-encoded for Unicode/special char support)
adb shell content insert --uri content://com.droidrun.portal/keyboard/input \
  --bind base64_text:s:$(echo -n "Hello World" | base64) \
  --bind clear:b:false

# Type text and clear field first
adb shell content insert --uri content://com.droidrun.portal/keyboard/input \
  --bind base64_text:s:$(echo -n "replacement text" | base64) \
  --bind clear:b:true

# Clear the focused text field
adb shell content insert --uri content://com.droidrun.portal/keyboard/clear
```

Important: The text field must be focused before typing. Tap the field first if needed.

## Key Events

```bash
# Send a key event by Android key code
adb shell content insert --uri content://com.droidrun.portal/keyboard/key \
  --bind key_code:i:66
```

### Key Code Reference

| Key | Code | Key | Code |
|-----|------|-----|------|
| Home | 3 | Back | 4 |
| Enter/Return | 66 | Backspace/Delete | 67 |
| Tab | 61 | Escape | 111 |
| Arrow Up | 19 | Arrow Down | 20 |
| Arrow Left | 21 | Arrow Right | 22 |
| Volume Up | 24 | Volume Down | 25 |
| Power | 26 | Camera | 27 |

## Navigation Shortcuts

```bash
# Go back
adb shell input keyevent 4

# Go home
adb shell input keyevent 3

# Open recent apps
adb shell input keyevent 187

# Open notifications
adb shell cmd statusbar expand-notifications
```

## The Observe-Act-Verify Workflow

1. **Observe** — Use android-observe skill: `adb shell content query --uri content://com.droidrun.portal/state_full`
2. **Find target** — Parse response, find element by text/class, extract bounds
3. **Calculate coordinates** — `center_x = (left+right)/2`, `center_y = (top+bottom)/2`
4. **Act** — Tap, type, swipe using commands above
5. **Verify** — Re-observe to confirm the action worked
6. **Repeat** — Continue with next action if needed

## Common Mistakes

- Tapping without observing first — coordinates may be wrong
- Forgetting to focus a text field before typing
- Using `adb shell input text` instead of ContentProvider (fails with Unicode/spaces)
- Not waiting between actions — add `sleep 1` between rapid actions if screen needs time to update
- Using wrong coordinates after scrolling — always re-observe after scrolling
