#!/usr/bin/env python3
"""
Venue Scout - Research Agent for Finding Performance Venues

This agent searches for new and existing music venues based on configurable
criteria, stores results daily, and generates weekly summary reports.

Usage:
    python venue_scout.py --daily          # Run daily search
    python venue_scout.py --weekly-report  # Generate weekly report
    python venue_scout.py --search "query" # Ad-hoc search
    python venue_scout.py --list-acts      # Show configured acts
"""

import argparse
import json
import os
import sys
import hashlib
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import tomllib
import re
import urllib.parse
import subprocess
import tempfile

# Configuration
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config" / "venues.toml"
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"
DB_PATH = DATA_DIR / "venues.db"


def load_config() -> dict:
    """Load configuration from TOML file."""
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def init_database():
    """Initialize SQLite database for storing venue data."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Venues table - core venue information
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS venues (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT,
            region TEXT,
            state TEXT DEFAULT 'NY',
            venue_type TEXT,
            capacity_estimate INTEGER,
            has_live_music BOOLEAN DEFAULT 1,
            website TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            booking_contact TEXT,
            genres TEXT,  -- JSON array
            notes TEXT,
            source TEXT,
            source_url TEXT,
            first_seen DATE,
            last_seen DATE,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active',  -- active, closed, unverified
            rating REAL,
            UNIQUE(name, city)
        )
    """
    )

    # Daily search results - raw search findings
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS search_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_date DATE NOT NULL,
            search_query TEXT,
            region TEXT,
            result_title TEXT,
            result_snippet TEXT,
            result_url TEXT,
            venue_id TEXT,
            processed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (venue_id) REFERENCES venues(id)
        )
    """
    )

    # Opportunities - booking leads and alerts
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venue_id TEXT,
            opportunity_type TEXT,  -- new_venue, seeking_artists, event, etc.
            description TEXT,
            source_url TEXT,
            discovered_date DATE,
            expiry_date DATE,
            status TEXT DEFAULT 'new',  -- new, contacted, booked, passed
            priority INTEGER DEFAULT 5,  -- 1=highest, 10=lowest
            notes TEXT,
            suitable_acts TEXT,  -- JSON array of act names
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (venue_id) REFERENCES venues(id)
        )
    """
    )

    # Search history - track what we've searched
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_date DATE NOT NULL,
            query TEXT NOT NULL,
            results_count INTEGER,
            new_venues_found INTEGER DEFAULT 0,
            opportunities_found INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Weekly reports metadata
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date DATE NOT NULL,
            week_start DATE,
            week_end DATE,
            report_path TEXT,
            summary TEXT,
            new_venues_count INTEGER,
            opportunities_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Excluded venues table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS excluded_venues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venue_id TEXT,
            name TEXT NOT NULL,
            city TEXT,
            reason TEXT,
            date_excluded DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name, city)
        )
    """
    )

    # Load exclusions from config
    config = load_config()
    excluded = config.get("excluded", {}).get("venues", [])
    for venue in excluded:
        if venue.get("name") and venue.get("name") != "Example Excluded Venue":
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO excluded_venues (name, city, reason, date_excluded, notes)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        venue.get("name"),
                        venue.get("city"),
                        venue.get("reason"),
                        venue.get("date_excluded"),
                        venue.get("notes"),
                    ),
                )
            except:
                pass

    conn.commit()
    conn.close()
    print(f"Database initialized: {DB_PATH}")


def generate_venue_id(name: str, city: str) -> str:
    """Generate a unique ID for a venue based on name and city."""
    key = f"{name.lower().strip()}:{city.lower().strip()}"
    return hashlib.md5(key.encode()).hexdigest()[:12]


def build_search_queries(config: dict) -> list[dict]:
    """Build list of search queries from config templates and regions."""
    queries = []
    templates = config.get("search_templates", {})
    regions = config.get("regions", {})

    for region_key, region_data in regions.items():
        region_name = region_data.get("name", region_key)
        priority = region_data.get("priority", 5)
        cities = region_data.get("cities", [])

        # Generate queries for each city in the region
        for city in cities:
            for template_type, template_list in templates.items():
                for template in template_list:
                    query = template.format(city=city, region=region_name)
                    queries.append(
                        {
                            "query": query,
                            "type": template_type,
                            "region": region_name,
                            "city": city,
                            "priority": priority,
                        }
                    )

    # Sort by priority (lower = higher priority)
    queries.sort(key=lambda x: x["priority"])
    return queries


def save_search_result(conn: sqlite3.Connection, result: dict):
    """Save a search result to the database."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO search_results 
        (search_date, search_query, region, result_title, result_snippet, result_url)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            datetime.now().strftime("%Y-%m-%d"),
            result.get("query"),
            result.get("region"),
            result.get("title"),
            result.get("snippet"),
            result.get("url"),
        ),
    )
    conn.commit()


def save_venue(conn: sqlite3.Connection, venue: dict) -> str:
    """Save or update a venue in the database. Returns venue_id."""
    venue_id = generate_venue_id(venue["name"], venue.get("city", "Unknown"))
    cursor = conn.cursor()

    # Check if venue exists
    cursor.execute("SELECT id FROM venues WHERE id = ?", (venue_id,))
    exists = cursor.fetchone()

    today = datetime.now().strftime("%Y-%m-%d")

    if exists:
        # Update last_seen
        cursor.execute(
            """
            UPDATE venues SET last_seen = ?, last_updated = CURRENT_TIMESTAMP
            WHERE id = ?
        """,
            (today, venue_id),
        )
    else:
        # Insert new venue
        cursor.execute(
            """
            INSERT INTO venues (id, name, city, region, state, venue_type, website,
                               source, source_url, first_seen, last_seen, genres)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                venue_id,
                venue["name"],
                venue.get("city"),
                venue.get("region"),
                venue.get("state"),  # Use state from venue dict if provided
                venue.get("venue_type"),
                venue.get("website"),
                venue.get("source"),
                venue.get("source_url"),
                today,
                today,
                json.dumps(venue.get("genres", [])),
            ),
        )

    conn.commit()
    return venue_id


def save_opportunity(conn: sqlite3.Connection, opportunity: dict):
    """Save a new opportunity to the database."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO opportunities 
        (venue_id, opportunity_type, description, source_url, discovered_date, 
         priority, suitable_acts)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            opportunity.get("venue_id"),
            opportunity.get("type"),
            opportunity.get("description"),
            opportunity.get("source_url"),
            datetime.now().strftime("%Y-%m-%d"),
            opportunity.get("priority", 5),
            json.dumps(opportunity.get("suitable_acts", [])),
        ),
    )
    conn.commit()


def check_for_alerts(config: dict, text: str) -> list[str]:
    """Check text for alert keywords. Returns list of matched alert types."""
    alerts = []
    alert_config = config.get("alerts", {})

    text_lower = text.lower()

    # Check seeking artists keywords
    for keyword in alert_config.get("seeking_artists_keywords", []):
        if keyword.lower() in text_lower:
            alerts.append("seeking_artists")
            break

    # Check fee mention keywords
    for keyword in alert_config.get("fee_mention_keywords", []):
        if keyword.lower() in text_lower:
            alerts.append("good_pay")
            break

    return alerts


def match_acts_to_venue(config: dict, venue_type: str, genres: list) -> list[str]:
    """Find which configured acts would be suitable for a venue."""
    suitable_acts = []
    acts = config.get("acts", {})

    venue_type_lower = venue_type.lower() if venue_type else ""
    genres_lower = [g.lower() for g in genres] if genres else []

    for act_key, act_data in acts.items():
        act_venue_types = [v.lower() for v in act_data.get("venue_types", [])]
        act_genres = [g.lower() for g in act_data.get("genres", [])]

        # Check if venue type matches
        type_match = any(vt in venue_type_lower for vt in act_venue_types)

        # Check if genres overlap
        genre_match = (
            any(g in genres_lower for g in act_genres) if genres_lower else False
        )

        if type_match or genre_match:
            suitable_acts.append(act_data.get("name", act_key))

    return suitable_acts


def run_daily_search(config: dict, max_queries: int = 20):
    """Run the daily venue search routine."""
    print(f"\n{'='*60}")
    print(f"VENUE SCOUT - Daily Search")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    init_database()
    conn = sqlite3.connect(DB_PATH)

    queries = build_search_queries(config)
    print(f"Generated {len(queries)} search queries")
    print(f"Running top {max_queries} by priority...\n")

    # Limit queries for daily run
    queries = queries[:max_queries]

    results_summary = {
        "queries_run": 0,
        "results_found": 0,
        "new_venues": 0,
        "opportunities": 0,
    }

    # Store queries to run - in practice, these would call actual search APIs
    queries_file = DATA_DIR / f"queries_{datetime.now().strftime('%Y%m%d')}.json"

    search_data = {
        "date": datetime.now().isoformat(),
        "queries": queries,
        "instructions": """
To run these searches:
1. Use web search tool with each query
2. Parse results for venue information
3. Run: python venue_scout.py --process-results <results_file>

For automated daily runs, integrate with:
- Claude API for search execution
- Cron job for scheduling
- Email/Slack for alert notifications
""",
    }

    with open(queries_file, "w") as f:
        json.dump(search_data, f, indent=2)

    print(f"Search queries saved to: {queries_file}")
    print(f"\nQuery breakdown by region:")

    region_counts = {}
    for q in queries:
        region = q["region"]
        region_counts[region] = region_counts.get(region, 0) + 1

    for region, count in sorted(region_counts.items()):
        print(f"  - {region}: {count} queries")

    print(f"\nQuery breakdown by type:")
    type_counts = {}
    for q in queries:
        qtype = q["type"]
        type_counts[qtype] = type_counts.get(qtype, 0) + 1

    for qtype, count in sorted(type_counts.items()):
        print(f"  - {qtype}: {count} queries")

    conn.close()
    return queries_file


def generate_weekly_report(config: dict) -> Path:
    """Generate the weekly summary report."""
    print(f"\n{'='*60}")
    print(f"VENUE SCOUT - Weekly Report")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Calculate week range
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday() + 7)  # Last Monday
    week_end = week_start + timedelta(days=6)  # Last Sunday

    week_start_str = week_start.strftime("%Y-%m-%d")
    week_end_str = week_end.strftime("%Y-%m-%d")

    # Gather statistics
    cursor.execute(
        """
        SELECT COUNT(*) FROM venues WHERE first_seen BETWEEN ? AND ?
    """,
        (week_start_str, week_end_str),
    )
    new_venues = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*) FROM opportunities WHERE discovered_date BETWEEN ? AND ?
    """,
        (week_start_str, week_end_str),
    )
    new_opportunities = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM venues WHERE status = 'active'")
    total_venues = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*) FROM opportunities WHERE status = 'new'
    """
    )
    open_opportunities = cursor.fetchone()[0]

    # Get new venues this week
    cursor.execute(
        """
        SELECT name, city, region, venue_type, website, first_seen
        FROM venues 
        WHERE first_seen BETWEEN ? AND ?
        ORDER BY first_seen DESC
    """,
        (week_start_str, week_end_str),
    )
    new_venue_list = cursor.fetchall()

    # Get new opportunities this week
    cursor.execute(
        """
        SELECT o.opportunity_type, o.description, o.source_url, 
               o.priority, o.suitable_acts, v.name as venue_name
        FROM opportunities o
        LEFT JOIN venues v ON o.venue_id = v.id
        WHERE o.discovered_date BETWEEN ? AND ?
        ORDER BY o.priority ASC
    """,
        (week_start_str, week_end_str),
    )
    opportunity_list = cursor.fetchall()

    # Get venues by region
    cursor.execute(
        """
        SELECT region, COUNT(*) as count 
        FROM venues 
        WHERE status = 'active'
        GROUP BY region
        ORDER BY count DESC
    """
    )
    venues_by_region = cursor.fetchall()

    # Build report
    report_date = today.strftime("%Y-%m-%d")
    report_filename = f"weekly_report_{report_date}.md"
    report_path = REPORTS_DIR / report_filename

    report_lines = [
        f"# Venue Scout Weekly Report",
        f"",
        f"**Report Date:** {report_date}",
        f"**Week Covered:** {week_start_str} to {week_end_str}",
        f"",
        f"---",
        f"",
        f"## Summary",
        f"",
        f"| Metric | This Week | Total |",
        f"|--------|-----------|-------|",
        f"| New Venues Discovered | {new_venues} | {total_venues} |",
        f"| New Opportunities | {new_opportunities} | {open_opportunities} open |",
        f"",
    ]

    # New venues section
    if new_venue_list:
        report_lines.extend(
            [
                f"## New Venues Discovered",
                f"",
            ]
        )
        for venue in new_venue_list:
            name, city, region, vtype, website, first_seen = venue
            report_lines.append(f"### {name}")
            report_lines.append(f"- **Location:** {city}, {region}")
            report_lines.append(f"- **Type:** {vtype or 'Unknown'}")
            if website:
                report_lines.append(f"- **Website:** {website}")
            report_lines.append(f"- **Discovered:** {first_seen}")
            report_lines.append("")

    # Opportunities section
    if opportunity_list:
        report_lines.extend(
            [
                f"## Booking Opportunities",
                f"",
            ]
        )
        for opp in opportunity_list:
            otype, desc, url, priority, suitable, venue_name = opp
            priority_label = ["🔴", "🟠", "🟡", "🟢", "⚪"][min(priority - 1, 4)]
            report_lines.append(
                f"### {priority_label} {otype.replace('_', ' ').title()}"
            )
            if venue_name:
                report_lines.append(f"**Venue:** {venue_name}")
            report_lines.append(f"**Details:** {desc}")
            if suitable:
                acts = json.loads(suitable) if isinstance(suitable, str) else suitable
                report_lines.append(f"**Suitable Acts:** {', '.join(acts)}")
            if url:
                report_lines.append(f"**Source:** {url}")
            report_lines.append("")

    # Coverage section
    report_lines.extend(
        [
            f"## Database Coverage by Region",
            f"",
            f"| Region | Active Venues |",
            f"|--------|---------------|",
        ]
    )
    for region, count in venues_by_region:
        report_lines.append(f"| {region or 'Unknown'} | {count} |")

    # Configured acts summary
    report_lines.extend(
        [
            f"",
            f"## Configured Acts",
            f"",
        ]
    )
    for act_key, act_data in config.get("acts", {}).items():
        report_lines.append(
            f"- **{act_data.get('name', act_key)}**: {', '.join(act_data.get('genres', []))}"
        )

    # Write report
    report_content = "\n".join(report_lines)
    with open(report_path, "w") as f:
        f.write(report_content)

    # Save report metadata
    cursor.execute(
        """
        INSERT INTO reports (report_date, week_start, week_end, report_path,
                            new_venues_count, opportunities_count)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            report_date,
            week_start_str,
            week_end_str,
            str(report_path),
            new_venues,
            new_opportunities,
        ),
    )
    conn.commit()
    conn.close()

    print(f"Report generated: {report_path}")
    print(f"\n{report_content}")

    return report_path


def list_acts(config: dict):
    """Display configured acts and their criteria."""
    print(f"\n{'='*60}")
    print("CONFIGURED ACTS")
    print(f"{'='*60}\n")

    acts = config.get("acts", {})

    for act_key, act_data in acts.items():
        print(f"## {act_data.get('name', act_key)}")
        print(f"   Genres: {', '.join(act_data.get('genres', []))}")
        print(
            f"   Capacity: {act_data.get('min_capacity')}-{act_data.get('max_capacity')} (ideal: {act_data.get('ideal_capacity')})"
        )
        print(f"   Members: {act_data.get('members')}")
        print(f"   Fee Range: ${act_data.get('min_fee')}-${act_data.get('max_fee')}")
        print(f"   Available: {', '.join(act_data.get('available_days', []))}")
        print(f"   Venue Types:")
        for vt in act_data.get("venue_types", [])[:5]:
            print(f"      - {vt}")
        if act_data.get("notes"):
            print(f"   Notes: {act_data.get('notes')}")
        print()


def add_venue_manual(config: dict, name: str, city: str, **kwargs):
    """Manually add a venue to the database."""
    init_database()
    conn = sqlite3.connect(DB_PATH)

    # Get state from kwargs or config
    state = kwargs.get("state") or config.get("settings", {}).get("state", "NY")

    venue = {
        "name": name,
        "city": city,
        "region": kwargs.get("region"),
        "state": state,
        "venue_type": kwargs.get("venue_type"),
        "website": kwargs.get("website"),
        "source": "manual",
        "genres": kwargs.get("genres", []),
    }

    venue_id = save_venue(conn, venue)
    conn.close()

    print(f"Added venue: {name} ({city}, {state}) - ID: {venue_id}")
    return venue_id


def export_venues(output_format: str = "json") -> Path:
    """Export all venues to a file."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, city, region, state, venue_type, capacity_estimate,
               website, phone, email, address, booking_contact, genres,
               status, rating, first_seen, last_seen
        FROM venues
        WHERE status = 'active'
        ORDER BY region, city, name
    """
    )

    venues = []
    for row in cursor.fetchall():
        venues.append(
            {
                "id": row[0],
                "name": row[1],
                "city": row[2],
                "region": row[3],
                "state": row[4],
                "venue_type": row[5],
                "capacity": row[6],
                "website": row[7],
                "phone": row[8],
                "email": row[9],
                "address": row[10],
                "booking_contact": row[11],
                "genres": json.loads(row[12]) if row[12] else [],
                "status": row[13],
                "rating": row[14],
                "first_seen": row[15],
                "last_seen": row[16],
            }
        )

    conn.close()

    export_path = (
        DATA_DIR / f"venues_export_{datetime.now().strftime('%Y%m%d')}.{output_format}"
    )

    if output_format == "json":
        with open(export_path, "w") as f:
            json.dump(venues, f, indent=2)
    elif output_format == "csv":
        import csv

        with open(export_path, "w", newline="") as f:
            if venues:
                writer = csv.DictWriter(f, fieldnames=venues[0].keys())
                writer.writeheader()
                writer.writerows(venues)

    print(f"Exported {len(venues)} venues to: {export_path}")
    return export_path


def exclude_venue(name: str, city: str, reason: str = "no_response", notes: str = None):
    """Add a venue to the exclusion list."""
    init_database()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    try:
        cursor.execute(
            """
            INSERT INTO excluded_venues (name, city, reason, date_excluded, notes)
            VALUES (?, ?, ?, ?, ?)
        """,
            (name, city, reason, today, notes),
        )
        conn.commit()
        print(f"✗ Excluded: {name} ({city}) - Reason: {reason}")
    except sqlite3.IntegrityError:
        print(f"Already excluded: {name} ({city})")

    # Also mark as excluded in main venues table if exists
    venue_id = generate_venue_id(name, city)
    cursor.execute("UPDATE venues SET status = 'excluded' WHERE id = ?", (venue_id,))
    conn.commit()
    conn.close()


def unexclude_venue(name: str, city: str):
    """Remove a venue from the exclusion list."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM excluded_venues WHERE name = ? AND city = ?", (name, city)
    )

    if cursor.rowcount > 0:
        print(f"✓ Removed from exclusion list: {name} ({city})")
        # Restore status in main venues table
        venue_id = generate_venue_id(name, city)
        cursor.execute("UPDATE venues SET status = 'active' WHERE id = ?", (venue_id,))
    else:
        print(f"Not found in exclusion list: {name} ({city})")

    conn.commit()
    conn.close()


def list_excluded_venues():
    """List all excluded venues."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT name, city, reason, date_excluded, notes 
        FROM excluded_venues 
        ORDER BY date_excluded DESC
    """
    )

    excluded = cursor.fetchall()
    conn.close()

    print(f"\n{'='*60}")
    print("EXCLUDED VENUES")
    print(f"{'='*60}\n")

    if not excluded:
        print("No venues currently excluded.")
        return

    print(f"{'Name':<30} {'City':<15} {'Reason':<15} {'Date'}")
    print("-" * 75)

    for name, city, reason, date_excluded, notes in excluded:
        print(f"{name:<30} {city or '':<15} {reason or '':<15} {date_excluded or ''}")
        if notes:
            print(f"    Notes: {notes}")

    print(f"\nTotal: {len(excluded)} excluded venues")


def is_venue_excluded(name: str, city: str) -> bool:
    """Check if a venue is in the exclusion list."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 1 FROM excluded_venues WHERE name = ? AND city = ?
    """,
        (name, city),
    )

    result = cursor.fetchone() is not None
    conn.close()
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Venue Scout - Research Agent for Finding Performance Venues"
    )
    parser.add_argument("--daily", action="store_true", help="Run daily search routine")
    parser.add_argument(
        "--weekly-report", action="store_true", help="Generate weekly summary report"
    )
    parser.add_argument("--list-acts", action="store_true", help="List configured acts")
    parser.add_argument(
        "--init-db", action="store_true", help="Initialize/reset database"
    )
    parser.add_argument(
        "--add-venue", nargs=2, metavar=("NAME", "CITY"), help="Manually add a venue"
    )
    parser.add_argument(
        "--export", choices=["json", "csv"], help="Export venues to file"
    )
    parser.add_argument("--search", type=str, help="Run ad-hoc search query")
    parser.add_argument(
        "--max-queries",
        type=int,
        default=20,
        help="Max queries for daily search (default: 20)",
    )
    parser.add_argument(
        "--exclude",
        nargs=2,
        metavar=("NAME", "CITY"),
        help="Exclude a venue from searches",
    )
    parser.add_argument(
        "--exclude-reason",
        type=str,
        default="no_response",
        choices=["no_response", "bad_experience", "closed", "not_booking", "wrong_fit"],
        help="Reason for exclusion",
    )
    parser.add_argument("--exclude-notes", type=str, help="Notes for exclusion")
    parser.add_argument(
        "--unexclude",
        nargs=2,
        metavar=("NAME", "CITY"),
        help="Remove a venue from exclusion list",
    )
    parser.add_argument(
        "--list-excluded", action="store_true", help="List all excluded venues"
    )

    args = parser.parse_args()

    # Load config
    config = load_config()

    if args.init_db:
        init_database()
    elif args.daily:
        run_daily_search(config, args.max_queries)
    elif args.weekly_report:
        generate_weekly_report(config)
    elif args.list_acts:
        list_acts(config)
    elif args.add_venue:
        add_venue_manual(config, args.add_venue[0], args.add_venue[1])
    elif args.export:
        export_venues(args.export)
    elif args.search:
        print(f"Ad-hoc search: {args.search}")
        print("(Integrate with web search API for live results)")
    elif args.exclude:
        exclude_venue(
            args.exclude[0], args.exclude[1], args.exclude_reason, args.exclude_notes
        )
    elif args.unexclude:
        unexclude_venue(args.unexclude[0], args.unexclude[1])
    elif args.list_excluded:
        list_excluded_venues()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
