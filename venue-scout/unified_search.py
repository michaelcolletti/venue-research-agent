#!/usr/bin/env python3
"""
Venue Scout - Multi-Provider Search Integration

Executes venue searches using configurable LLM providers:
- Claude (Anthropic) with native web search
- OpenRouter with multiple models and web search via Exa.ai
- Ollama for local/private searches
- MCP for universal web search with any LLM

Usage:
    python unified_search.py --daily                      # Use configured provider
    python unified_search.py --daily --provider claude    # Specify provider
    python unified_search.py --daily --provider openrouter
    python unified_search.py --query "..." --provider ollama
    python unified_search.py --list-providers             # List available providers
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
import tomllib

from providers import create_provider, list_providers

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config" / "venues.toml"
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = DATA_DIR / "search_results"


def load_config() -> dict:
    """Load configuration from venues.toml"""
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def build_search_queries(config: dict, limit: int = 10) -> list[dict]:
    """
    Build prioritized search queries from config.

    This function is identical to the one in claude_search.py to maintain compatibility.
    """
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


def execute_searches(provider, config: dict, max_queries: int) -> Path:
    """
    Execute searches using the given provider.

    Args:
        provider: SearchProvider instance
        config: Configuration dict
        max_queries: Maximum number of queries to execute

    Returns:
        Path to results file
    """
    print(f"\n{'='*60}")
    print(f"VENUE SCOUT - Multi-Provider Search")
    print(f"Provider: {provider.get_provider_name().title()}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    queries = build_search_queries(config, max_queries)
    print(f"Running {len(queries)} searches...\n")

    results = []

    for i, q in enumerate(queries, 1):
        print(f"[{i}/{len(queries)}] Searching: {q['query'][:50]}...")

        result = provider.search(q["query"], q)
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
        "provider": provider.get_provider_name(),
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


def run_daily_searches(
    config: dict, max_queries: int = 10, provider_name: str = None
) -> Path:
    """
    Run daily search batch using specified or configured provider.

    Args:
        config: Configuration dict
        max_queries: Maximum number of queries
        provider_name: Provider to use (None = use configured default)

    Returns:
        Path to results file
    """
    # Get provider configuration
    provider_config = config.get("search_provider", {})
    provider_name = provider_name or provider_config.get("default_provider", "claude")
    fallback_providers = provider_config.get("fallback_providers", [])

    # Try primary provider
    try:
        print(f"\nInitializing provider: {provider_name}")
        provider = create_provider(provider_name, config)

        if not provider.validate_config():
            raise RuntimeError(f"{provider_name} configuration validation failed")

        return execute_searches(provider, config, max_queries)

    except Exception as e:
        print(f"\n⚠️  Provider '{provider_name}' failed: {e}")

        # Try fallback providers
        for fallback_name in fallback_providers:
            try:
                print(f"\n🔄 Trying fallback provider: {fallback_name}")
                provider = create_provider(fallback_name, config)

                if provider.validate_config():
                    return execute_searches(provider, config, max_queries)

            except Exception as fallback_error:
                print(f"⚠️  Fallback '{fallback_name}' failed: {fallback_error}")

        # All providers failed
        print("\n" + "=" * 60)
        print("ERROR: All providers failed")
        print("=" * 60)
        print("\nTroubleshooting:")
        print("1. Check that required environment variables are set")
        print("2. Verify API keys are valid")
        print("3. For Ollama, ensure the service is running")
        print("4. For MCP, ensure MCP servers are installed")
        print("\nSee CLAUDE.md for setup instructions")
        sys.exit(1)


def single_search(query: str, provider_name: str = None):
    """Run a single ad-hoc search."""
    config = load_config()
    provider_config = config.get("search_provider", {})
    provider_name = provider_name or provider_config.get("default_provider", "claude")

    try:
        print(f"\nInitializing provider: {provider_name}")
        provider = create_provider(provider_name, config)

        if not provider.validate_config():
            print(f"Error: {provider_name} configuration validation failed")
            sys.exit(1)

        print(f"\n🔍 Searching with {provider_name}: {query}\n")

        result = provider.search(query, {"query": query, "type": "adhoc"})

        if result["success"]:
            print(result["text"])
        else:
            print(f"Error: {result.get('error')}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Venue Scout Multi-Provider Search Integration"
    )
    parser.add_argument("--daily", action="store_true", help="Run daily search batch")
    parser.add_argument("--query", type=str, help="Run single search query")
    parser.add_argument(
        "--provider",
        type=str,
        help="Provider to use (claude, openrouter, ollama, mcp)",
    )
    parser.add_argument(
        "--max-queries", type=int, default=10, help="Max queries for daily run"
    )
    parser.add_argument(
        "--list-providers", action="store_true", help="List available providers"
    )

    args = parser.parse_args()

    # List providers
    if args.list_providers:
        print("\nAvailable Providers:")
        for provider in list_providers():
            print(f"  - {provider}")
        print("\nUse --provider <name> to specify a provider")
        return

    config = load_config()

    # Run daily searches
    if args.daily:
        run_daily_searches(config, args.max_queries, args.provider)

    # Run single query
    elif args.query:
        single_search(args.query, args.provider)

    # Show help and setup instructions
    else:
        parser.print_help()
        print("\n" + "=" * 60)
        print("SETUP INSTRUCTIONS")
        print("=" * 60)
        print(
            """
1. Choose a provider and set up API keys:

   Claude (Anthropic):
     export ANTHROPIC_API_KEY='sk-ant-...'

   OpenRouter (free tier available):
     export OPENROUTER_API_KEY='sk-or-...'

   Ollama (local, free):
     # Install from https://ollama.ai/
     ollama pull llama3.1:latest
     ollama serve

   MCP (Model Context Protocol):
     # Requires MCP server + LLM API key
     npm install -g web-search-mcp
     export ANTHROPIC_API_KEY='sk-ant-...'  # or other LLM key

2. Optionally configure provider in config/venues.toml:

   [search_provider]
   default_provider = "claude"  # or openrouter, ollama, mcp
   fallback_providers = ["openrouter", "ollama"]

3. Run daily searches:
   python unified_search.py --daily

   Or specify provider:
   python unified_search.py --daily --provider openrouter

4. Process results:
   python search_runner.py --process data/search_results/daily_*.json

5. Generate weekly report:
   python venue_scout.py --weekly-report

For more details, see CLAUDE.md
"""
        )


if __name__ == "__main__":
    main()
