# Venue Research Agent

A comprehensive suite of research and automation tools for musicians seeking performance venues and festival opportunities.

## Overview

This repository contains two complementary systems for musicians:

- **Venue Scout** - Research agent for discovering and tracking performance venues
- **Festival Submit** - Automated festival submission management system

Both systems use intelligent agents, LLM integration, and automation to streamline the business side of being a working musician.

## Projects

### 🎵 Venue Scout

Research agent for finding new and existing performance venues across the United States.

**Key Features:**
- Multi-provider LLM support (Claude, OpenRouter, Ollama, MCP)
- Web-based setup wizard for any US state
- Automated daily venue searches with web scraping
- SQLite database for venue tracking
- Exclusion system for non-responsive venues
- Weekly reporting and analytics
- Multiple act profile support with intelligent matching

**Quick Start:**
```bash
cd venue-scout
make setup          # One-time setup
make wizard         # Interactive configuration
make run-daily      # Daily search workflow
```

See [venue-scout/README.md](venue-scout/README.md) for full documentation.

### 🎪 Festival Submit

Automated festival submission system for managing multiple musical acts and their festival applications.

**Key Features:**
- Multi-act and multi-festival management
- Geographic tiering (local/regional/national/international)
- Automated deadline tracking and notifications
- Email template system with variable substitution
- Submission status tracking and reporting
- Calendar view of deadlines and opportunities
- Desktop and email notifications

**Quick Start:**
```bash
cd festival-submit
make setup          # One-time setup
make acts           # View configured acts
make festivals      # Browse festival database
make match ACT='your_act_id'  # Find matching festivals
```

See [festival-submit/README.md](festival-submit/README.md) for full documentation.

## Installation

### Prerequisites
- Python 3.11+
- Make (optional but recommended)
- API keys for LLM providers (see provider-specific docs)

### Quick Setup

**Using Make (Recommended):**
```bash
# Setup both projects
make setup-all

# Or setup individually
cd venue-scout && make setup
cd festival-submit && make setup
```

**Manual Installation:**
```bash
# Clone repository
git clone https://github.com/michaelcolletti/venue-research-agent.git
cd venue-research-agent

# Setup venue-scout
cd venue-scout
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python venue_scout.py --init-db

# Setup festival-submit
cd ../festival-submit
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python festival_submit.py init
```

## Project Structure

```
venue-research-agent/
├── venue-scout/              # Venue discovery and research
│   ├── config/               # Act profiles, regions, search templates
│   ├── data/                 # SQLite database and search results
│   ├── providers/            # Multi-provider LLM integrations
│   ├── reports/              # Weekly analysis reports
│   ├── static/               # Setup wizard assets
│   ├── templates/            # Setup wizard HTML
│   ├── utils/                # Helper utilities
│   ├── venue_scout.py        # Main CLI
│   ├── unified_search.py     # Multi-provider search (NEW)
│   ├── claude_search.py      # Legacy Claude-only search
│   ├── search_runner.py      # Result processing
│   ├── setup_wizard.py       # Web-based configuration
│   └── Makefile              # Automation commands
│
├── festival-submit/          # Festival submission management
│   ├── config/               # Acts, festivals, templates
│   ├── data/                 # Submissions database
│   ├── reports/              # Generated reports
│   ├── logs/                 # Automation logs
│   ├── festival_submit.py    # Main CLI
│   ├── scheduler.py          # Automation scheduler
│   ├── notifications.py      # Alert system
│   └── Makefile              # Automation commands
│
├── Makefile                  # Root-level project coordination
├── README.md                 # This file
└── requirements.txt          # Shared dependencies
```

## Workflow Integration

These tools work together in a musician's business workflow:

```
1. Venue Scout discovers venues
   ↓
2. Venues added to database with contact info
   ↓
3. Musician books shows and builds relationships
   ↓
4. Festival Submit manages festival applications
   ↓
5. Deadline tracking and follow-ups automated
   ↓
6. Weekly reports show progress and opportunities
```

## Security

Both projects follow security best practices:

- No hardcoded API keys or credentials
- Environment variables for sensitive data
- Parameterized SQL queries (SQL injection protection)
- Input sanitization (command injection protection)
- .env files excluded from version control
- SMTP passwords should use app-specific passwords

See individual project READMEs for security configuration details.

## Automation

### Venue Scout Automation
```bash
# Add to crontab
0 6 * * * /path/to/venue-scout/run_daily.sh
```

### Festival Submit Automation
```bash
# Add to crontab
0 9 * * * /path/to/festival-submit/run_automation.sh
```

### Combined Automation
```bash
# Using root Makefile
make daily-all      # Run all daily tasks
make weekly-all     # Run all weekly tasks
```

## Documentation

- [Venue Scout Documentation](venue-scout/README.md)
- [Venue Scout Claude Code Guide](venue-scout/CLAUDE.md)
- [Festival Submit Documentation](festival-submit/README.md)
- [Root Makefile Reference](Makefile) - Run `make help` for commands

## Contributing

This is a private repository. Security contributions and bug reports welcome via issues.

## License

Private - All rights reserved.

## Support

For issues or questions:
- Check project-specific README files
- Review CLAUDE.md for AI agent guidance
- Open an issue on GitHub
