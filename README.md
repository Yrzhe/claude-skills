# yrzhe Claude Code Skills

A collection of powerful Claude Code skills and plugins by [@yrzhe](https://x.com/yrzhe_top).

## Installation

### Option 1: Via Plugin Marketplace

Add this marketplace to your Claude Code:

```bash
/plugin marketplace add yrzhe/claude-skills
```

Then install any plugin you want:

```bash
/plugin install intelligent-web-scraper@yrzhe-skills
```

### Option 2: Manual Installation

If the plugin command doesn't work, you can manually copy the skill files:

1. Clone or download this repository
2. Copy the skill folder to your Claude skills directory:

**macOS / Linux:**
```bash
cp -r plugins/intelligent-web-scraper/skills/intelligent-web-scraper ~/.claude/skills/
```

**Windows (PowerShell):**
```powershell
Copy-Item -Recurse plugins\intelligent-web-scraper\skills\intelligent-web-scraper $env:USERPROFILE\.claude\skills\
```

3. Restart Claude Code to load the new skill

## Available Plugins

### intelligent-web-scraper

Self-learning intelligent web scraper agent that automatically analyzes page structure, handles pagination, anti-blocking, and discovers article series. No user configuration needed - AI decides everything.

**Features:**
- Intelligent page analysis and data extraction
- Smart pagination handling (page numbers, infinite scroll, load more)
- Detail link following for complete data
- Anti-blocking with adaptive delays
- Series/chapter discovery
- Self-learning system that remembers successful patterns
- Resume capability for interrupted scrapes
- Concurrent scraping with rate limiting
- Local browser support (preserve login sessions)

**Usage:**
```
/intelligent-web-scraper
```

Then provide a URL to scrape and let the AI handle everything.

## Contributing

Feel free to open issues or submit pull requests to improve these skills.

## License

MIT License - see individual plugins for details.

## Author

**yrzhe** - [@yrzhe_top](https://x.com/yrzhe_top)
