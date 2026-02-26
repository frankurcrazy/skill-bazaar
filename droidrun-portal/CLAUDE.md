# Claude Code Configuration for droidrun-portal

## Project Overview

This is a Claude Code skills plugin for controlling Android devices via droidrun-portal's ADB ContentProvider interface.

## Project Structure

```
droidrun-portal/
├── scripts/           # Python helper scripts
│   ├── droidutils.py  # Shared utilities module (imported by other scripts)
│   └── droid-*.py     # CLI scripts (observe, tap, tap-index, type, wait)
├── skills/            # Claude Code skill definitions
│   └── android-*/     # Each skill has a SKILL.md
└── docs/plans/        # Design documents
```

## Development Guidelines

### Scripts

- **Naming convention**: CLI scripts use hyphens (`droid-tap.py`), import modules use no separator (`droidutils.py`)
- **Shared code**: All common functionality goes in `droidutils.py` — never duplicate code across scripts
- **Error handling**: Use `run_adb(check=True)` for required commands, `check=False` for optional/retry scenarios
- **Filtering**: Default filtering removes noise (layout containers), tiny elements (<5px), keyboard elements, and off-screen elements

### Skills

- Skills are in `skills/<name>/SKILL.md` with YAML frontmatter (`name`, `description`)
- Document both raw ADB commands AND helper scripts
- Follow observe→act→verify workflow pattern

### Design Documents

- Keep `docs/plans/` updated when making architectural changes
- Design doc covers architecture, helper scripts, and ContentProvider API reference

## Key APIs

### ContentProvider URIs

| URI | Method | Purpose |
|-----|--------|---------|
| `/a11y_tree` | query | Get UI elements with indices |
| `/phone_state` | query | Get current app, keyboard status |
| `/state_full` | query | Combined tree + state + device info |
| `/keyboard/input` | insert | Type text (base64-encoded) |
| `/keyboard/key` | insert | Send key event |

### Helper Script Usage

```bash
# Observe
python3 scripts/droid-observe.py --phone-state

# Interact
python3 scripts/droid-tap.py "Submit"
python3 scripts/droid-tap-index.py 5
python3 scripts/droid-type.py "Hello" --clear
python3 scripts/droid-wait.py "Loading" --timeout 30
```

## Testing

No automated tests yet. Manual testing:
1. Connect Android device with droidrun-portal installed
2. Run `python3 scripts/droid-observe.py` to verify connection
3. Test tap/type/wait scripts against a sample app

## Maintenance Checklist

When adding new skills or scripts, update these files:

- [ ] `README.md` — Add to "Available Skills" table and/or "Helper Scripts" section
- [ ] `docs/plans/*-design.md` — Update architecture sections if structure changes
- [ ] `CLAUDE.md` — Update if new APIs or conventions are introduced
