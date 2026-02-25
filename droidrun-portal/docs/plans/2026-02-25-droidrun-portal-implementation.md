# Droidrun Portal Skills Plugin — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a Claude Code plugin with four skills that let Claude directly control Android devices via droidrun-portal's ADB ContentProvider interface, without the droidrun Python framework.

**Architecture:** Plugin with four SKILL.md files (android-setup, android-observe, android-interact, android-apps), each documenting ADB shell commands and smart workflow guidance. No scripts or Python dependencies — pure ADB commands.

**Tech Stack:** Claude Code plugin format (SKILL.md with YAML frontmatter), ADB shell commands, droidrun-portal ContentProvider API.

---

### Task 1: Create Plugin Scaffold

**Files:**
- Create: `droidrun-portal/.claude-plugin/plugin.json`
- Create: `droidrun-portal/.claude-plugin/marketplace.json`

**Step 1: Create plugin.json**

```json
{
  "name": "droidrun-portal",
  "version": "1.0.0",
  "description": "Control Android devices via droidrun-portal using ADB commands",
  "author": {
    "name": "Frank"
  },
  "homepage": "https://github.com/droidrun/droidrun-portal",
  "license": "MIT",
  "keywords": ["android", "mobile", "automation", "adb", "droidrun"]
}
```

**Step 2: Create marketplace.json**

```json
{
  "name": "droidrun-portal",
  "description": "Android device control skills using droidrun-portal",
  "owner": { "name": "Frank" },
  "plugins": [
    {
      "name": "droidrun-portal",
      "description": "Control Android devices via droidrun-portal ADB commands",
      "version": "1.0.0",
      "source": "./",
      "author": { "name": "Frank" }
    }
  ]
}
```

**Step 3: Create skill directories**

```bash
mkdir -p droidrun-portal/skills/{android-setup,android-observe,android-interact,android-apps}
```

**Step 4: Commit**

```bash
git add droidrun-portal/.claude-plugin/
git commit -m "feat: scaffold droidrun-portal plugin structure"
```

---

### Task 2: Write android-setup Skill

**Files:**
- Create: `droidrun-portal/skills/android-setup/SKILL.md`

**Step 1: Write SKILL.md**

The skill covers:
- Prerequisites (ADB installed, USB debugging enabled)
- Portal APK installation from GitHub releases
- Enabling accessibility service via ADB
- Connection verification with ping
- Overlay configuration
- Wireless ADB setup
- Troubleshooting

Key commands to document:
```bash
# Install portal APK
adb install droidrun-portal.apk

# Enable accessibility service
adb shell settings put secure enabled_accessibility_services com.droidrun.portal/.service.DroidrunAccessibilityService

# Verify connection
adb shell content query --uri content://com.droidrun.portal/ping

# Check version
adb shell content query --uri content://com.droidrun.portal/version

# Configure overlay
adb shell content insert --uri content://com.droidrun.portal/overlay_visible --bind visible:b:true
adb shell content insert --uri content://com.droidrun.portal/overlay_offset --bind offset:i:0
```

**Step 2: Commit**

```bash
git add droidrun-portal/skills/android-setup/
git commit -m "feat: add android-setup skill for device connection and portal installation"
```

---

### Task 3: Write android-observe Skill

**Files:**
- Create: `droidrun-portal/skills/android-observe/SKILL.md`

**Step 1: Write SKILL.md**

The skill covers all observation/query commands and teaches how to parse responses:

Query commands:
```bash
# Full state (recommended starting point)
adb shell content query --uri content://com.droidrun.portal/state_full

# Combined tree + phone state
adb shell content query --uri content://com.droidrun.portal/state

# Visible elements with overlay indices
adb shell content query --uri content://com.droidrun.portal/a11y_tree

# Complete accessibility tree
adb shell content query --uri content://com.droidrun.portal/a11y_tree_full

# Phone state only (current app, keyboard status)
adb shell content query --uri content://com.droidrun.portal/phone_state

# Screenshot
adb exec-out screencap -p > /tmp/android-screenshot.png
```

Smart guidance sections:
- How to parse JSON from ContentProvider output (strip `Row: 0 result=` prefix)
- How to find elements by text content, className, or clickable status
- How to extract bounds `[left,top][right,bottom]` and calculate center coordinates
- The observe→identify→interact workflow
- When to use `state_full` vs `a11y_tree` vs `phone_state`

**Step 2: Commit**

```bash
git add droidrun-portal/skills/android-observe/
git commit -m "feat: add android-observe skill for reading device state and UI"
```

---

### Task 4: Write android-interact Skill

**Files:**
- Create: `droidrun-portal/skills/android-interact/SKILL.md`

**Step 1: Write SKILL.md**

The skill covers all input/action commands:

Touch and gesture commands:
```bash
# Tap at coordinates
adb shell input tap X Y

# Swipe (scroll, drag)
adb shell input swipe X1 Y1 X2 Y2 DURATION_MS

# Long press (swipe with same start/end)
adb shell input swipe X Y X Y 1000
```

Text input (via ContentProvider for Unicode support):
```bash
# Type text (base64-encoded)
adb shell content insert --uri content://com.droidrun.portal/keyboard/input \
  --bind base64_text:s:$(echo -n "Hello" | base64) --bind clear:b:false

# Clear focused field
adb shell content insert --uri content://com.droidrun.portal/keyboard/clear

# Send key event
adb shell content insert --uri content://com.droidrun.portal/keyboard/key \
  --bind key_code:i:66
```

Navigation:
```bash
# Back button
adb shell input keyevent 4

# Home button
adb shell input keyevent 3
```

Smart guidance sections:
- Calculating tap coordinates from element bounds: `center_x = (left+right)/2`
- Common swipe patterns: scroll down `swipe 540 1500 540 500 300`, scroll up reverse
- Text encoding workflow for Unicode/special characters
- Key code reference table
- The full observe→act→verify workflow
- Error recovery patterns

**Step 2: Commit**

```bash
git add droidrun-portal/skills/android-interact/
git commit -m "feat: add android-interact skill for touch, gesture, and text input"
```

---

### Task 5: Write android-apps Skill

**Files:**
- Create: `droidrun-portal/skills/android-apps/SKILL.md`

**Step 1: Write SKILL.md**

The skill covers app lifecycle management:

```bash
# List installed launchable apps
adb shell content query --uri content://com.droidrun.portal/packages

# Launch app by package name
adb shell monkey -p com.example.app -c android.intent.category.LAUNCHER 1

# Alternative launch with specific activity
adb shell am start -n com.example.app/.MainActivity

# Stop app
adb shell am force-stop com.example.app

# Install APK
adb install /path/to/app.apk

# Install with permissions auto-granted
adb install -g /path/to/app.apk
```

Smart guidance sections:
- How to find package names from the packages list
- Common package names (com.android.settings, com.android.chrome, etc.)
- Wait-after-launch pattern: launch → sleep 2 → get_state
- Handling "app not found" errors

**Step 2: Commit**

```bash
git add droidrun-portal/skills/android-apps/
git commit -m "feat: add android-apps skill for app lifecycle management"
```

---

### Task 6: Verify Plugin Structure and Test

**Step 1: Verify all files exist**

```bash
find droidrun-portal -type f | sort
```

Expected:
```
droidrun-portal/.claude-plugin/marketplace.json
droidrun-portal/.claude-plugin/plugin.json
droidrun-portal/docs/plans/2026-02-25-droidrun-portal-implementation.md
droidrun-portal/docs/plans/2026-02-25-droidrun-portal-skills-design.md
droidrun-portal/skills/android-apps/SKILL.md
droidrun-portal/skills/android-interact/SKILL.md
droidrun-portal/skills/android-observe/SKILL.md
droidrun-portal/skills/android-setup/SKILL.md
```

**Step 2: Verify YAML frontmatter in each SKILL.md**

Check that each has valid `name` and `description` fields.

**Step 3: Final commit**

```bash
git add -A droidrun-portal/
git commit -m "feat: complete droidrun-portal plugin with four Android control skills"
```
