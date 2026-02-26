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

**Option 1: Add as a marketplace (recommended for Git repos)**

```bash
# Add this repository as a marketplace
/plugin marketplace add https://github.com/user/skills.git

# Then install the plugin
/plugin install droidrun-portal@skills
```

**Option 2: Add as a local marketplace (for local development)**

```bash
# Add the local directory as a marketplace
/plugin marketplace add /path/to/skills

# Then install the plugin
/plugin install droidrun-portal@skills --scope local
```

**Option 3: Interactive installation**

```bash
# Open the plugin manager
/plugin

# Navigate to Marketplaces tab → Add your marketplace
# Then go to Discover tab → Find and install droidrun-portal
```

### Verify Installation

After installation, the skills should be available. Test with:
```bash
/plugin  # Go to "Installed" tab to verify
```

Available skills:
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
python3 scripts/droid-observe.py --full --json  # Complete tree

# Tap by text
python3 scripts/droid-tap.py "Submit"
python3 scripts/droid-tap.py "Submit" --exact --avoid-overlap

# Tap by index (faster)
python3 scripts/droid-tap-index.py 5
python3 scripts/droid-tap-index.py 5 --full  # Use with --full observe

# Long-press
python3 scripts/droid-longpress.py "Item"
python3 scripts/droid-longpress-index.py 5 --duration 2000

# Type text
python3 scripts/droid-type.py "Hello World"
python3 scripts/droid-type.py "replacement" --clear

# Wait for element
python3 scripts/droid-wait.py "Loading" --timeout 30

# Window overlays (bubbles, PiP) - not in accessibility tree
python3 scripts/droid-windows.py           # List overlay windows
python3 scripts/droid-windows.py --all     # List all visible windows
python3 scripts/droid-tap-window.py "Bubbles"  # Tap window by name
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
│   ├── droid-longpress.py # Long-press by text
│   ├── droid-longpress-index.py # Long-press by index
│   ├── droid-type.py      # Type text
│   ├── droid-wait.py      # Wait for element
│   ├── droid-windows.py   # List system overlay windows
│   └── droid-tap-window.py # Tap overlay by window name
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
