#!/bin/bash
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
