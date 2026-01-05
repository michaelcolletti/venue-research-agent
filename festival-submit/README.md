# Festival Submit

Automated festival submission system for managing multiple musical acts and their festival applications.

## Configured Acts

| Act | Genre | Members |
|-----|-------|---------|
| **Tree of Life Trio** | Jazz/Soul/Funk | 3 |
| **CloudBurst** | Jazz-Rock Fusion | 5 |
| **Tillson Jazz Ensemble** | Classic Jazz/Bebop | 5 |
| **Colletti** | Solo Looping Bass | 1 |
| **McGroovin** | Irish Trad/Funk Fusion | 5 |
| **Nail, Thump and Flow** | Prog/Jazz Fusion | 4 |
| **Pablo Shine Latin Jazz Band** | Latin Jazz/Afro-Cuban | 7 |
| **Tree of Life Band** | Funk/Soul (Full) | 6 |
| **Michael Colletti Solo** | Acoustic/Singer-Songwriter | 1 |

## Quick Start

### Recommended: Use Make Commands

The easiest way to use festival-submit is with the included Makefile:

```bash
# One-time setup (creates venv, installs dependencies, initializes database)
make setup

# List all acts and festivals
make acts
make festivals

# Find matching festivals for an act
make match ACT='cloudburst'

# Create a submission
make submit ACT='tree_of_life_trio' FEST='regional.saratoga_jazz'

# Check submission status
make status

# Generate reports
make report-status
make report-opps ACT='pablo_shine'
make calendar

# View all commands
make help
```

### Manual Commands (without Make)

```bash
# Initialize database
python3 festival_submit.py init

# List all acts
python3 festival_submit.py acts

# List festivals
python3 festival_submit.py festivals

# Find matching festivals for an act
python3 festival_submit.py match --act cloudburst

# Create a submission
python3 festival_submit.py submit --act tree_of_life_trio --festival regional.saratoga_jazz

# Check submission status
python3 festival_submit.py status

# Generate reports
python3 festival_submit.py report --type status
python3 festival_submit.py report --type opportunities --act pablo_shine
python3 festival_submit.py calendar --months 12

# Render a submission template
python3 festival_submit.py render --template festival_submission_jazz \
    --act tillson_jazz_ensemble --festival national.rochester_jazz
```

## Automation

### Daily/Weekly Automation with Make

```bash
# Run all automation tasks
make automation

# Run daily tasks only
make daily

# Run weekly tasks (reports)
make weekly

# Check upcoming deadlines
make check-deadlines

# Setup cron automation
make setup-cron
```

### Manual Automation Commands

```bash
# Run all automation tasks
python3 scheduler.py --all

# Run daily tasks only
python3 scheduler.py --daily

# Run weekly tasks (reports)
python3 scheduler.py --weekly

# Check deadlines and send notifications
python3 notifications.py --check

# Send email digest (requires SMTP config)
python3 notifications.py --digest

# Test desktop notification
python3 notifications.py --test
```

### Cron Setup

Use Make to setup cron automation:

```bash
make setup-cron
```

Or manually add to crontab (`crontab -e`):

```cron
# Daily at 9am
0 9 * * * /path/to/festival-submit/run_automation.sh

# Weekly digest on Monday at 8am
0 8 * * 1 /path/to/festival-submit/run_automation.sh
```

### Email Configuration

Set environment variables for email notifications:

```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASS="your-app-password"
export EMAIL_TO="notifications@example.com"
```

## Configuration

### Acts (`config/acts.toml`)

Each act includes:
- Basic info (name, genres, members)
- Fee structures by tier (local/regional/national/international)
- Travel requirements
- Press assets (EPK, social media, photos)
- Festival preferences

### Festivals (`config/festivals.toml`)

Organized by geographic tier:
- **Local** (0-75 miles)
- **Regional** (75-250 miles)
- **National** (250-2000 miles)
- **International** (2000+ miles)

### Templates (`config/templates.toml`)

Pre-built templates for:
- Standard festival submissions
- Jazz festival submissions
- Irish/Celtic festival submissions
- Latin jazz submissions
- Fusion/prog submissions
- Follow-up emails

## Directory Structure

```
festival-submit/
├── config/
│   ├── acts.toml          # Act configurations
│   ├── festivals.toml     # Festival database
│   └── templates.toml     # Email templates
├── data/
│   └── submissions.db     # SQLite database
├── logs/                  # Automation logs
├── reports/               # Generated reports
├── exports/               # Data exports
├── submissions/           # Generated submissions
├── festival_submit.py     # Main CLI
├── scheduler.py           # Automation scheduler
├── notifications.py       # Notification system
├── run_automation.sh      # Shell wrapper
└── requirements.txt
```

## Commands Reference

| Command | Description |
|---------|-------------|
| `init` | Initialize database |
| `acts` | List all configured acts |
| `festivals` | List all festivals |
| `match --act ID` | Find matching festivals |
| `submit --act ID --festival ID` | Create submission |
| `status [--act ID]` | Show submission status |
| `report --type TYPE [--act ID]` | Generate reports |
| `calendar [--months N]` | Generate submission calendar |
| `templates` | List available templates |
| `render --template ID --act ID --festival ID` | Render template |

## License

Private - All rights reserved.
