# Venue Scout Makefile
# Performance venue research and tracking system

.PHONY: help install install-dev install-wizard setup clean clean-all \
        init-db daily search weekly-report list-acts export test wizard \
        install-core run-daily run-claude process-results

# Configuration
PYTHON := python3
PIP := $(PYTHON) -m pip
VENV := venv
VENV_BIN := $(VENV)/bin
VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip

# Directories
DATA_DIR := data
CONFIG_DIR := config
REPORTS_DIR := reports
LOGS_DIR := logs

# Default target
help:
	@echo "═══════════════════════════════════════════════════════════"
	@echo "🎵 Venue Scout - Performance Venue Research System"
	@echo "═══════════════════════════════════════════════════════════"
	@echo ""
	@echo "📦 Installation & Setup:"
	@echo "  make install          - Install core dependencies"
	@echo "  make install-wizard   - Install setup wizard dependencies"
	@echo "  make install-dev      - Install all dependencies including dev tools"
	@echo "  make venv             - Create virtual environment"
	@echo "  make setup            - Full setup (venv + install + init-db)"
	@echo "  make clean            - Remove generated files and caches"
	@echo "  make clean-all        - Remove everything including venv and database"
	@echo ""
	@echo "🎸 Setup Wizard:"
	@echo "  make wizard           - Run interactive web-based setup wizard"
	@echo ""
	@echo "💾 Database:"
	@echo "  make init-db          - Initialize/reset database"
	@echo "  make list-acts        - List configured acts"
	@echo "  make export-json      - Export venues to JSON"
	@echo "  make export-csv       - Export venues to CSV"
	@echo "  make list-excluded    - List excluded venues"
	@echo ""
	@echo "🔍 Search & Research:"
	@echo "  make daily            - Run daily search (generates queries)"
	@echo "  make run-claude       - Run searches via Claude API"
	@echo "  make process          - Process latest search results"
	@echo "  make search Q='...'   - Run ad-hoc search query"
	@echo ""
	@echo "📊 Reports:"
	@echo "  make weekly-report    - Generate weekly venue report"
	@echo "  make view-latest      - View latest weekly report"
	@echo ""
	@echo "🤖 Automation:"
	@echo "  make setup-cron       - Generate cron automation script"
	@echo "  make run-daily        - Run complete daily workflow"
	@echo ""
	@echo "🧪 Development:"
	@echo "  make test             - Run tests"
	@echo "  make lint             - Run linters"
	@echo "  make format           - Format code with black"
	@echo ""
	@echo "Environment: ANTHROPIC_API_KEY must be set for Claude searches"
	@echo "═══════════════════════════════════════════════════════════"

# Virtual environment setup
$(VENV):
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	@echo "✓ Virtual environment created at $(VENV)/"
	@echo "  Activate with: source $(VENV)/bin/activate"

venv: $(VENV)

# Installation targets
install-core: $(VENV)
	@echo "Installing core dependencies..."
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install anthropic
	@echo "✓ Core dependencies installed"

install-wizard: $(VENV)
	@echo "Installing setup wizard dependencies..."
	$(VENV_PIP) install flask uszipcode
	@echo "✓ Setup wizard dependencies installed"

install: $(VENV)
	@echo "Installing all runtime dependencies..."
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r ../requirements.txt
	@echo "✓ All dependencies installed"

install-dev: install
	@echo "Installing development dependencies..."
	$(VENV_PIP) install pytest black flake8
	@echo "✓ Development dependencies installed"

# Full setup
setup: venv install init-db
	@echo ""
	@echo "✓ Setup complete!"
	@echo "  Next steps:"
	@echo "    1. Activate venv: source $(VENV)/bin/activate"
	@echo "    2. Set API key: export ANTHROPIC_API_KEY='sk-ant-...'"
	@echo "    3. Run wizard:  make wizard"
	@echo "    4. Or run manually: make daily"

# Setup wizard
wizard: $(VENV)
	@echo "Starting setup wizard..."
	$(VENV_PYTHON) setup_wizard.py

# Database operations
init-db: $(VENV)
	@echo "Initializing database..."
	@mkdir -p $(DATA_DIR) $(REPORTS_DIR) $(LOGS_DIR)
	$(VENV_PYTHON) venue_scout.py --init-db
	@echo "✓ Database initialized"

list-acts: $(VENV)
	@$(VENV_PYTHON) venue_scout.py --list-acts

export-json: $(VENV)
	@echo "Exporting venues to JSON..."
	@$(VENV_PYTHON) venue_scout.py --export json

export-csv: $(VENV)
	@echo "Exporting venues to CSV..."
	@$(VENV_PYTHON) venue_scout.py --export csv

list-excluded: $(VENV)
	@$(VENV_PYTHON) venue_scout.py --list-excluded

# Search operations
daily: $(VENV)
	@echo "Running daily search query generation..."
	@$(VENV_PYTHON) venue_scout.py --daily --max-queries 20

run-claude: $(VENV)
	@if [ -z "$$ANTHROPIC_API_KEY" ]; then \
		echo "❌ Error: ANTHROPIC_API_KEY not set"; \
		echo "   Set with: export ANTHROPIC_API_KEY='sk-ant-...'"; \
		exit 1; \
	fi
	@echo "Running Claude API searches..."
	@$(VENV_PYTHON) claude_search.py --daily --max-queries 15

search: $(VENV)
	@if [ -z "$(Q)" ]; then \
		echo "Usage: make search Q='your search query'"; \
		exit 1; \
	fi
	@$(VENV_PYTHON) claude_search.py --query "$(Q)"

process: $(VENV)
	@echo "Processing latest search results..."
	@LATEST=$$(ls -t $(DATA_DIR)/search_results/daily_*.json 2>/dev/null | head -n1); \
	if [ -n "$$LATEST" ]; then \
		echo "Processing: $$LATEST"; \
		$(VENV_PYTHON) search_runner.py --process "$$LATEST"; \
	else \
		echo "No search results found in $(DATA_DIR)/search_results/"; \
	fi

# Complete daily workflow
run-daily: run-claude process
	@echo ""
	@echo "✓ Daily workflow complete"
	@echo "  Run 'make weekly-report' on Sunday to generate summary"

# Reports
weekly-report: $(VENV)
	@echo "Generating weekly report..."
	@$(VENV_PYTHON) venue_scout.py --weekly-report

view-latest:
	@LATEST=$$(ls -t $(REPORTS_DIR)/weekly_report_*.md 2>/dev/null | head -n1); \
	if [ -n "$$LATEST" ]; then \
		echo "Latest report: $$LATEST"; \
		echo ""; \
		cat "$$LATEST"; \
	else \
		echo "No reports found in $(REPORTS_DIR)/"; \
	fi

# Automation
setup-cron: $(VENV)
	@echo "Generating cron automation script..."
	@$(VENV_PYTHON) search_runner.py --setup-cron
	@echo ""
	@echo "To schedule daily runs:"
	@echo "  crontab -e"
	@echo "  # Add: 0 6 * * * $(PWD)/run_daily.sh"

# Development
test: $(VENV)
	@echo "Running tests..."
	@if [ -d "tests" ]; then \
		$(VENV_PYTHON) -m pytest tests/ -v; \
	else \
		echo "No tests directory found"; \
	fi

lint: $(VENV)
	@echo "Running linters..."
	@$(VENV_BIN)/flake8 *.py || true

format: $(VENV)
	@echo "Formatting code with black..."
	@$(VENV_BIN)/black *.py utils/*.py || true

# Sample data for testing
sample: $(VENV)
	@echo "Creating sample search results..."
	@$(VENV_PYTHON) search_runner.py --sample

# Cleanup
clean:
	@echo "Cleaning generated files..."
	@rm -rf __pycache__ utils/__pycache__
	@rm -f *.pyc utils/*.pyc
	@rm -rf .pytest_cache
	@rm -rf *.egg-info
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Cleaned"

clean-all: clean
	@echo "Removing virtual environment and database..."
	@rm -rf $(VENV)
	@rm -rf $(DATA_DIR)/*.db
	@rm -rf $(DATA_DIR)/queries_*.json
	@echo "✓ Full cleanup complete"
	@echo "  Run 'make setup' to start fresh"

# Exclude venue
exclude:
	@if [ -z "$(NAME)" ] || [ -z "$(CITY)" ]; then \
		echo "Usage: make exclude NAME='Venue Name' CITY='City' REASON='no_response' NOTES='Your notes'"; \
		exit 1; \
	fi
	@$(VENV_PYTHON) venue_scout.py --exclude "$(NAME)" "$(CITY)" \
		--exclude-reason "$(or $(REASON),no_response)" \
		$(if $(NOTES),--exclude-notes "$(NOTES)")

# Add venue manually
add-venue:
	@if [ -z "$(NAME)" ] || [ -z "$(CITY)" ]; then \
		echo "Usage: make add-venue NAME='Venue Name' CITY='City'"; \
		exit 1; \
	fi
	@$(VENV_PYTHON) venue_scout.py --add-venue "$(NAME)" "$(CITY)"
