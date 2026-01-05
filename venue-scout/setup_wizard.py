#!/usr/bin/env python3
"""
Venue Scout Setup Wizard
User-friendly web interface for configuring venue-scout
"""

import os
import sys
import json
import shutil
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify

try:
    from uszipcode import SearchEngine
except ImportError:
    print("Error: uszipcode not installed")
    print("Install with: pip install uszipcode")
    sys.exit(1)

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))
from utils.config_generator import (
    generate_venues_toml,
    validate_settings,
    validate_act_profile
)

# Configuration
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config" / "venues.toml"
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Initialize Flask app
app = Flask(__name__,
           template_folder=str(TEMPLATE_DIR),
           static_folder=str(STATIC_DIR))

# Initialize zip code search engine
search_engine = SearchEngine()


@app.route('/')
def index():
    """Serve the main wizard page."""
    return render_template('wizard.html')


@app.route('/api/lookup-zip', methods=['POST'])
def lookup_zip():
    """
    Look up zip code and return location information.

    Expected POST data:
        {
            "zipcode": "12498",
            "radius": 75
        }

    Returns:
        {
            "success": true,
            "city": "Woodstock",
            "county": "Ulster",
            "state": "NY",
            "lat": 42.04,
            "lng": -74.11,
            "nearby_cities": ["Kingston", "Woodstock", ...]
        }
    """
    try:
        data = request.get_json()
        zipcode = data.get('zipcode', '').strip()
        radius = int(data.get('radius', 75))

        if not zipcode or not zipcode.isdigit() or len(zipcode) != 5:
            return jsonify({
                'success': False,
                'error': 'Invalid zip code format (must be 5 digits)'
            })

        # Lookup zip code
        result = search_engine.by_zipcode(zipcode)

        if not result:
            return jsonify({
                'success': False,
                'error': 'Zip code not found'
            })

        # Validate NY state only
        if result.state != 'NY':
            return jsonify({
                'success': False,
                'error': f'Only NY state is supported (detected: {result.state})'
            })

        # Get nearby cities
        nearby_cities = get_nearby_cities(result.lat, result.lng, radius)

        return jsonify({
            'success': True,
            'city': result.major_city or result.post_office_city,
            'county': result.county,
            'state': result.state,
            'lat': result.lat,
            'lng': result.lng,
            'nearby_cities': nearby_cities
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


def get_nearby_cities(lat, lng, radius_miles):
    """
    Find all NY cities within radius of given coordinates.

    Args:
        lat: Latitude
        lng: Longitude
        radius_miles: Search radius in miles

    Returns:
        List of dicts with city and county information
    """
    try:
        # Search for nearby zip codes
        nearby_zips = search_engine.by_coordinates(
            lat=lat,
            lng=lng,
            radius=radius_miles,
            returns=1000  # Get many results, we'll filter
        )

        # Extract unique cities in NY
        cities_map = {}  # city -> {county, ...}

        for zip_result in nearby_zips:
            if zip_result.state != 'NY':
                continue

            city = zip_result.major_city or zip_result.post_office_city
            county = zip_result.county

            if city and city not in cities_map:
                cities_map[city] = {
                    'city': city,
                    'county': county
                }

        # Convert to sorted list
        cities_list = sorted(cities_map.values(), key=lambda x: x['city'])

        return cities_list

    except Exception as e:
        print(f"Error finding nearby cities: {e}")
        return []


@app.route('/api/preview-config', methods=['POST'])
def preview_config():
    """
    Generate and return preview of TOML configuration.

    Expected POST data: Complete form data structure
    Returns: TOML configuration string
    """
    try:
        form_data = request.get_json()

        # Validate form data
        valid, error = validate_form_data(form_data)
        if not valid:
            return jsonify({
                'success': False,
                'error': error
            })

        # Generate TOML
        toml_content = generate_venues_toml(form_data)

        return jsonify({
            'success': True,
            'config': toml_content
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error generating config: {str(e)}'
        })


@app.route('/api/save-config', methods=['POST'])
def save_config():
    """
    Save configuration and optionally initialize database.

    Expected POST data:
        {
            ... form data ...,
            "init_db": true/false
        }

    Returns:
        {
            "success": true,
            "message": "Configuration saved successfully",
            "config_path": "/path/to/venues.toml",
            "backup_path": "/path/to/backup" (if backup created)
        }
    """
    try:
        form_data = request.get_json()

        # Validate form data
        valid, error = validate_form_data(form_data)
        if not valid:
            return jsonify({
                'success': False,
                'error': error
            })

        # Generate TOML
        toml_content = generate_venues_toml(form_data)

        # Ensure config directory exists
        config_dir = CONFIG_PATH.parent
        config_dir.mkdir(parents=True, exist_ok=True)

        # Backup existing config if it exists
        backup_path = None
        if CONFIG_PATH.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = CONFIG_PATH.parent / f"venues.toml.backup_{timestamp}"
            shutil.copy2(CONFIG_PATH, backup_path)

        # Save new configuration
        with open(CONFIG_PATH, 'w') as f:
            f.write(toml_content)

        # Initialize database if requested
        db_initialized = False
        db_error = None
        if form_data.get('init_db', False):
            try:
                # Ensure data, reports, and logs directories exist
                (BASE_DIR / 'data').mkdir(exist_ok=True)
                (BASE_DIR / 'reports').mkdir(exist_ok=True)
                (BASE_DIR / 'logs').mkdir(exist_ok=True)

                # Run venue_scout.py --init-db
                result = subprocess.run(
                    [sys.executable, str(BASE_DIR / 'venue_scout.py'), '--init-db'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    db_initialized = True
                else:
                    db_error = result.stderr or "Unknown error initializing database"

            except subprocess.TimeoutExpired:
                db_error = "Database initialization timed out"
            except Exception as e:
                db_error = str(e)

        response_data = {
            'success': True,
            'message': 'Configuration saved successfully!',
            'config_path': str(CONFIG_PATH),
            'db_initialized': db_initialized
        }

        if backup_path:
            response_data['backup_path'] = str(backup_path)

        if db_error:
            response_data['db_error'] = db_error

        return jsonify(response_data)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error saving configuration: {str(e)}'
        })


def validate_form_data(form_data):
    """
    Validate complete form data.

    Returns:
        tuple: (success: bool, error_message: str)
    """
    # Validate settings
    valid, error = validate_settings(form_data)
    if not valid:
        return False, f"Settings error: {error}"

    # Validate at least one act
    acts = form_data.get('acts', [])
    if not acts or len(acts) == 0:
        return False, "At least one act profile is required"

    # Validate each act
    for i, act in enumerate(acts):
        valid, error = validate_act_profile(act)
        if not valid:
            return False, f"Act #{i+1} error: {error}"

    # Validate cities
    cities_with_counties = form_data.get('cities_with_counties', [])
    if not cities_with_counties or len(cities_with_counties) == 0:
        return False, "At least one city must be selected"

    return True, ""


def main():
    """Run the setup wizard web server."""
    print("\n" + "="*60)
    print("VENUE SCOUT - Setup Wizard")
    print("="*60)
    print("\nStarting web server...")
    print("\nThe wizard will open in your browser at:")
    print("  http://localhost:5000")
    print("\nPress Ctrl+C to stop the server when done.")
    print("="*60 + "\n")

    # Open browser after a short delay
    import threading
    def open_browser():
        import time
        time.sleep(1.5)
        try:
            webbrowser.open('http://localhost:5000')
        except:
            pass

    threading.Thread(target=open_browser, daemon=True).start()

    # Run Flask app
    app.run(host='localhost', port=5000, debug=False)


if __name__ == '__main__':
    main()
