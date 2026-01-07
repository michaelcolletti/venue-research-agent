# Festival Submit 🎪

Automated festival submission system for managing multiple musical acts and their festival applications.

## Overview

Festival Submit streamlines the complex process of submitting to music festivals. It manages multiple act profiles, tracks deadlines, generates customized submission materials from templates, and sends automated reminders. Focus on making music while the system handles the business logistics.

### Key Features

- **Multi-Act Management** - Configure unlimited acts with unique profiles, fees, and press materials
- **Geographic Tiering** - Festivals organized by distance (local/regional/national/international)
- **Template System** - Pre-built email templates with variable substitution
- **Deadline Tracking** - Automated notifications at 30, 14, 7, 3, and 1 days before deadlines
- **Status Tracking** - Monitor submissions from draft to acceptance/rejection
- **Calendar View** - Visualize all deadlines and opportunities
- **Email Integration** - SMTP support for automated notifications and digests
- **Desktop Notifications** - macOS native notifications for urgent deadlines
- **Reports & Analytics** - Weekly digests and act-specific opportunity reports

## Quick Start

### Recommended: Use Make Commands

```bash
# One-time setup (creates venv, installs dependencies, initializes database)
make setup

# View configured acts and festivals
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
python festival_submit.py init

# List all acts
python festival_submit.py acts

# List festivals
python festival_submit.py festivals

# Find matching festivals for an act
python festival_submit.py match --act cloudburst

# Create a submission
python festival_submit.py submit --act tree_of_life_trio --festival regional.saratoga_jazz

# Check submission status
python festival_submit.py status

# Generate reports
python festival_submit.py report --type status
python festival_submit.py report --type opportunities --act pablo_shine
python festival_submit.py calendar --months 12

# Render a submission template
python festival_submit.py render --template festival_submission_jazz \
    --act tillson_jazz_ensemble --festival national.rochester_jazz
```

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

Each act includes:
- Basic info (name, genres, members)
- Fee structures by tier (local/regional/national/international)
- Travel requirements (van_needed, backline_needed)
- Press assets (EPK URL, social media, photos, videos)
- Festival preferences (preferred_slot_time, preferred_stage_size)

## Configuration

### Acts (`config/acts.toml`)

```toml
[tree_of_life_trio]
name = "Tree of Life Trio"
genres = ["jazz", "soul", "funk"]
members = 3
description = "Jazz trio featuring piano, bass, and drums"

[tree_of_life_trio.fees]
local = 500
regional = 1000
national = 1500
international = 2500

[tree_of_life_trio.press]
epk_url = "https://example.com/epk"
website = "https://treeoflifetrio.com"
facebook = "https://facebook.com/treeoflifetrio"
instagram = "@treeoflifetrio"
spotify = "https://open.spotify.com/artist/..."
bandcamp = "https://treeoflifetrio.bandcamp.com"
```

### Festivals (`config/festivals.toml`)

Organized by geographic tier:

```toml
[local.kingston_jazz_festival]
name = "Kingston Jazz Festival"
location = "Kingston, NY"
distance_miles = 15
deadline = "2025-03-15"
notification_email = "submissions@kingstonjazz.org"
website = "https://kingstonjazz.org"
submission_fee = 0
genres = ["jazz", "blues", "soul"]
notes = "Family-friendly outdoor festival"
```

**Tiers:**
- **Local** (0-75 miles) - Minimal travel, lower fees
- **Regional** (75-250 miles) - Day trip or overnight
- **National** (250-2000 miles) - Multi-day travel, higher fees
- **International** (2000+ miles) - International travel, highest fees

### Templates (`config/templates.toml`)

Pre-built templates with variable substitution:

```toml
[festival_submission_jazz]
name = "Standard Jazz Festival Submission"
subject = "{act_name} - {festival_name} Submission"
body = """
Dear {festival_name} Selection Committee,

We are writing to submit {act_name} for consideration...

Genre: {genres}
Members: {members}
EPK: {epk_url}

Best regards,
{contact_name}
"""
variables = ["act_name", "festival_name", "genres", "members", "epk_url", "contact_name"]
```

**Available templates:**
- `festival_submission_jazz` - Jazz festival submissions
- `festival_submission_irish` - Irish/Celtic festivals
- `festival_submission_latin` - Latin jazz festivals
- `festival_submission_fusion` - Fusion/prog festivals
- `followup_email` - Post-submission follow-ups

## Automation

### Daily/Weekly Automation with Make

```bash
# Run all automation tasks
make automation

# Run daily tasks only (deadline checks, notifications)
make daily

# Run weekly tasks (reports, digests)
make weekly

# Check upcoming deadlines
make check-deadlines

# Setup cron automation
make setup-cron
```

### Manual Automation Commands

```bash
# Run all automation tasks
python scheduler.py --all

# Run daily tasks only
python scheduler.py --daily

# Run weekly tasks (reports)
python scheduler.py --weekly

# Check deadlines and send notifications
python notifications.py --check

# Send email digest (requires SMTP config)
python notifications.py --digest

# Test desktop notification
python notifications.py --test
```

### Cron Setup

**Using Make:**
```bash
make setup-cron
```

**Manual Setup:**
Add to crontab (`crontab -e`):

```cron
# Daily at 9am
0 9 * * * /path/to/festival-submit/run_automation.sh

# Weekly digest on Monday at 8am
0 8 * * 1 /path/to/festival-submit/run_automation.sh
```

## Email Configuration

Set environment variables for email notifications:

```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASS="your-app-password"      # Use app-specific password!
export EMAIL_TO="notifications@example.com"
```

**Security Best Practice:** Use app-specific passwords instead of your actual email password:
- Gmail: https://support.google.com/accounts/answer/185833
- Outlook: https://support.microsoft.com/en-us/account-billing/using-app-passwords-with-apps-that-don-t-support-two-step-verification-5896ed9b-4263-e681-128a-a6f2979a7944

Store in `.env` file (excluded from git):
```bash
# .env file
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
EMAIL_TO=notifications@example.com
```

## Project Structure

```
festival-submit/
├── config/
│   ├── acts.toml              # Act configurations and profiles
│   ├── festivals.toml         # Festival database (local/regional/national/intl)
│   └── templates.toml         # Email templates with variables
├── data/
│   └── submissions.db         # SQLite database (submissions, tasks)
├── logs/                      # Automation logs
│   └── run_*.log
├── reports/                   # Generated reports
│   ├── status_*.md
│   └── opportunities_*.md
├── exports/                   # Data exports (CSV, JSON)
├── submissions/               # Generated submission drafts
├── festival_submit.py         # Main CLI (database, matching, reports)
├── scheduler.py               # Automation scheduler (daily/weekly tasks)
├── notifications.py           # Notification system (email, desktop)
├── run_automation.sh          # Shell wrapper for cron
├── Makefile                   # Automation commands
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Database Schema

SQLite database with two main tables:

**submissions:**
- `id` - Auto-increment primary key
- `act_id` - References act in config
- `festival_id` - References festival in config
- `festival_name` - Display name
- `deadline_date` - Submission deadline
- `submission_date` - When submitted (NULL if draft)
- `submission_fee` - Cost to submit
- `status` - draft, submitted
- `response_status` - NULL, accepted, rejected, waitlisted
- `response_date` - When festival responded
- `notes` - Free-text notes

**scheduled_tasks:**
- Automated task tracking
- Deadline reminders
- Follow-up scheduling

## Commands Reference

| Command | Description |
|---------|-------------|
| `init` | Initialize database schema |
| `acts` | List all configured acts with details |
| `festivals` | List all festivals by tier |
| `match --act ID` | Find matching festivals for an act |
| `submit --act ID --festival ID` | Create a submission |
| `status [--act ID]` | Show submission status (all or by act) |
| `report --type TYPE [--act ID]` | Generate reports (status, opportunities) |
| `calendar [--months N]` | Generate submission calendar |
| `templates` | List available email templates |
| `render --template ID --act ID --festival ID` | Render template with substitutions |
| `export --format [csv\|json]` | Export submissions |

## Security

Festival Submit follows security best practices:

- **No Hardcoded Secrets** - All credentials via environment variables
- **SQL Injection Protection** - Parameterized queries throughout (recent security fix)
- **Command Injection Prevention** - Input sanitization in notification system (recent security fix)
- **Secure Defaults** - .env files excluded from git
- **App-Specific Passwords** - SMTP authentication uses app passwords, not account passwords

### Recent Security Fixes (2026-01-07)

Two critical vulnerabilities were identified and fixed:

1. **SQL Injection** (festival_submit.py:140-163)
   - **Fixed:** Replaced string concatenation with parameterized queries
   - **Impact:** Prevents malicious act_id values from executing arbitrary SQL

2. **Command Injection** (notifications.py:29-38)
   - **Fixed:** Added proper escaping for AppleScript strings
   - **Impact:** Prevents malicious notification titles/messages from executing shell commands

All code now follows secure coding practices.

## Workflow Examples

### Submit to Multiple Festivals

```bash
# Find all matching festivals for CloudBurst
make match ACT='cloudburst'

# Submit to several festivals
make submit ACT='cloudburst' FEST='regional.catskill_jazz'
make submit ACT='cloudburst' FEST='regional.saratoga_jazz'
make submit ACT='cloudburst' FEST='national.newport_jazz'

# Check submission status
make status
```

### Weekly Workflow

```bash
# Monday morning: Check status and upcoming deadlines
make status
make check-deadlines

# Review opportunities for specific act
make report-opps ACT='pablo_shine'

# View calendar for next 3 months
python festival_submit.py calendar --months 3
```

### Template Customization

```bash
# Render a template to preview
python festival_submit.py render \
    --template festival_submission_jazz \
    --act tree_of_life_trio \
    --festival regional.saratoga_jazz

# Output saved to submissions/ directory
```

## Reports

### Status Report
Shows all submissions grouped by status (draft, submitted, accepted, rejected):

```bash
make report-status
# Output: reports/status_YYYY-MM-DD.md
```

### Opportunities Report
Shows festivals matching a specific act:

```bash
make report-opps ACT='pablo_shine'
# Output: reports/opportunities_pablo_shine_YYYY-MM-DD.md
```

### Calendar View
Timeline of all deadlines:

```bash
make calendar
# Displays next 12 months of deadlines
```

## Troubleshooting

**Database errors:**
- Reinitialize: `python festival_submit.py init`
- Check file permissions on `data/submissions.db`

**Email notifications not working:**
- Verify SMTP environment variables are set
- Test with: `python notifications.py --test`
- Check if using app-specific password (not account password)
- Review logs in `logs/` directory

**Desktop notifications not appearing:**
- macOS only (uses osascript)
- Grant terminal app notification permissions in System Preferences
- Test with: `python notifications.py --test`

**Act or festival not found:**
- Check spelling in `config/acts.toml` and `config/festivals.toml`
- Act IDs and festival IDs must match exactly (case-sensitive)
- Use `make acts` and `make festivals` to list all IDs

## Dependencies

```bash
# Core dependencies
pip install -r requirements.txt

# No additional dependencies required
# Uses Python standard library for:
# - sqlite3 (database)
# - smtplib (email)
# - subprocess (desktop notifications)
```

## Documentation

- [Root README](../README.md) - Overview of both festival-submit and venue-scout
- [Makefile](Makefile) - Run `make help` for all automation commands

## Support

For issues or questions:
- Review this README for command reference
- Check logs in `logs/` directory
- Open an issue on GitHub

## License

Private - All rights reserved.
