#!/usr/bin/env python3
"""
Venue Scout - Claude API Integration

Executes venue searches using Claude API with web search capability.
Requires: ANTHROPIC_API_KEY environment variable

Usage:
    python claude_search.py --daily       # Run daily searches via Claude
    python claude_search.py --query "..."  # Single query
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
import tomllib

try:
    from anthropic import Anthropic
except ImportError:
    print("Install anthropic: pip install anthropic")
    sys.exit(1)

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config" / "venues.toml"
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = DATA_DIR / "search_results"


def load_config() -> dict:
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def build_search_queries(config: dict, limit: int = 10) -> list[dict]:
    """Build prioritized search queries from config."""
    queries = []
    templates = config.get("search_templates", {})
    regions = config.get("regions", {})

    for region_key, region_data in regions.items():
        region_name = region_data.get("name", region_key)
        priority = region_data.get("priority", 5)
        cities = region_data.get("cities", [])[:3]  # Top 3 cities per region

        for city in cities:
            # Focus on most valuable query types
            for template_type in ["new_venues", "booking_opportunities"]:
                template_list = templates.get(template_type, [])
                if template_list:
                    query = template_list[0].format(city=city, region=region_name)
                    queries.append(
                        {
                            "query": query,
                            "type": template_type,
                            "region": region_name,
                            "city": city,
                            "priority": priority,
                        }
                    )

    queries.sort(key=lambda x: x["priority"])
    return queries[:limit]


def search_with_claude(client: Anthropic, query: str, query_info: dict) -> dict:
    """Execute a single search using Claude with web search tool."""

    system_prompt = """You are a venue research assistant helping a musician find
performance venues. When searching, focus on:
- Live music venues, bars, restaurants with live music
- Capacity and venue type when available
- Booking contact information if found
- Any mentions of venues seeking musicians

Format your findings as structured data."""

    user_message = f"""Search for: {query}

After searching, provide a structured summary of venues found with:
1. Venue name
2. City/Location  
3. Venue type (bar, restaurant, theater, etc.)
4. Any booking/contact info found
5. Notable details (capacity, genres, etc.)

Also note any opportunities where venues are actively seeking musicians."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": user_message}],
        )

        # Extract text content from response
        result_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                result_text += block.text

        return {
            "query_info": query_info,
            "text": result_text,
            "success": True,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "query_info": query_info,
            "text": "",
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


def run_daily_searches(config: dict, max_queries: int = 10):
    """Run the daily search batch via Claude API."""

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("\nTo set up:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    client = Anthropic(api_key=api_key)

    print(f"\n{'='*60}")
    print(f"VENUE SCOUT - Claude API Daily Search")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    queries = build_search_queries(config, max_queries)
    print(f"Running {len(queries)} searches...\n")

    results = []

    for i, q in enumerate(queries, 1):
        print(f"[{i}/{len(queries)}] Searching: {q['query'][:50]}...")

        result = search_with_claude(client, q["query"], q)
        results.append(result)

        if result["success"]:
            print(f"    ✓ Complete ({len(result['text'])} chars)")
        else:
            print(f"    ✗ Error: {result.get('error', 'Unknown')}")

    # Save results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results_file = RESULTS_DIR / f"daily_{datetime.now().strftime('%Y%m%d_%H%M')}.json"

    output_data = {
        "date": datetime.now().isoformat(),
        "queries_run": len(queries),
        "successful": sum(1 for r in results if r["success"]),
        "results": results,
    }

    with open(results_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Results saved to: {results_file}")
    print(f"Successful: {output_data['successful']}/{output_data['queries_run']}")
    print(f"\nNext step: python search_runner.py --process {results_file}")

    return results_file


def single_search(query: str):
    """Run a single ad-hoc search."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    client = Anthropic(api_key=api_key)

    print(f"\n🔍 Searching: {query}\n")

    result = search_with_claude(client, query, {"query": query, "type": "adhoc"})

    if result["success"]:
        print(result["text"])
    else:
        print(f"Error: {result.get('error')}")


def main():
    parser = argparse.ArgumentParser(description="Venue Scout Claude API Integration")
    parser.add_argument("--daily", action="store_true", help="Run daily search batch")
    parser.add_argument("--query", type=str, help="Run single search query")
    parser.add_argument(
        "--max-queries", type=int, default=10, help="Max queries for daily run"
    )

    args = parser.parse_args()
    config = load_config()

    if args.daily:
        run_daily_searches(config, args.max_queries)
    elif args.query:
        single_search(args.query)
    else:
        parser.print_help()
        print("\n" + "=" * 60)
        print("SETUP INSTRUCTIONS")
        print("=" * 60)
        print(
            """
1. Set your Anthropic API key:
   export ANTHROPIC_API_KEY='sk-ant-...'

2. Install dependencies:
   pip install anthropic

3. Run daily searches:
   python claude_search.py --daily

4. Process results:
   python search_runner.py --process data/search_results/daily_*.json

5. Generate weekly report:
   python venue_scout.py --weekly-report
"""
        )


if __name__ == "__main__":
    main()
