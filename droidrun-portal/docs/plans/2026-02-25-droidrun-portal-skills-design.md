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
