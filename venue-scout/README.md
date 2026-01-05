# Venue Scout 🎵

Research agent for finding new and existing performance venues across the United States.

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

## Quick Start

### Recommended: Use Make Commands

The easiest way to use venue-scout is with the included Makefile:

```bash
# One-time setup (creates venv, installs dependencies, initializes database)
make setup

# Run the setup wizard
make wizard

# Daily operations
make run-daily      # Complete daily workflow (search + process)
make weekly-report  # Generate weekly report

# View all commands
make help
```

### For Non-Technical Users: Setup Wizard

Use the interactive web-based setup wizard to configure venue-scout (works for any US state):

```bash
# With Make
make wizard

# Or manually
pip install flask uszipcode
python setup_wizard.py
# Opens browser at http://localhost:5000
```

The wizard will guide you through:
1. Entering your zip code and selecting nearby cities
2. Creating act profiles with genres, fees, and venue preferences
3. Generating configuration automatically

### Manual Commands (without Make)

```bash
# Initialize database
python venue_scout.py --init-db

# View configured acts
python venue_scout.py --list-acts

# Run daily search
python venue_scout.py --daily

# Generate weekly report
python venue_scout.py --weekly-report

# Export venues
python venue_scout.py --export json
```

## Dependencies

```bash
# Core dependencies
pip install anthropic  # For Claude API searches

# Setup wizard dependencies (optional, only if using wizard)
pip install flask uszipcode
```

## Exclude Non-Responsive Venues

```bash
# Exclude a venue (reasons: no_response, bad_experience, closed, not_booking, wrong_fit)
python venue_scout.py --exclude "Bad Venue Name" "Kingston" --exclude-reason no_response --exclude-notes "No reply after 3 attempts"

# List excluded venues
python venue_scout.py --list-excluded

# Remove from exclusion list
python venue_scout.py --unexclude "Bad Venue Name" "Kingston"
```

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
│   └── venues.toml        # Acts, regions, exclusions, search config
├── data/
│   └── venues.db          # SQLite database
├── reports/
│   └── weekly_*.md        # Weekly reports
├── logs/
├── venue_scout.py         # Main CLI
├── search_runner.py       # Search processing
├── claude_search.py       # Claude API integration
└── run_daily.sh           # Cron script
```

## Configuration

### Act Profiles

```toml
[acts.my_act]
name = "My Band"
genres = ["rock", "indie"]
min_capacity = 100
max_capacity = 500
ideal_capacity = 200
requires_stage = true
venue_types = ["music venue", "bar", "club"]
available_days = ["friday", "saturday"]
min_fee = 500
max_fee = 2000
```

### Search Regions

```toml
[regions.hudson_valley]
name = "Hudson Valley"
counties = ["Ulster", "Dutchess"]
cities = ["Kingston", "Woodstock", "New Paltz"]
priority = 1  # Lower = higher priority
```

## Automation

### Cron Setup

```bash
crontab -e
# Add:
0 6 * * * /path/to/venue-scout/run_daily.sh
```

### Claude API Integration

```bash
export ANTHROPIC_API_KEY='sk-ant-...'
python claude_search.py --daily --max-queries 15
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `--init-db` | Initialize database |
| `--daily` | Run daily search |
| `--weekly-report` | Generate weekly report |
| `--list-acts` | Show configured acts |
| `--add-venue NAME CITY` | Add venue manually |
| `--export [json\|csv]` | Export venues |
| `--exclude NAME CITY` | Exclude venue |
| `--exclude-reason REASON` | Reason for exclusion |
| `--exclude-notes NOTES` | Notes for exclusion |
| `--unexclude NAME CITY` | Remove exclusion |
| `--list-excluded` | List excluded venues |

## Exclusion Reasons

- `no_response` - Venue doesn't respond to inquiries
- `bad_experience` - Had a negative booking experience
- `closed` - Venue is permanently closed
- `not_booking` - Venue not currently booking live music
- `wrong_fit` - Venue doesn't fit any act profiles
