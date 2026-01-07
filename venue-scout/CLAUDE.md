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
1. **Step 1: Location** - Enter your US zip code, automatically discovers nearby cities within a customizable radius (supports any state)
2. **Step 2: Acts** - Add one or more act profiles with guided forms for all required fields
3. **Step 3: Review** - Preview and save configuration, optionally initialize database

**Benefits:**
- Works with any US state (not limited to NY)
- No need to understand TOML format or edit config files manually
- Auto-detects region based on county/zip code
- Generates state-specific search templates
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

## Multi-Provider LLM Support

**NEW**: Venue-scout now supports multiple LLM providers for web searches, not just Claude! Choose from:
- **Claude** (Anthropic) - Native web search, most reliable
- **OpenRouter** - Access to multiple models (GPT-4, Gemini, etc.) with web search via Exa.ai
- **Ollama** - Free local models, privacy-focused (requires local installation)
- **MCP** (Model Context Protocol) - Universal web search with any LLM

### Quick Start with Different Providers

```bash
# Using Claude (default, existing behavior)
export ANTHROPIC_API_KEY='sk-ant-...'
python unified_search.py --daily

# Using OpenRouter (free tier available, multiple models)
export OPENROUTER_API_KEY='sk-or-...'
python unified_search.py --daily --provider openrouter

# Using Ollama (free, runs locally)
ollama pull llama3.1:latest
ollama serve
python unified_search.py --daily --provider ollama

# Using MCP (flexible, multiple search engines)
npm install -g web-search-mcp
export ANTHROPIC_API_KEY='sk-ant-...'  # or other LLM key
python unified_search.py --daily --provider mcp
```

### Configuration

Configure providers in `config/venues.toml`:

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

### Provider Comparison

| Provider | Cost | Web Search | Setup Complexity | Privacy |
|----------|------|------------|------------------|---------|
| **Claude** | $$ (API usage) | Native (included) | Easy (API key) | Cloud |
| **OpenRouter** | $ (varies by model + $4/1000 search results) | Via Exa.ai | Easy (API key) | Cloud |
| **Ollama** | Free (local compute) | Limited (via MCP) | Medium (local install) | Private |
| **MCP** | Varies by server | Multiple engines | Advanced | Configurable |

### Setup Instructions by Provider

#### Claude (Anthropic)
```bash
# Get API key from https://console.anthropic.com/
export ANTHROPIC_API_KEY='sk-ant-...'
pip install anthropic

# Run searches
python unified_search.py --daily --provider claude
```

#### OpenRouter
```bash
# Get API key from https://openrouter.ai/ (free tier available)
export OPENROUTER_API_KEY='sk-or-...'
pip install openai

# Run searches (web search via Exa.ai)
python unified_search.py --daily --provider openrouter

# Try different models
# Edit config/venues.toml:
#   [search_provider.openrouter]
#   model = "google/gemini-2.0-flash-exp:online"  # or other :online model
```

#### Ollama (Local)
```bash
# Install Ollama from https://ollama.ai/
# Download model
ollama pull llama3.1:latest

# Start Ollama service
ollama serve

# Install Python client
pip install ollama

# Run searches (uses local model)
python unified_search.py --daily --provider ollama

# Note: Ollama doesn't have native web search
# For web search with Ollama, use MCP provider with Ollama as LLM
```

#### MCP (Model Context Protocol)
```bash
# Install MCP server (WebSearch-MCP is free, no API key)
npm install -g web-search-mcp

# Install MCP Python SDK
pip install mcp

# Install LLM client (Claude, OpenAI, etc.)
pip install anthropic  # or openai
export ANTHROPIC_API_KEY='sk-ant-...'

# Run searches (MCP for search, LLM for analysis)
python unified_search.py --daily --provider mcp

# Alternative MCP servers:
# SerpApi: npm install -g mcp-server-serpapi (requires SERPAPI_API_KEY)
# Brave: npm install -g @modelcontextprotocol/server-brave-search (requires BRAVE_API_KEY)
```

### Migrating from claude_search.py

The old `claude_search.py` still works but is deprecated. Migrate to `unified_search.py`:

```bash
# Old way (still works, shows deprecation warning)
python claude_search.py --daily

# New way (same behavior with Claude)
python unified_search.py --daily --provider claude

# Or use configured default provider
python unified_search.py --daily
```

### Automatic Fallback

Configure fallback providers in case the primary fails:

```toml
[search_provider]
default_provider = "claude"
fallback_providers = ["openrouter", "ollama"]  # tries these in order if Claude fails
```

The system will automatically try fallback providers if the primary is unavailable.

## Commands

### Daily Operations
```bash
# Initialize database (run once or to reset)
python venue_scout.py --init-db

# Run daily venue search (NEW: multi-provider support)
python unified_search.py --daily --max-queries 15

# Or specify a specific provider
python unified_search.py --daily --provider openrouter --max-queries 15

# Legacy: Old Claude-only script (still works but deprecated)
python claude_search.py --daily --max-queries 15

# Process search results (works with all providers)
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

- **venues** - Core venue information (name, city, region, state, type, capacity, contact info, genres)
  - Primary key: MD5 hash of `name:city` (12 chars)
  - Unique constraint on (name, city)
  - Tracks first_seen, last_seen dates
  - Status field: active, closed, unverified, excluded
  - State field: 2-letter state code (defaults to 'NY' for legacy compatibility)

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
- Claude API integration:
  - Model: `claude-sonnet-4-20250514` (as of May 2025 - update to latest available model as needed)
  - Web search tool: `web_search_20250305` (March 2025 version - update to latest available version as needed)
  - See claude_search.py:92-96 for implementation
- Search result parsing uses regex patterns to extract venue names from unstructured text
- Cron integration via generated bash script with daily runs and Sunday weekly reports
