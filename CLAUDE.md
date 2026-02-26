# Claude Code Configuration for Skills Marketplace

## Project Overview

This is a Claude Code plugin marketplace containing custom skills and plugins.

## Project Structure

```
skills/
├── .claude-plugin/
│   └── marketplace.json   # Plugin registry (update when adding plugins)
├── droidrun-portal/       # Android device control plugin
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── scripts/
│   ├── skills/
│   └── README.md
└── <future-plugins>/
```

## Adding a New Plugin

1. Create a new directory: `mkdir new-plugin`
2. Add plugin metadata: `new-plugin/.claude-plugin/plugin.json`
3. Add skills: `new-plugin/skills/<skill-name>/SKILL.md`
4. Register in marketplace: Update `.claude-plugin/marketplace.json`
5. Update `README.md` with the new plugin

### Plugin Structure Template

```
new-plugin/
├── .claude-plugin/
│   └── plugin.json        # Required: name, version, description
├── scripts/               # Optional: helper scripts
├── skills/
│   └── skill-name/
│       └── SKILL.md       # Required: YAML frontmatter + instructions
├── docs/                  # Optional: design docs
├── CLAUDE.md              # Recommended: plugin-specific instructions
└── README.md              # Recommended: plugin documentation
```

### plugin.json Template

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "What this plugin does",
  "author": { "name": "Your Name" },
  "license": "MIT",
  "keywords": ["relevant", "keywords"]
}
```

### SKILL.md Template

```markdown
---
name: skill-name
description: When to use this skill (shown in skill discovery)
---

# Skill Title

Instructions for Claude when this skill is invoked.
```

## Marketplace Registration

When adding a plugin, update `.claude-plugin/marketplace.json`:

```json
{
  "plugins": [
    // ... existing plugins
    {
      "name": "new-plugin",
      "description": "What it does",
      "version": "1.0.0",
      "source": "./new-plugin"
    }
  ]
}
```

## Development Guidelines

- Each plugin should be self-contained in its own directory
- Use conventional commits: `feat(plugin-name):`, `fix(plugin-name):`
- Keep plugin READMEs updated with installation and usage
- Commit often, push when features are complete

## Installation (for users)

```bash
/plugin marketplace add /path/to/skills
/plugin install <plugin-name>@skills
```
