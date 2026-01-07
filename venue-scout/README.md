# Venue Scout 🎵

Research agent for finding new and existing performance venues across the United States.

## Overview

Venue Scout automates the time-consuming task of discovering and tracking performance venues. It uses AI-powered web searches to find venues that match your act profiles, maintains a SQLite database of opportunities, and generates weekly reports to help you build a sustainable touring calendar.

### Key Features

- **Multi-Provider LLM Support** - Choose from Claude, OpenRouter, Ollama, or MCP for web searches
- **Web-Based Setup Wizard** - User-friendly configuration for any US state (no TOML editing required)
- **Automated Daily Searches** - AI-powered web searches tailored to your genres and regions
- **Intelligent Act Matching** - Automatically matches discovered venues to suitable acts
- **Exclusion System** - Track non-responsive or problematic venues
- **Weekly Reports** - Markdown reports with statistics and new opportunities
- **SQLite Database** - Local, portable venue tracking with full history
- **Geographic Prioritization** - Focus searches on high-value regions first

## Quick Start

### Recommended: Use Make Commands

```bash
# One-time setup (creates venv, installs dependencies, initializes database)
make setup

# Run the setup wizard (opens web browser)
make wizard

# Daily operations
make run-daily      # Complete daily workflow (search + process)
make weekly-report  # Generate weekly report

# Database operations
make list-acts      # View configured acts
make export         # Export venues to CSV

# View all commands
make help
```

### For Non-Technical Users: Setup Wizard

The interactive web-based setup wizard works for any US state and generates all configuration automatically:

```bash
# With Make
make wizard

# Or manually
pip install flask uszipcode
python setup_wizard.py
# Opens browser at http://localhost:5000
```

The wizard guides you through:
1. **Location** - Enter zip code, auto-discover nearby cities within radius
2. **Acts** - Create profiles with genres, fees, venue preferences
3. **Review** - Preview and save configuration, optionally initialize database

## Multi-Provider LLM Support

**NEW:** Venue Scout now supports multiple LLM providers for web searches!

### Provider Comparison

| Provider | Cost | Web Search | Setup | Privacy | Best For |
|----------|------|------------|-------|---------|----------|
| **Claude** | $$ API | Native | Easy | Cloud | Most reliable, recommended |
| **OpenRouter** | $ varies | Via Exa.ai | Easy | Cloud | Cost-effective, multi-model |
| **Ollama** | Free | Via MCP | Medium | Local | Privacy-focused, no API costs |
| **MCP** | Varies | Multiple | Advanced | Configurable | Flexibility, custom servers |

### Quick Setup by Provider

**Claude (Recommended):**
```bash
export ANTHROPIC_API_KEY='sk-ant-...'
python unified_search.py --daily --provider claude
```

**OpenRouter:**
```bash
export OPENROUTER_API_KEY='sk-or-...'
python unified_search.py --daily --provider openrouter
```

**Ollama (Local):**
```bash
ollama pull llama3.1:latest
ollama serve
python unified_search.py --daily --provider ollama
```

**MCP:**
```bash
npm install -g web-search-mcp
export ANTHROPIC_API_KEY='sk-ant-...'  # or other LLM key
python unified_search.py --daily --provider mcp
```

See [CLAUDE.md](CLAUDE.md) for detailed provider configuration and comparison.

## Configured Acts

| Act | Genre | Members | Fee Range |
|-----|-------|---------|-----------|
| Tree of Life Trio | Jazz/Soul/Funk | 3 | $500-2500 |
| CloudBurst | Jazz-Rock Fusion | 5 | $1500-7000 |
| Tillson Jazz Ensemble | Classic Jazz | 5 | $800-3500 |
| Colletti | Solo Looping Bass | 1 | $200-1200 |
| McGroovin | Irish Trad/Funk | 5 | $500-3500 |
| Nail, Thump and Flow | Prog Jazz | 4 | $1200-6000 |
| Pablo Shine Latin Jazz | Latin Jazz | 7 | $2000-9000 |
| Michael Colletti Solo | Acoustic | 1 | $150-600 |
| Tree of Life Band | Funk/Soul | 6 | $2000-8000 |

## Daily Workflow

### Using Make (Recommended)
```bash
make run-daily     # Runs unified_search.py + search_runner.py automatically
```

### Manual Commands

**1. Run Daily Search** (with configured provider)
```bash
python unified_search.py --daily --max-queries 15
```

**2. Process Results**
```bash
python search_runner.py --process data/search_results/daily_*.json
```

**3. Generate Weekly Report** (Sundays)
```bash
python venue_scout.py --weekly-report
```

## Command Reference

### Main Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `unified_search.py` | Multi-provider search (NEW) | **Recommended** |
| `claude_search.py` | Claude-only search | Deprecated |
| `venue_scout.py` | Database management & reports | Active |
| `search_runner.py` | Result processing | Active |
| `setup_wizard.py` | Web-based configuration | Active |

### Database Management

```bash
# Initialize database
python venue_scout.py --init-db

# View configured acts
python venue_scout.py --list-acts

# Manually add a venue
python venue_scout.py --add-venue "Venue Name" "City"

# Export all active venues
python venue_scout.py --export json
python venue_scout.py --export csv
```

### Venue Exclusions

Track non-responsive or problematic venues:

```bash
# Exclude a venue
python venue_scout.py --exclude "Bad Venue" "Kingston" \
    --exclude-reason no_response \
    --exclude-notes "No reply after 3 attempts"

# List excluded venues
python venue_scout.py --list-excluded

# Remove from exclusion list
python venue_scout.py --unexclude "Bad Venue" "Kingston"
```

**Exclusion Reasons:**
- `no_response` - Venue doesn't respond to inquiries
- `bad_experience` - Negative booking experience
- `closed` - Permanently closed
- `not_booking` - Not currently booking live music
- `wrong_fit` - Doesn't match any act profiles

You can also add exclusions directly in `config/venues.toml`:

```toml
[[excluded.venues]]
name = "Non Responsive Bar"
city = "Kingston"
reason = "no_response"
date_excluded = "2025-01-15"
notes = "No response after 3 follow-ups"
```

## Project Structure

```
venue-scout/
├── config/
│   └── venues.toml           # Acts, regions, exclusions, search config
├── data/
│   ├── venues.db             # SQLite database (venues, opportunities, history)
│   ├── queries_*.json        # Generated search queries
│   └── search_results/       # Daily search results
│       └── daily_*.json
├── reports/
│   └── weekly_*.md           # Generated weekly reports
├── logs/
│   └── daily_*.log           # Automation logs
├── providers/                # Multi-provider LLM integrations (NEW)
│   ├── __init__.py
│   ├── base.py               # Base provider interface
│   ├── claude_provider.py    # Claude/Anthropic
│   ├── openrouter_provider.py
│   ├── ollama_provider.py
│   ├── mcp_provider.py       # Model Context Protocol
│   └── factory.py            # Provider factory
├── static/                   # Setup wizard CSS/JS
├── templates/                # Setup wizard HTML
├── utils/                    # Helper utilities
├── venue_scout.py            # Main CLI (database, reports, management)
├── unified_search.py         # Multi-provider search script (NEW)
├── claude_search.py          # Legacy Claude-only search (deprecated)
├── search_runner.py          # Result processing and database updates
├── setup_wizard.py           # Web-based configuration wizard
├── run_daily.sh              # Cron script
├── Makefile                  # Automation commands
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── CLAUDE.md                 # Claude Code guide (detailed docs)
```

## Configuration

### Act Profiles (`config/venues.toml`)

```toml
[acts.my_act]
name = "My Band"
genres = ["rock", "indie", "alternative"]
min_capacity = 100
max_capacity = 500
ideal_capacity = 200
requires_stage = true
requires_sound_system = true
set_length_hours = 2
members = 4
venue_types = ["music venue", "bar with stage", "club"]
available_days = ["thursday", "friday", "saturday"]
min_fee = 500
max_fee = 2000
notes = "Full band with drums"
```

### Search Regions

```toml
[regions.hudson_valley]
name = "Hudson Valley"
counties = ["Ulster", "Dutchess", "Greene"]
cities = ["Kingston", "Woodstock", "New Paltz", "Rhinebeck"]
priority = 1  # Lower number = higher priority

[regions.capital_region]
name = "Capital Region"
counties = ["Albany", "Rensselaer"]
cities = ["Albany", "Troy", "Saratoga Springs"]
priority = 2
```

### Provider Configuration

```toml
[search_provider]
default_provider = "claude"  # or openrouter, ollama, mcp
fallback_providers = ["openrouter", "ollama"]  # automatic fallback

[search_provider.claude]
model = "claude-sonnet-4-20250514"
max_tokens = 2000

[search_provider.openrouter]
model = "openai/gpt-4o:online"  # :online enables web search
max_tokens = 2000

[search_provider.ollama]
model = "llama3.1:latest"
base_url = "http://localhost:11434"

[search_provider.mcp]
server_type = "websearch-mcp"  # or serpapi, brave
model = "claude-sonnet-4-20250514"
```

## Automation

### Cron Setup

**Using Make:**
```bash
make setup-cron
```

**Manual Setup:**
Add to crontab (`crontab -e`):
```cron
# Daily at 6am
0 6 * * * /path/to/venue-scout/run_daily.sh

# Weekly report on Sunday at 8am
0 8 * * 0 cd /path/to/venue-scout && python3 venue_scout.py --weekly-report
```

The `run_daily.sh` script automatically runs weekly reports on Sundays.

## Security

Venue Scout follows security best practices:

- **No Hardcoded Secrets** - All API keys via environment variables
- **SQL Injection Protection** - Parameterized queries throughout
- **Input Sanitization** - Command injection prevention
- **Secure Defaults** - .env files excluded from git

### Environment Variables

```bash
# Required for Claude provider
export ANTHROPIC_API_KEY='sk-ant-...'

# Required for OpenRouter provider
export OPENROUTER_API_KEY='sk-or-...'

# Optional for MCP with specific servers
export SERPAPI_API_KEY='your-key'
export BRAVE_API_KEY='your-key'
```

Store in `.env` file (excluded from git):
```bash
# .env file
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-...
```

## Dependencies

**Core:**
```bash
pip install anthropic      # For Claude provider
pip install openai         # For OpenRouter provider
pip install ollama         # For Ollama provider
pip install mcp            # For MCP provider
```

**Setup Wizard (Optional):**
```bash
pip install flask uszipcode
```

**All dependencies:**
```bash
pip install -r requirements.txt
```

## Migration from claude_search.py

The old `claude_search.py` still works but is deprecated:

```bash
# Old way (still works, shows deprecation warning)
python claude_search.py --daily

# New way (multi-provider support)
python unified_search.py --daily --provider claude

# Or use default provider from config
python unified_search.py --daily
```

## Troubleshooting

**Search returns no results:**
- Check API key is set correctly
- Verify provider is running (Ollama: `ollama serve`)
- Review search templates in `config/venues.toml`
- Check logs in `logs/daily_*.log`

**Database errors:**
- Reinitialize: `python venue_scout.py --init-db`
- Check file permissions on `data/venues.db`

**Provider not working:**
- Claude: Verify `ANTHROPIC_API_KEY` is valid
- OpenRouter: Ensure model name includes `:online` suffix
- Ollama: Confirm service is running and model is pulled
- MCP: Check MCP server is installed globally (`npm list -g`)

## CLI Reference

| Command | Description |
|---------|-------------|
| `--init-db` | Initialize database schema |
| `--daily` | Run daily search (deprecated, use unified_search.py) |
| `--weekly-report` | Generate weekly markdown report |
| `--list-acts` | Show all configured acts |
| `--add-venue NAME CITY` | Manually add a venue |
| `--export [json\|csv]` | Export active venues |
| `--exclude NAME CITY` | Exclude a venue |
| `--exclude-reason REASON` | Set exclusion reason |
| `--exclude-notes NOTES` | Add exclusion notes |
| `--unexclude NAME CITY` | Remove from exclusion list |
| `--list-excluded` | List all excluded venues |

## Documentation

- [CLAUDE.md](CLAUDE.md) - Comprehensive guide for Claude Code users (includes detailed provider docs)
- [Root README](../README.md) - Overview of both venue-scout and festival-submit
- [Makefile](Makefile) - Run `make help` for all automation commands

## Support

For issues or questions:
- Review [CLAUDE.md](CLAUDE.md) for detailed documentation
- Check logs in `logs/` directory
- Open an issue on GitHub

## License

Private - All rights reserved.
