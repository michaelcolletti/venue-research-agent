# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup Wizard (For Musicians)

For non-technical users, run the interactive web-based setup wizard to configure venue-scout:

```bash
# Install dependencies
pip install flask uszipcode

# Run the setup wizard
python setup_wizard.py
# Opens browser at http://localhost:5000
```

The wizard provides a user-friendly interface that:
1. **Step 1: Location** - Enter your NY zip code, automatically discovers nearby cities within a customizable radius
2. **Step 2: Acts** - Add one or more act profiles with guided forms for all required fields
3. **Step 3: Review** - Preview and save configuration, optionally initialize database

**Benefits:**
- No need to understand TOML format or edit config files manually
- Auto-detects region based on zip code
- Validates all inputs before saving
- Creates backup of existing config
- Works on mobile and desktop browsers

**Architecture:**
- `setup_wizard.py` - Flask web application serving the wizard interface
- `utils/config_generator.py` - Generates valid TOML from form data
- `templates/wizard.html` - Multi-step wizard UI
- `static/wizard.js` - Interactive form logic
- `static/wizard.css` - Musician-friendly styling

The wizard generates `config/venues.toml` matching the exact schema expected by the venue-scout system.

## Commands

### Daily Operations
```bash
# Initialize database (run once or to reset)
python venue_scout.py --init-db

# Run daily venue search (generates queries only)
python venue_scout.py --daily --max-queries 20

# Run daily search with Claude API (executes actual web searches)
python claude_search.py --daily --max-queries 15

# Process search results from Claude API
python search_runner.py --process data/search_results/daily_*.json

# Generate weekly report
python venue_scout.py --weekly-report
```

### Database Management
```bash
# View configured acts
python venue_scout.py --list-acts

# Manually add a venue
python venue_scout.py --add-venue "Venue Name" "City"

# Export all active venues
python venue_scout.py --export json
python venue_scout.py --export csv

# Exclude non-responsive venues
python venue_scout.py --exclude "Venue Name" "City" --exclude-reason no_response --exclude-notes "Your notes"

# List excluded venues
python venue_scout.py --list-excluded

# Remove venue from exclusion list
python venue_scout.py --unexclude "Venue Name" "City"
```

### Testing
```bash
# Create sample search results for testing
python search_runner.py --sample

# Process sample results
python search_runner.py --process data/sample_results.json

# Generate cron script
python search_runner.py --setup-cron
```

## Architecture

### Three-Script System

The codebase uses three main Python scripts that work together in a pipeline:

1. **venue_scout.py** - Core database and reporting engine
   - Database initialization and schema management (SQLite)
   - Query generation from templates and regions
   - Weekly report generation
   - Manual venue management (add, exclude, export)
   - CLI interface for all operations

2. **claude_search.py** - Claude API integration for web searches
   - Executes searches using Claude API with web_search tool
   - Requires `ANTHROPIC_API_KEY` environment variable
   - Builds prioritized query lists from config
   - Saves results to `data/search_results/`

3. **search_runner.py** - Result processing and automation
   - Parses search result text for venue information
   - Extracts opportunities (venues seeking musicians)
   - Processes batch results into database
   - Generates cron scripts for automation

### Database Schema

SQLite database (`data/venues.db`) with five core tables:

- **venues** - Core venue information (name, city, region, type, capacity, contact info, genres)
  - Primary key: MD5 hash of `name:city` (12 chars)
  - Unique constraint on (name, city)
  - Tracks first_seen, last_seen dates
  - Status field: active, closed, unverified, excluded

- **search_results** - Raw daily search findings (linked to venues via foreign key)

- **opportunities** - Booking leads and alerts (linked to venues, includes suitable_acts as JSON array)

- **search_history** - Query tracking and statistics

- **excluded_venues** - Venues to skip (no_response, bad_experience, closed, not_booking, wrong_fit)

### Configuration System

Single TOML file (`config/venues.toml`) controls:

- **Acts** - Multiple act profiles with genres, capacity range, venue types, fee range, members count
  - Used to match venues to suitable acts
  - Determines search priorities

- **Regions** - Geographic search areas with priority levels (1=highest)
  - Each region has counties and cities arrays
  - Lower priority number = searched first

- **Search Templates** - Query templates by type (new_venues, existing_venues, booking_opportunities)
  - Templates use `{city}` and `{region}` placeholders
  - Combined with regions to generate query lists

- **Alerts** - Keywords to detect opportunities ("booking live music", "seeking musicians")

- **Filters** - Exclusion patterns and quality thresholds

- **Excluded Venues** - Can be managed via CLI or directly in TOML

### Data Flow

```
1. venue_scout.py --daily
   └─> Generates queries from templates × regions × cities
   └─> Saves to data/queries_YYYYMMDD.json

2. claude_search.py --daily
   └─> Reads config, builds prioritized queries
   └─> Executes via Claude API web_search tool
   └─> Saves results to data/search_results/daily_YYYYMMDD_HHMM.json

3. search_runner.py --process <results_file>
   └─> Parses venue names/cities from result text
   └─> Checks for alert keywords (seeking musicians, etc.)
   └─> Inserts/updates venues table
   └─> Creates opportunity records
   └─> Updates search_history

4. venue_scout.py --weekly-report
   └─> Queries database for week's statistics
   └─> Generates markdown report in reports/
   └─> Includes new venues, opportunities, coverage by region
```

## Environment Setup

```bash
# Required for Claude API searches
export ANTHROPIC_API_KEY='sk-ant-...'

# Install dependencies
pip install anthropic
```

## Key Design Patterns

### Venue ID Generation
Uses MD5 hash of `name:city` (lowercase, stripped) truncated to 12 characters. This enables idempotent updates - same venue found multiple times updates last_seen date rather than creating duplicates.

### Exclusion System
Two-tier exclusion: database table (`excluded_venues`) and config file (`venues.toml`). Config exclusions are loaded into database on init. Both CLI and direct TOML editing supported. Excluded venues are marked with `status='excluded'` in main venues table.

### Act Matching
`match_acts_to_venue()` compares venue type and genres against all configured acts, returning list of suitable act names. Used to populate `opportunities.suitable_acts` field (stored as JSON array).

### Priority-Based Search
Queries sorted by region priority (lower = higher) before limiting to max_queries. Ensures most important regions searched first.

### Report Generation
Weekly reports calculate date ranges as "last Monday through Sunday", query database for that week's new venues/opportunities, and generate markdown with emoji priority indicators (🔴🟠🟡🟢⚪).

## Notable Implementation Details

- Uses Python 3.11+ features: `tomllib` (built-in TOML parser), `match/case` not used but could be
- All dates stored as strings in ISO format (YYYY-MM-DD)
- Genres and suitable_acts stored as JSON arrays in TEXT columns
- Claude API integration uses `claude-sonnet-4-20250514` model with web_search tool
- Search result parsing uses regex patterns to extract venue names from unstructured text
- Cron integration via generated bash script with daily runs and Sunday weekly reports
