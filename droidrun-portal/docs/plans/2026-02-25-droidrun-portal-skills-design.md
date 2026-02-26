# Droidrun Portal Skills Plugin — Design Document

## Goal

Create a Claude Code plugin that lets Claude directly control Android devices via droidrun-portal's ADB ContentProvider interface, without requiring the droidrun Python framework.

## Architecture

**droidrun-portal** is an Android accessibility service app that exposes device control via:
- ContentProvider (`content://com.droidrun.portal/...`) — accessed via `adb shell content query/insert`
- HTTP server (port 8080) — REST API with bearer token auth
- WebSocket server (port 8081) — real-time control

This plugin uses **ContentProvider exclusively** (plus `adb shell input` for taps/swipes) for zero-config operation — no port forwarding or auth tokens needed.

## Plugin Structure

```
droidrun-portal/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── scripts/
│   ├── droidutils.py        # Shared utilities module
│   ├── droid-observe.py     # Query UI elements
│   ├── droid-tap.py         # Tap by text search
│   ├── droid-tap-index.py   # Tap by element index
│   ├── droid-type.py        # Type text
│   └── droid-wait.py        # Wait for element
├── skills/
│   ├── android-setup/
│   │   └── SKILL.md
│   ├── android-observe/
│   │   └── SKILL.md
│   ├── android-interact/
│   │   └── SKILL.md
│   └── android-apps/
│       └── SKILL.md
└── README.md
```

## Skills

### 1. android-setup

**Purpose:** One-time device setup and connection verification.

**Triggers:** "connect to phone", "set up Android device", "install droidrun portal", "enable accessibility"

**Commands covered:**
- ADB device detection and connection
- Portal APK installation from GitHub releases
- Accessibility service enablement
- Connection verification via ping
- Overlay configuration
- Wireless ADB setup

### 2. android-observe

**Purpose:** Read device state, UI elements, and capture screenshots.

**Triggers:** "what's on screen", "get device state", "take screenshot", "read UI elements"

**Commands covered:**
- `state_full` — full accessibility tree + phone state + device context
- `state` — combined tree + phone state
- `a11y_tree` / `a11y_tree_full` — UI element trees
- `phone_state` — current activity, focused element, keyboard visibility
- Screenshots via `adb exec-out screencap -p`

**Guidance:** How to parse JSON responses, extract element bounds, identify interactive elements, understand the observe-then-act workflow.

### 3. android-interact

**Purpose:** Perform touch, gesture, and text input actions.

**Triggers:** "tap on", "click", "swipe", "type text", "press back", "scroll"

**Commands covered:**
- Tap via `adb shell input tap X Y`
- Swipe via `adb shell input swipe X1 Y1 X2 Y2 duration`
- Text input via ContentProvider keyboard/input (base64-encoded)
- Key events via ContentProvider keyboard/key
- Clear field, back, home, enter

**Guidance:** Coordinate calculation from bounds, swipe patterns for scrolling, text encoding, key code reference, observe→act→verify workflow.

### 4. android-apps

**Purpose:** App lifecycle management.

**Triggers:** "open app", "launch", "install APK", "list apps"

**Commands covered:**
- List packages via ContentProvider
- Launch app via `adb shell monkey` or `adb shell am start`
- Stop app via `adb shell am force-stop`
- Install APK via `adb install`

**Guidance:** Finding package names, common app packages, wait-after-launch patterns.

## Design Decisions

1. **ContentProvider over HTTP** — No port forwarding or auth token setup needed. Works immediately with USB or wireless ADB.
2. **No Python dependency** — All commands are pure ADB shell. Only requires `adb` on the host machine.
3. **Raw commands + smart guidance** — Skills document the commands and teach Claude how to compose them into workflows, rather than using wrapper scripts.
4. **Four focused skills** — Maps to natural usage patterns: setup once, observe first, then interact, manage apps separately.

## Key Reference

### ContentProvider Query Commands
| URI Path | Returns |
|----------|---------|
| `/ping` | Connection test |
| `/state_full` | Full UI tree + phone state + device context |
| `/state` | UI tree + phone state |
| `/a11y_tree` | Visible elements with indices |
| `/a11y_tree_full` | Complete element tree |
| `/phone_state` | Current activity, keyboard status |
| `/packages` | Installed launchable apps |
| `/version` | Portal app version |

### ContentProvider Insert Commands
| URI Path | Parameters | Action |
|----------|-----------|--------|
| `/keyboard/input` | `base64_text:s:`, `clear:b:` | Type text |
| `/keyboard/clear` | — | Clear focused field |
| `/keyboard/key` | `key_code:i:` | Send key event |
| `/overlay_offset` | `offset:i:` | Set overlay offset |
| `/overlay_visible` | `visible:b:` | Toggle overlay |

### Key Codes
| Key | Code |
|-----|------|
| Home | 3 |
| Back | 4 |
| Enter | 66 |
| Backspace | 67 |
| Tab | 61 |
| Escape | 111 |

## Helper Scripts Architecture

The `scripts/` directory contains Python helper scripts that simplify common operations. These are optional — all functionality is also available via raw ADB commands.

### Shared Utilities Module (`droidutils.py`)

Consolidates common functionality with improvements learned from the droidrun library:

| Feature | Function | Description |
|---------|----------|-------------|
| **ADB execution** | `run_adb()` | Run ADB commands with error handling |
| **Response parsing** | `parse_content_provider()` | Parse ContentProvider JSON responses |
| **Retry logic** | `query_tree_with_retry()` | Retry failed queries (3 attempts, 0.5s delay) |
| **Index lookup** | `build_index()`, `find_element_by_index()` | O(1) element lookup by index |
| **Text search** | `find_element()` | Recursive tree search by text |
| **Filtering** | `should_filter()` | Combines all filter checks |
| **Size filtering** | `is_too_small()` | Filter elements < 5px |
| **Visibility filtering** | `is_visible()` | Filter elements < 10% visible |
| **Keyboard filtering** | `is_keyboard_element()` | Filter Google/Samsung keyboard elements |
| **Clear point detection** | `find_clear_point()`, `get_tap_point()` | Quadrant subdivision to avoid overlaps |
| **Formatting** | `format_element()` | Format element for display |

### Script Reference

| Script | Purpose | Key Options |
|--------|---------|-------------|
| `droid-observe.py` | List UI elements | `--phone-state`, `--all`, `--no-filter-*` |
| `droid-tap.py` | Tap by text | `--exact`, `--avoid-overlap` |
| `droid-tap-index.py` | Tap by index | `--avoid-overlap` |
| `droid-type.py` | Type text | `--clear` |
| `droid-wait.py` | Wait for element | `--timeout`, `--exact` |

### Efficiency Improvements from droidrun

1. **Index-based lookup**: O(1) element access via `build_index()` dict instead of O(N) recursive search
2. **Smart filtering**: Reduces element count by 30-50% via size/visibility/keyboard filters
3. **Retry logic**: Handles flaky ADB connections with configurable retries
4. **Clear point detection**: Quadrant subdivision algorithm finds unblocked tap points for overlapping elements
5. **Shared utilities**: Single module eliminates code duplication across scripts
