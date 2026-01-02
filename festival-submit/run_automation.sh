#!/bin/bash
# Festival Submit - Automation Runner
# Add to crontab: 0 9 * * * /path/to/run_automation.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/run_$(date +%Y-%m-%d_%H%M%S).log"

echo "=== Festival Submit Automation ===" | tee "$LOG_FILE"
echo "Started: $(date)" | tee -a "$LOG_FILE"

# Run scheduler
echo "Running scheduler..." | tee -a "$LOG_FILE"
python3 scheduler.py --all 2>&1 | tee -a "$LOG_FILE"

# Run notifications
echo "Running notifications..." | tee -a "$LOG_FILE"
python3 notifications.py --check 2>&1 | tee -a "$LOG_FILE"

echo "Completed: $(date)" | tee -a "$LOG_FILE"

# Cleanup old logs (30 days)
find "$LOG_DIR" -name "run_*.log" -mtime +30 -delete 2>/dev/null || true
