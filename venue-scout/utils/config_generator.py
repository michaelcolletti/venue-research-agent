#!/usr/bin/env python3
"""
Configuration Generator for Venue Scout
Generates venues.toml from wizard form data
"""

from datetime import datetime
from typing import Any, Dict, List


# County to region mapping based on existing config
COUNTY_TO_REGION = {
    # Hudson Valley
    "Ulster": ("hudson_valley", "Hudson Valley", 1),
    "Dutchess": ("hudson_valley", "Hudson Valley", 1),
    "Columbia": ("hudson_valley", "Hudson Valley", 1),
    "Greene": ("hudson_valley", "Hudson Valley", 1),
    "Orange": ("hudson_valley", "Hudson Valley", 1),
    "Sullivan": ("hudson_valley", "Hudson Valley", 1),

    # Capital District
    "Albany": ("capital_district", "Capital District", 2),
    "Schenectady": ("capital_district", "Capital District", 2),
    "Rensselaer": ("capital_district", "Capital District", 2),
    "Saratoga": ("capital_district", "Capital District", 2),

    # Catskills
    "Delaware": ("catskills", "Catskills", 1),

    # NYC Metro
    "Westchester": ("nyc_metro", "NYC Metro", 3),
    "Rockland": ("nyc_metro", "NYC Metro", 3),
    "Putnam": ("nyc_metro", "NYC Metro", 3),
}


def format_toml_array(items: List[str]) -> str:
    """Format a Python list as a TOML array string."""
    if not items:
        return "[]"
    # Escape quotes in items and format
    escaped_items = [item.replace('"', '\\"') for item in items]
    return '[' + ', '.join(f'"{item}"' for item in escaped_items) + ']'


def format_toml_string(value: str) -> str:
    """Format a string value for TOML, escaping quotes."""
    return value.replace('"', '\\"')


def validate_settings(data: Dict[str, Any]) -> tuple[bool, str]:
    """Validate settings section data."""
    required_fields = ['zip_code', 'base_region', 'radius']

    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Missing required field: {field}"

    # Validate zip code format
    if not data['zip_code'].isdigit() or len(data['zip_code']) != 5:
        return False, "Invalid zip code format (must be 5 digits)"

    # Validate radius
    try:
        radius = int(data['radius'])
        if radius < 10 or radius > 200:
            return False, "Radius must be between 10 and 200 miles"
    except (ValueError, TypeError):
        return False, "Invalid radius value"

    return True, ""


def validate_act_profile(data: Dict[str, Any]) -> tuple[bool, str]:
    """Validate act profile data."""
    required_fields = ['name', 'genres', 'members', 'min_capacity', 'max_capacity',
                      'ideal_capacity', 'min_fee', 'max_fee', 'venue_types', 'available_days']

    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"

    # Validate name
    if not data['name'] or not data['name'].strip():
        return False, "Act name cannot be empty"

    # Validate arrays
    if not data['genres'] or len(data['genres']) == 0:
        return False, "At least one genre must be selected"

    if not data['venue_types'] or len(data['venue_types']) == 0:
        return False, "At least one venue type must be selected"

    if not data['available_days'] or len(data['available_days']) == 0:
        return False, "At least one available day must be selected"

    # Validate numeric fields
    try:
        members = int(data['members'])
        if members < 1:
            return False, "Members must be at least 1"
    except (ValueError, TypeError):
        return False, "Invalid members count"

    try:
        min_cap = int(data['min_capacity'])
        max_cap = int(data['max_capacity'])
        ideal_cap = int(data['ideal_capacity'])

        if min_cap < 0 or max_cap < 0 or ideal_cap < 0:
            return False, "Capacity values must be positive"

        if min_cap > max_cap:
            return False, "Min capacity cannot exceed max capacity"

        if ideal_cap < min_cap or ideal_cap > max_cap:
            return False, "Ideal capacity must be between min and max"
    except (ValueError, TypeError):
        return False, "Invalid capacity values"

    try:
        min_fee = int(data['min_fee'])
        max_fee = int(data['max_fee'])

        if min_fee < 0 or max_fee < 0:
            return False, "Fee values must be positive"

        if min_fee > max_fee:
            return False, "Min fee cannot exceed max fee"
    except (ValueError, TypeError):
        return False, "Invalid fee values"

    return True, ""


def detect_regions(cities_with_counties: List[Dict[str, str]]) -> Dict[str, Dict]:
    """
    Detect regions based on cities and their counties.

    Args:
        cities_with_counties: List of dicts with 'city' and 'county' keys

    Returns:
        Dict mapping region keys to region data
    """
    regions = {}

    for item in cities_with_counties:
        city = item.get('city')
        county = item.get('county')

        if not city:
            continue

        # Get region info from county mapping
        if county in COUNTY_TO_REGION:
            region_key, region_name, priority = COUNTY_TO_REGION[county]
        else:
            # Default to custom region
            region_key = "custom_region"
            region_name = "Custom Region"
            priority = 5

        # Initialize region if not exists
        if region_key not in regions:
            regions[region_key] = {
                'name': region_name,
                'counties': set(),
                'cities': [],
                'priority': priority
            }

        # Add city and county to region
        if city not in regions[region_key]['cities']:
            regions[region_key]['cities'].append(city)

        if county:
            regions[region_key]['counties'].add(county)

    # Convert sets to sorted lists
    for region_data in regions.values():
        region_data['counties'] = sorted(region_data['counties'])

    return regions


def generate_venues_toml(form_data: Dict[str, Any]) -> str:
    """
    Generate a complete venues.toml configuration from form data.

    Args:
        form_data: Dictionary containing wizard form data

    Returns:
        String containing the complete TOML configuration
    """
    toml_lines = []

    # Header comment
    toml_lines.append("# Venue Scout Configuration")
    toml_lines.append(f"# Generated by Setup Wizard on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    toml_lines.append("")

    # ========================================================================
    # Settings Section
    # ========================================================================
    toml_lines.append("# ============================================================================")
    toml_lines.append("# SETTINGS")
    toml_lines.append("# ============================================================================")
    toml_lines.append("")
    toml_lines.append("[settings]")
    toml_lines.append(f'default_radius_miles = {form_data["radius"]}')
    toml_lines.append(f'base_zip = "{form_data["zip_code"]}"')
    toml_lines.append(f'base_region = "{format_toml_string(form_data["base_region"])}"')
    toml_lines.append('state = "NY"')
    toml_lines.append("keep_daily_results_days = 30")
    toml_lines.append('report_day = "sunday"')
    toml_lines.append('sources = ["google", "yelp", "songkick", "bandsintown", "local_news", "facebook_events"]')
    toml_lines.append("")

    # ========================================================================
    # Excluded Venues Section
    # ========================================================================
    toml_lines.append("# ============================================================================")
    toml_lines.append("# EXCLUDED VENUES")
    toml_lines.append("# Add venues you don't want to contact using --exclude command")
    toml_lines.append("# ============================================================================")
    toml_lines.append("")
    toml_lines.append("[excluded]")
    toml_lines.append("")

    # ========================================================================
    # Acts Section
    # ========================================================================
    toml_lines.append("# ============================================================================")
    toml_lines.append("# ACT PROFILES")
    toml_lines.append("# ============================================================================")
    toml_lines.append("")

    for act in form_data.get('acts', []):
        # Generate act key from name
        act_key = act['name'].lower().replace(' ', '_').replace('-', '_')
        # Remove special characters
        act_key = ''.join(c for c in act_key if c.isalnum() or c == '_')

        toml_lines.append(f"[acts.{act_key}]")
        toml_lines.append(f'name = "{format_toml_string(act["name"])}"')
        toml_lines.append(f'genres = {format_toml_array(act["genres"])}')
        toml_lines.append(f'min_capacity = {act["min_capacity"]}')
        toml_lines.append(f'max_capacity = {act["max_capacity"]}')
        toml_lines.append(f'ideal_capacity = {act["ideal_capacity"]}')

        # Use provided values or defaults
        requires_stage = act.get('requires_stage', True)
        requires_sound = act.get('requires_sound_system', True)
        set_length = act.get('set_length_hours', 2)

        toml_lines.append(f'requires_stage = {str(requires_stage).lower()}')
        toml_lines.append(f'requires_sound_system = {str(requires_sound).lower()}')
        toml_lines.append(f'set_length_hours = {set_length}')
        toml_lines.append(f'members = {act["members"]}')
        toml_lines.append(f'venue_types = {format_toml_array(act["venue_types"])}')
        toml_lines.append(f'available_days = {format_toml_array(act["available_days"])}')
        toml_lines.append(f'min_fee = {act["min_fee"]}')
        toml_lines.append(f'max_fee = {act["max_fee"]}')

        if act.get('notes'):
            toml_lines.append(f'notes = "{format_toml_string(act["notes"])}"')

        toml_lines.append("")

    # ========================================================================
    # Regions Section
    # ========================================================================
    toml_lines.append("# ============================================================================")
    toml_lines.append("# SEARCH REGIONS")
    toml_lines.append("# ============================================================================")
    toml_lines.append("")

    regions = detect_regions(form_data.get('cities_with_counties', []))

    for region_key, region_data in regions.items():
        toml_lines.append(f"[regions.{region_key}]")
        toml_lines.append(f'name = "{region_data["name"]}"')
        toml_lines.append(f'counties = {format_toml_array(region_data["counties"])}')
        toml_lines.append(f'cities = {format_toml_array(region_data["cities"])}')
        toml_lines.append(f'priority = {region_data["priority"]}')
        toml_lines.append("")

    # ========================================================================
    # Filters Section
    # ========================================================================
    toml_lines.append("# ============================================================================")
    toml_lines.append("# FILTERS & ALERTS")
    toml_lines.append("# ============================================================================")
    toml_lines.append("")
    toml_lines.append("[filters]")
    toml_lines.append('exclude_patterns = ["karaoke", "DJ only", "cover band only"]')
    toml_lines.append("prefer_original_music = true")
    toml_lines.append("min_rating = 3.5")
    toml_lines.append("")
    toml_lines.append("[alerts]")
    toml_lines.append("new_venue_opened = true")
    toml_lines.append('seeking_artists_keywords = ["booking live music", "seeking musicians", "looking for bands", "live music wanted", "now booking"]')
    toml_lines.append("capacity_threshold = 300")
    toml_lines.append("")

    # ========================================================================
    # Search Templates Section
    # ========================================================================
    toml_lines.append("# ============================================================================")
    toml_lines.append("# SEARCH TEMPLATES")
    toml_lines.append("# ============================================================================")
    toml_lines.append("")
    toml_lines.append("[search_templates]")
    toml_lines.append('new_venues = ["{city} NY new live music venue 2024 2025", "{city} NY brewery taproom live music"]')
    toml_lines.append('existing_venues = ["{city} NY live music venues", "{city} NY jazz clubs"]')
    toml_lines.append('booking_opportunities = ["{city} NY venues looking for musicians", "{region} NY booking live music"]')
    toml_lines.append("")

    return '\n'.join(toml_lines)
