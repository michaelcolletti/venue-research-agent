#!/usr/bin/env python3
"""
Venue Scout - Automated Search Runner

This script executes the actual web searches and processes results.
Designed to be run via cron or as a scheduled task.

For use with Claude API or as a standalone web scraper.
"""

import json
import os
import sys
import sqlite3
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import tomllib
import hashlib
import argparse

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config" / "venues.toml"
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"
DB_PATH = DATA_DIR / "venues.db"


def load_config() -> dict:
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def generate_venue_id(name: str, city: str) -> str:
    key = f"{name.lower().strip()}:{city.lower().strip()}"
    return hashlib.md5(key.encode()).hexdigest()[:12]


def parse_search_results(results_text: str, query_info: dict) -> list[dict]:
    """
    Parse search results text into structured venue data.
    This handles various formats from web search results.
    """
    venues = []
    
    # Common patterns for venue information
    venue_patterns = [
        # Pattern: "Venue Name - City, NY"
        r'([A-Z][^-\n]+?)\s*[-–]\s*([A-Za-z\s]+),?\s*(?:NY|New York)',
        # Pattern: "Venue Name in City"
        r'([A-Z][^in\n]+?)\s+in\s+([A-Za-z\s]+)',
    ]
    
    # Extract potential venue mentions
    lines = results_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 10:
            continue
            
        # Skip obvious non-venue lines
        skip_patterns = ['http', 'www.', 'click here', 'read more', 'advertisement']
        if any(p in line.lower() for p in skip_patterns):
            continue
        
        # Try to extract venue information
        for pattern in venue_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                city = match.group(2).strip()
                
                # Filter out non-venue matches
                if len(name) > 5 and len(name) < 100:
                    venues.append({
                        "name": name,
                        "city": city,
                        "region": query_info.get("region"),
                        "source": "web_search",
                        "source_query": query_info.get("query"),
                        "raw_text": line[:200]
                    })
                break
    
    return venues


def extract_opportunities(text: str, config: dict) -> list[dict]:
    """Extract booking opportunities from search result text."""
    opportunities = []
    alert_keywords = config.get("alerts", {}).get("seeking_artists_keywords", [])
    
    text_lower = text.lower()
    
    for keyword in alert_keywords:
        if keyword.lower() in text_lower:
            # Find the sentence containing the keyword
            sentences = re.split(r'[.!?]', text)
            for sent in sentences:
                if keyword.lower() in sent.lower():
                    opportunities.append({
                        "type": "seeking_artists",
                        "description": sent.strip()[:500],
                        "keyword_matched": keyword
                    })
                    break
    
    return opportunities


def process_daily_results(results_file: Path, config: dict):
    """Process search results from a daily run."""
    print(f"Processing results from: {results_file}")

    with open(results_file) as f:
        results_data = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get state from config
    state = config.get("settings", {}).get("state", "NY")

    stats = {
        "results_processed": 0,
        "venues_found": 0,
        "new_venues": 0,
        "opportunities": 0
    }

    for result in results_data.get("results", []):
        stats["results_processed"] += 1

        query_info = result.get("query_info", {})
        search_text = result.get("text", "")

        # Parse for venues
        venues = parse_search_results(search_text, query_info)
        stats["venues_found"] += len(venues)

        for venue in venues:
            # Add state to venue data
            venue["state"] = state
            venue_id = generate_venue_id(venue["name"], venue["city"])
            
            # Check if new
            cursor.execute("SELECT id FROM venues WHERE id = ?", (venue_id,))
            if not cursor.fetchone():
                stats["new_venues"] += 1
                today = datetime.now().strftime("%Y-%m-%d")
                cursor.execute("""
                    INSERT INTO venues (id, name, city, region, state, source, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (venue_id, venue["name"], venue["city"], venue["region"],
                      venue.get("state"), venue["source"], today, today))
        
        # Extract opportunities
        opportunities = extract_opportunities(search_text, config)
        stats["opportunities"] += len(opportunities)
        
        for opp in opportunities:
            cursor.execute("""
                INSERT INTO opportunities (opportunity_type, description, discovered_date)
                VALUES (?, ?, ?)
            """, (opp["type"], opp["description"], datetime.now().strftime("%Y-%m-%d")))
    
    conn.commit()
    conn.close()
    
    print(f"\nProcessing complete:")
    print(f"  Results processed: {stats['results_processed']}")
    print(f"  Venues found: {stats['venues_found']}")
    print(f"  New venues: {stats['new_venues']}")
    print(f"  Opportunities: {stats['opportunities']}")
    
    return stats


def create_sample_results_file():
    """Create a sample results file for testing."""
    sample_data = {
        "date": datetime.now().isoformat(),
        "results": [
            {
                "query_info": {
                    "query": "Kingston NY live music venues",
                    "region": "Hudson Valley",
                    "city": "Kingston"
                },
                "text": """
BSP Kingston - Kingston, NY - Live music venue featuring indie and alternative acts.
Keegan Ales - Kingston, NY - Brewery with live music on weekends.
The Anchor - Kingston, New York - Bar and music venue, seeking local musicians.
Stockade Tavern - Kingston - Historic tavern with occasional live music.
"""
            },
            {
                "query_info": {
                    "query": "Woodstock NY jazz clubs",
                    "region": "Hudson Valley", 
                    "city": "Woodstock"
                },
                "text": """
The Colony - Woodstock, NY - Legendary music venue, all genres welcome.
Bearsville Theater - Woodstock - Concert venue booking live music acts.
Looking for musicians to play our new outdoor series this summer!
"""
            }
        ]
    }
    
    sample_path = DATA_DIR / "sample_results.json"
    with open(sample_path, "w") as f:
        json.dump(sample_data, f, indent=2)
    
    print(f"Created sample results file: {sample_path}")
    return sample_path


def run_interactive_search(query: str):
    """
    Run a single search query interactively.
    This is a placeholder for actual web search integration.
    """
    print(f"\n🔍 Search Query: {query}")
    print("-" * 50)
    print("""
To integrate with actual web search:

1. Claude API Integration:
   - Use Claude's web_search tool
   - Parse results and feed to process_daily_results()

2. Direct Search API:
   - Google Custom Search API
   - Bing Search API
   - SerpAPI

3. Manual Process:
   - Run search in browser
   - Copy results to JSON file
   - Process with: python search_runner.py --process <file>

Example Claude API call structure:
{
    "tool": "web_search",
    "query": "<query>",
    "max_results": 10
}
""")


def generate_search_script():
    """Generate a bash script for manual/cron execution."""
    script_content = '''#!/bin/bash
# Venue Scout - Daily Search Script
# Run this via cron: 0 6 * * * /path/to/run_daily.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/daily_$(date +%Y%m%d).log"

echo "=== Venue Scout Daily Run ===" >> "$LOG_FILE"
echo "Started: $(date)" >> "$LOG_FILE"

# Run daily search
cd "$SCRIPT_DIR"
python3 venue_scout.py --daily >> "$LOG_FILE" 2>&1

# Check if it's Sunday for weekly report
if [ $(date +%u) -eq 7 ]; then
    echo "Generating weekly report..." >> "$LOG_FILE"
    python3 venue_scout.py --weekly-report >> "$LOG_FILE" 2>&1
fi

echo "Completed: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
'''
    
    script_path = BASE_DIR / "run_daily.sh"
    with open(script_path, "w") as f:
        f.write(script_content)
    os.chmod(script_path, 0o755)
    
    print(f"Created daily run script: {script_path}")
    print("\nTo set up cron job:")
    print(f"  crontab -e")
    print(f"  # Add: 0 6 * * * {script_path}")
    
    return script_path


def main():
    parser = argparse.ArgumentParser(description="Venue Scout Search Runner")
    parser.add_argument("--process", type=str, help="Process results file")
    parser.add_argument("--sample", action="store_true", help="Create sample results file")
    parser.add_argument("--search", type=str, help="Run interactive search")
    parser.add_argument("--setup-cron", action="store_true", help="Generate cron scripts")
    
    args = parser.parse_args()
    config = load_config()
    
    if args.process:
        process_daily_results(Path(args.process), config)
    elif args.sample:
        sample_path = create_sample_results_file()
        print("\nTo test processing:")
        print(f"  python search_runner.py --process {sample_path}")
    elif args.search:
        run_interactive_search(args.search)
    elif args.setup_cron:
        generate_search_script()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
