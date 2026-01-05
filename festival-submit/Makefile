# Festival Submit Makefile
# Automated festival submission system for managing musical acts

.PHONY: help install install-dev setup clean clean-all venv \
        init acts festivals match submit status report calendar \
        templates render automation daily weekly check-deadlines \
        test lint format

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
EXPORTS_DIR := exports
SUBMISSIONS_DIR := submissions

# Default target
help:
	@echo "═══════════════════════════════════════════════════════════"
	@echo "🎪 Festival Submit - Festival Submission Automation"
	@echo "═══════════════════════════════════════════════════════════"
	@echo ""
	@echo "📦 Installation & Setup:"
	@echo "  make install          - Install dependencies"
	@echo "  make install-dev      - Install with dev tools"
	@echo "  make venv             - Create virtual environment"
	@echo "  make setup            - Full setup (venv + install + init)"
	@echo "  make clean            - Remove generated files"
	@echo "  make clean-all        - Remove everything including venv"
	@echo ""
	@echo "💾 Database & Configuration:"
	@echo "  make init             - Initialize database"
	@echo "  make acts             - List all configured acts"
	@echo "  make festivals        - List all festivals"
	@echo "  make templates        - List available templates"
	@echo ""
	@echo "🎯 Matching & Submission:"
	@echo "  make match ACT='...'  - Find matching festivals for act"
	@echo "  make submit           - Create submission (interactive)"
	@echo "  make status           - View submission status"
	@echo "  make status-act ACT='...' - View status for specific act"
	@echo ""
	@echo "📊 Reports & Calendar:"
	@echo "  make report-status    - Generate status report"
	@echo "  make report-opps      - Generate opportunities report"
	@echo "  make calendar         - Generate 12-month calendar"
	@echo "  make calendar-6       - Generate 6-month calendar"
	@echo ""
	@echo "✉️  Templates:"
	@echo "  make render ACT='...' FEST='...' TMPL='...' - Render template"
	@echo ""
	@echo "🤖 Automation:"
	@echo "  make automation       - Run all automation tasks"
	@echo "  make daily            - Run daily automation"
	@echo "  make weekly           - Run weekly automation"
	@echo "  make check-deadlines  - Check upcoming deadlines"
	@echo "  make setup-cron       - Setup cron automation"
	@echo ""
	@echo "🧪 Development:"
	@echo "  make test             - Run tests"
	@echo "  make lint             - Run linters"
	@echo "  make format           - Format code"
	@echo ""
	@echo "Examples:"
	@echo "  make match ACT='cloudburst'"
	@echo "  make render ACT='tree_of_life_trio' FEST='regional.saratoga_jazz' TMPL='festival_submission_jazz'"
	@echo "═══════════════════════════════════════════════════════════"

# Virtual environment setup
$(VENV):
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	@echo "✓ Virtual environment created at $(VENV)/"
	@echo "  Activate with: source $(VENV)/bin/activate"

venv: $(VENV)

# Installation

install: $(VENV)
	@echo "Installing dependencies..."
	$(VENV_PIP) install --upgrade pip
	@if [ -f requirements.txt ]; then \
		$(VENV_PIP) install -r requirements.txt; \
	fi
	@echo "✓ Dependencies installed"

install-dev: install
	@echo "Installing development dependencies..."
	$(VENV_PIP) install pytest black flake8
	@echo "✓ Development dependencies installed"

# Full setup
setup: venv install init
	@echo ""
	@echo "✓ Setup complete!"
	@echo "  Next steps:"
	@echo "    1. Activate venv: source $(VENV)/bin/activate"
	@echo "    2. Configure acts in config/acts.toml"
	@echo "    3. Configure festivals in config/festivals.toml"
	@echo "    4. Run: make acts"

# Database operations
init: $(VENV)
	@echo "Initializing database..."
	@mkdir -p $(DATA_DIR) $(REPORTS_DIR) $(LOGS_DIR) $(EXPORTS_DIR) $(SUBMISSIONS_DIR)
	$(VENV_PYTHON) festival_submit.py init
	@echo "✓ Database initialized"

acts: $(VENV)
	@$(VENV_PYTHON) festival_submit.py acts

festivals: $(VENV)
	@$(VENV_PYTHON) festival_submit.py festivals

templates: $(VENV)
	@$(VENV_PYTHON) festival_submit.py templates

# Matching and submission
match: $(VENV)
	@if [ -z "$(ACT)" ]; then \
		echo "Usage: make match ACT='act_id'"; \
		echo "Example: make match ACT='cloudburst'"; \
		exit 1; \
	fi
	@$(VENV_PYTHON) festival_submit.py match --act $(ACT)

submit: $(VENV)
	@if [ -z "$(ACT)" ] || [ -z "$(FEST)" ]; then \
		echo "Usage: make submit ACT='act_id' FEST='festival_id'"; \
		echo "Example: make submit ACT='tree_of_life_trio' FEST='regional.saratoga_jazz'"; \
		exit 1; \
	fi
	@$(VENV_PYTHON) festival_submit.py submit --act $(ACT) --festival $(FEST)

status: $(VENV)
	@$(VENV_PYTHON) festival_submit.py status

status-act: $(VENV)
	@if [ -z "$(ACT)" ]; then \
		echo "Usage: make status-act ACT='act_id'"; \
		exit 1; \
	fi
	@$(VENV_PYTHON) festival_submit.py status --act $(ACT)

# Reports
report-status: $(VENV)
	@echo "Generating status report..."
	@$(VENV_PYTHON) festival_submit.py report --type status

report-opps: $(VENV)
	@if [ -n "$(ACT)" ]; then \
		echo "Generating opportunities report for $(ACT)..."; \
		$(VENV_PYTHON) festival_submit.py report --type opportunities --act $(ACT); \
	else \
		echo "Generating opportunities report for all acts..."; \
		$(VENV_PYTHON) festival_submit.py report --type opportunities; \
	fi

calendar: $(VENV)
	@echo "Generating 12-month submission calendar..."
	@$(VENV_PYTHON) festival_submit.py calendar --months 12

calendar-6: $(VENV)
	@echo "Generating 6-month submission calendar..."
	@$(VENV_PYTHON) festival_submit.py calendar --months 6

view-latest-report:
	@LATEST=$$(ls -t $(REPORTS_DIR)/*.md 2>/dev/null | head -n1); \
	if [ -n "$$LATEST" ]; then \
		echo "Latest report: $$LATEST"; \
		echo ""; \
		cat "$$LATEST"; \
	else \
		echo "No reports found in $(REPORTS_DIR)/"; \
	fi

# Templates
render: $(VENV)
	@if [ -z "$(ACT)" ] || [ -z "$(FEST)" ] || [ -z "$(TMPL)" ]; then \
		echo "Usage: make render ACT='act_id' FEST='festival_id' TMPL='template_id'"; \
		echo "Example: make render ACT='tillson_jazz_ensemble' FEST='national.rochester_jazz' TMPL='festival_submission_jazz'"; \
		echo ""; \
		echo "Available templates:"; \
		$(VENV_PYTHON) festival_submit.py templates; \
		exit 1; \
	fi
	@$(VENV_PYTHON) festival_submit.py render --template $(TMPL) --act $(ACT) --festival $(FEST)

# Automation
automation: $(VENV)
	@echo "Running all automation tasks..."
	@$(VENV_PYTHON) scheduler.py --all
	@echo "✓ Automation complete"

daily: $(VENV)
	@echo "Running daily automation tasks..."
	@$(VENV_PYTHON) scheduler.py --daily
	@echo "✓ Daily tasks complete"

weekly: $(VENV)
	@echo "Running weekly automation tasks..."
	@$(VENV_PYTHON) scheduler.py --weekly
	@echo "✓ Weekly tasks complete"

check-deadlines: $(VENV)
	@echo "Checking upcoming deadlines..."
	@$(VENV_PYTHON) notifications.py --check

notify-digest: $(VENV)
	@if [ -z "$$SMTP_USER" ]; then \
		echo "⚠️  Email not configured. Set SMTP environment variables:"; \
		echo "   export SMTP_HOST='smtp.gmail.com'"; \
		echo "   export SMTP_PORT='587'"; \
		echo "   export SMTP_USER='your-email@gmail.com'"; \
		echo "   export SMTP_PASS='your-app-password'"; \
		echo "   export EMAIL_TO='notifications@example.com'"; \
		exit 1; \
	fi
	@echo "Sending email digest..."
	@$(VENV_PYTHON) notifications.py --digest

notify-test: $(VENV)
	@echo "Testing desktop notification..."
	@$(VENV_PYTHON) notifications.py --test

setup-cron:
	@echo "Setting up cron automation..."
	@chmod +x run_automation.sh
	@echo ""
	@echo "Add to crontab (crontab -e):"
	@echo ""
	@echo "# Daily at 9am"
	@echo "0 9 * * * $(PWD)/run_automation.sh"
	@echo ""
	@echo "# Weekly digest on Monday at 8am"
	@echo "0 8 * * 1 $(PWD)/run_automation.sh"
	@echo ""
	@echo "Shell script ready: $(PWD)/run_automation.sh"

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
	@$(VENV_BIN)/black *.py || true

# Utility commands
show-config:
	@echo "Configuration files:"
	@echo "  Acts:      $(CONFIG_DIR)/acts.toml"
	@echo "  Festivals: $(CONFIG_DIR)/festivals.toml"
	@echo "  Templates: $(CONFIG_DIR)/templates.toml"
	@echo ""
	@echo "Database:"
	@echo "  Location:  $(DATA_DIR)/submissions.db"
	@echo ""
	@echo "Directories:"
	@echo "  Reports:      $(REPORTS_DIR)/"
	@echo "  Exports:      $(EXPORTS_DIR)/"
	@echo "  Submissions:  $(SUBMISSIONS_DIR)/"
	@echo "  Logs:         $(LOGS_DIR)/"

stats: $(VENV)
	@echo "Festival Submit Statistics:"
	@echo ""
	@if [ -f "$(DATA_DIR)/submissions.db" ]; then \
		echo "Database: $(DATA_DIR)/submissions.db"; \
		$(VENV_PYTHON) -c "import sqlite3; conn = sqlite3.connect('$(DATA_DIR)/submissions.db'); print('  Tables:', [r[0] for r in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()])"; \
	else \
		echo "Database not initialized. Run 'make init'"; \
	fi

backup:
	@echo "Creating backup..."
	@mkdir -p backups
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	tar -czf backups/festival_submit_$$TIMESTAMP.tar.gz \
		$(CONFIG_DIR) $(DATA_DIR) $(REPORTS_DIR) 2>/dev/null || true
	@echo "✓ Backup created in backups/"

# Cleanup
clean:
	@echo "Cleaning generated files..."
	@rm -rf __pycache__
	@rm -f *.pyc
	@rm -rf .pytest_cache
	@rm -rf *.egg-info
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Cleaned"

clean-all: clean
	@echo "Removing virtual environment and generated data..."
	@rm -rf $(VENV)
	@rm -rf $(LOGS_DIR)/*
	@echo "✓ Full cleanup complete"
	@echo "  (Database, config, and reports preserved)"
	@echo "  Run 'make setup' to reinstall"

reset-db:
	@echo "⚠️  This will delete all submission data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -f $(DATA_DIR)/submissions.db; \
		echo "✓ Database deleted"; \
		$(MAKE) init; \
	else \
		echo "Cancelled"; \
	fi

# Quick shortcuts
.PHONY: ls-acts ls-fests ls-templates
ls-acts: acts
ls-fests: festivals
ls-templates: templates
