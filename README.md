# Skills Marketplace

A collection of custom Claude Code plugins and skills.

## Installation

### Add this marketplace to Claude Code

```bash
# From a local path
/plugin marketplace add /path/to/skills

# From a Git repository
/plugin marketplace add https://github.com/user/skills.git
```

### Install a plugin

```bash
# Interactive
/plugin
# Navigate to Discover tab → Select plugin → Install

# Command line
/plugin install <plugin-name>@skills
```

## Available Plugins

| Plugin | Description | Skills |
|--------|-------------|--------|
| [droidrun-portal](./droidrun-portal/) | Control Android devices via ADB and droidrun-portal | `android-setup`, `android-observe`, `android-interact`, `android-apps` |

## Plugin Details

### droidrun-portal

Control Android devices using [droidrun-portal](https://github.com/droidrun/droidrun-portal)'s ContentProvider interface.

**Skills included:**
- `android-setup` — Device connection and portal installation
- `android-observe` — Read UI elements and device state
- `android-interact` — Tap, swipe, type, and navigate
- `android-apps` — Launch, stop, and manage apps

**Requirements:**
- ADB (Android SDK Platform Tools)
- Android device with USB debugging enabled
- droidrun-portal APK installed on device

[Full documentation →](./droidrun-portal/README.md)

## Creating a New Plugin

1. Create plugin directory with required structure:
   ```
   my-plugin/
   ├── .claude-plugin/
   │   └── plugin.json
   └── skills/
       └── my-skill/
           └── SKILL.md
   ```

2. Register in `.claude-plugin/marketplace.json`:
   ```json
   {
     "name": "my-plugin",
     "description": "What it does",
     "version": "1.0.0",
     "source": "./my-plugin"
   }
   ```

3. Update this README with your plugin

See [CLAUDE.md](./CLAUDE.md) for detailed plugin development guidelines.

## License

MIT
