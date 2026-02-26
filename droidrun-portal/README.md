# droidrun-portal

A Claude Code skills plugin for controlling Android devices via [droidrun-portal](https://github.com/droidrun/droidrun-portal)'s ADB ContentProvider interface.

## Features

- **No Python dependencies** — All functionality works via ADB shell commands
- **Helper scripts** — Optional Python scripts for common operations
- **Smart filtering** — Removes noise elements, tiny elements, keyboard clutter
- **Index-based tapping** — O(1) element lookup for fast automation

## Installation

### Prerequisites

1. **ADB installed** — Android SDK Platform Tools on your PATH
2. **Android device** — USB debugging enabled, connected via USB or WiFi
3. **droidrun-portal APK** — Installed on the device with accessibility service enabled

### Install as Claude Code Plugin

```bash
# Navigate to your Claude Code plugins directory
cd ~/.claude/plugins

# Clone or symlink this repository
git clone <repo-url> droidrun-portal
# Or symlink if developing locally:
ln -s /path/to/skills/droidrun-portal droidrun-portal

# Restart Claude Code to load the plugin
```

### Verify Installation

In Claude Code, the skills should now be available:
- `android-setup` — Device connection and portal installation
- `android-observe` — Read UI elements and device state
- `android-interact` — Tap, swipe, type, and navigate
- `android-apps` — Launch, stop, and manage apps

## Available Skills

| Skill | Description | Use When |
|-------|-------------|----------|
| `android-setup` | Device connection, portal installation, accessibility service | Setting up a new device |
| `android-observe` | Query UI elements, take screenshots, check app state | Need to see what's on screen |
| `android-interact` | Tap, swipe, type text, press keys, navigate | Need to interact with the device |
| `android-apps` | Launch apps, stop apps, list packages, install APKs | Managing app lifecycle |

## Helper Scripts

Optional Python scripts in `scripts/` simplify common operations:

```bash
# Observe UI elements
python3 scripts/droid-observe.py
python3 scripts/droid-observe.py --phone-state

# Tap by text
python3 scripts/droid-tap.py "Submit"
python3 scripts/droid-tap.py "Submit" --exact --avoid-overlap

# Tap by index (faster)
python3 scripts/droid-tap-index.py 5

# Type text
python3 scripts/droid-type.py "Hello World"
python3 scripts/droid-type.py "replacement" --clear

# Wait for element
python3 scripts/droid-wait.py "Loading" --timeout 30
```

### Script Features

- **Shared utilities** (`droidutils.py`) — Common functions for all scripts
- **Smart filtering** — Removes layout containers, tiny elements (<5px), keyboard elements, off-screen elements
- **Retry logic** — Handles flaky ADB connections
- **Clear point detection** — Finds unblocked tap points for overlapping elements

## Quick Start

1. **Setup device:**
   ```bash
   # Install portal APK
   adb install droidrun-portal.apk

   # Enable accessibility service
   adb shell settings put secure enabled_accessibility_services \
     com.droidrun.portal/.service.DroidrunAccessibilityService

   # Verify connection
   adb shell content query --uri content://com.droidrun.portal/ping
   ```

2. **Observe screen:**
   ```bash
   python3 scripts/droid-observe.py --phone-state
   ```

3. **Interact:**
   ```bash
   python3 scripts/droid-tap.py "Settings"
   ```

## ContentProvider API Reference

| URI | Method | Purpose |
|-----|--------|---------|
| `/ping` | query | Verify portal is running |
| `/version` | query | Get portal version |
| `/a11y_tree` | query | Get UI elements with indices |
| `/a11y_tree_full` | query | Get complete accessibility tree |
| `/phone_state` | query | Get current app, keyboard status |
| `/state_full` | query | Combined tree + state + device info |
| `/packages` | query | List installed launchable apps |
| `/keyboard/input` | insert | Type text (base64-encoded) |
| `/keyboard/clear` | insert | Clear focused text field |
| `/keyboard/key` | insert | Send key event |

## Project Structure

```
droidrun-portal/
├── .claude-plugin/        # Plugin metadata
│   ├── plugin.json
│   └── marketplace.json
├── scripts/               # Python helper scripts
│   ├── droidutils.py      # Shared utilities module
│   ├── droid-observe.py   # Query UI elements
│   ├── droid-tap.py       # Tap by text search
│   ├── droid-tap-index.py # Tap by element index
│   ├── droid-type.py      # Type text
│   └── droid-wait.py      # Wait for element
├── skills/                # Claude Code skill definitions
│   ├── android-setup/     # Device setup skill
│   ├── android-observe/   # Observation skill
│   ├── android-interact/  # Interaction skill
│   └── android-apps/      # App management skill
├── docs/plans/            # Design documents
├── CLAUDE.md              # Claude Code project config
└── README.md              # This file
```

## Requirements

- Python 3.8+ (for helper scripts only)
- ADB (Android SDK Platform Tools)
- Android device with:
  - USB debugging enabled
  - droidrun-portal APK installed
  - Accessibility service enabled

## License

MIT
