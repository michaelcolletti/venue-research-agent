# Venue Research Agent - Root Makefile
# Comprehensive music venue research and festival submission system

.PHONY: help install install-dev setup clean clean-all \
        festival-setup venue-setup wizard \
        daily weekly status reports \
        test lint format \
        festival venue

# Configuration
PYTHON := python3
PIP := $(PYTHON) -m pip
VENV := venv
VENV_BIN := $(VENV)/bin
VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip

# Subdirectories
FESTIVAL_DIR := festival-submit
VENUE_DIR := venue-scout

# Default target
help:
	@echo "═══════════════════════════════════════════════════════════"
	@echo "🎭 Venue Research Agent - Music Industry Automation"
	@echo "═══════════════════════════════════════════════════════════"
	@echo ""
	@echo "📦 Installation & Setup:"
	@echo "  make install          - Install all dependencies"
	@echo "  make install-dev      - Install with dev tools"
	@echo "  make venv             - Create virtual environment"
	@echo "  make setup            - Full setup (both systems)"
	@echo "  make festival-setup   - Setup festival-submit only"
	@echo "  make venue-setup      - Setup venue-scout only"
	@echo "  make wizard           - Run venue-scout setup wizard"
	@echo "  make clean            - Remove generated files"
	@echo "  make clean-all        - Remove everything including venv"
	@echo ""
	@echo "🎯 Daily Operations:"
	@echo "  make daily            - Run daily tasks (both systems)"
	@echo "  make venue-daily      - Run venue research only"
	@echo "  make festival-daily   - Run festival automation only"
	@echo "  make weekly           - Generate weekly reports"
	@echo "  make status           - View current status"
	@echo ""
	@echo "📊 Reports:"
	@echo "  make reports          - Generate all reports"
	@echo "  make venue-report     - Venue research report"
	@echo "  make festival-report  - Festival submission report"
	@echo "  make calendar         - Festival submission calendar"
	@echo ""
	@echo "🔧 Component Access:"
	@echo "  make festival         - Show festival-submit commands"
	@echo "  make venue            - Show venue-scout commands"
	@echo "  cd festival-submit && make help"
	@echo "  cd venue-scout && make help"
	@echo ""
	@echo "🧪 Development:"
	@echo "  make test             - Run all tests"
	@echo "  make lint             - Run linters"
	@echo "  make format           - Format code"
	@echo ""
	@echo "📚 Documentation:"
	@echo "  - README.md           - Project overview"
	@echo "  - festival-submit/README.md - Festival submission docs"
	@echo "  - venue-scout/README.md     - Venue research docs"
	@echo ""
	@echo "Environment Variables:"
	@echo "  ANTHROPIC_API_KEY     - Required for Claude API searches"
	@echo "  SMTP_*                - Optional for email notifications"
	@echo "═══════════════════════════════════════════════════════════"

# Virtual environment setup
$(VENV):
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	@echo "✓ Virtual environment created at $(VENV)/"
	@echo "  Activate with: source $(VENV)/bin/activate"

venv: | $(VENV)

# Installation
install: $(VENV)
	@echo "Installing project dependencies..."
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements.txt
	@echo "✓ All dependencies installed"

install-dev: install
	@echo "Installing development dependencies..."
	$(VENV_PIP) install pytest black flake8
	@echo "✓ Development dependencies installed"

# Full setup
setup: venv install festival-setup venue-setup
	@echo ""
	@echo "✓ Complete setup finished!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Activate venv: source $(VENV)/bin/activate"
	@echo "  2. Set API key: export ANTHROPIC_API_KEY='sk-ant-...'"
	@echo "  3. Run venue wizard: make wizard"
	@echo "  4. Configure festival-submit: edit $(FESTIVAL_DIR)/config/*.toml"
	@echo "  5. Start daily operations: make daily"

festival-setup: $(VENV)
	@echo "Setting up festival-submit..."
	@cd $(FESTIVAL_DIR) && $(MAKE) setup
	@echo "✓ Festival-submit ready"

venue-setup: $(VENV)
	@echo "Setting up venue-scout..."
	@cd $(VENUE_DIR) && $(MAKE) setup
	@echo "✓ Venue-scout ready"

# Setup wizard
wizard: $(VENV)
	@echo "Starting venue-scout setup wizard..."
	@cd $(VENUE_DIR) && $(MAKE) wizard

# Daily operations
daily: venue-daily festival-daily
	@echo ""
	@echo "✓ Daily operations complete"
	@date

venue-daily: $(VENV)
	@echo "═══ Running venue-scout daily tasks ═══"
	@cd $(VENUE_DIR) && $(MAKE) run-daily

festival-daily: $(VENV)
	@echo "═══ Running festival-submit daily tasks ═══"
	@cd $(FESTIVAL_DIR) && $(MAKE) daily

# Weekly operations
weekly: venue-weekly festival-weekly
	@echo ""
	@echo "✓ Weekly reports generated"
	@date

venue-weekly: $(VENV)
	@cd $(VENUE_DIR) && $(MAKE) weekly-report

festival-weekly: $(VENV)
	@cd $(FESTIVAL_DIR) && $(MAKE) weekly

# Status
status: venue-status festival-status

venue-status: $(VENV)
	@echo "═══ Venue Scout Status ═══"
	@cd $(VENUE_DIR) && $(MAKE) list-acts || echo "Not initialized"
	@echo ""

festival-status: $(VENV)
	@echo "═══ Festival Submit Status ═══"
	@cd $(FESTIVAL_DIR) && $(MAKE) status || echo "Not initialized"
	@echo ""

# Reports
reports: venue-report festival-report calendar

venue-report: $(VENV)
	@cd $(VENUE_DIR) && $(MAKE) weekly-report

festival-report: $(VENV)
	@cd $(FESTIVAL_DIR) && $(MAKE) report-status

calendar: $(VENV)
	@cd $(FESTIVAL_DIR) && $(MAKE) calendar

# Component help
festival:
	@echo "Festival Submit Commands:"
	@cd $(FESTIVAL_DIR) && $(MAKE) help

venue:
	@echo "Venue Scout Commands:"
	@cd $(VENUE_DIR) && $(MAKE) help

# Development
test: $(VENV)
	@echo "Running all tests..."
	@cd $(FESTIVAL_DIR) && $(MAKE) test
	@cd $(VENUE_DIR) && $(MAKE) test
	@echo "✓ All tests complete"

lint: $(VENV)
	@echo "Running linters..."
	@cd $(FESTIVAL_DIR) && $(MAKE) lint
	@cd $(VENUE_DIR) && $(MAKE) lint
	@echo "✓ Linting complete"

format: $(VENV)
	@echo "Formatting code..."
	@cd $(FESTIVAL_DIR) && $(MAKE) format
	@cd $(VENUE_DIR) && $(MAKE) format
	@echo "✓ Code formatted"

# Utilities
check-env:
	@echo "Environment Check:"
	@if [ -z "$$ANTHROPIC_API_KEY" ]; then \
		echo "❌ ANTHROPIC_API_KEY not set"; \
		echo "   Set with: export ANTHROPIC_API_KEY='sk-ant-...'"; \
	else \
		echo "✓ ANTHROPIC_API_KEY is set"; \
	fi
	@echo ""
	@if [ -z "$$SMTP_USER" ]; then \
		echo "⚠️  Email notifications not configured (optional)"; \
	else \
		echo "✓ Email notifications configured"; \
	fi
	@echo ""
	@if [ -d "$(VENV)" ]; then \
		echo "✓ Virtual environment exists"; \
	else \
		echo "❌ Virtual environment missing - run 'make venv'"; \
	fi

backup:
	@echo "Creating full backup..."
	@mkdir -p backups
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	tar -czf backups/venue_research_agent_$$TIMESTAMP.tar.gz \
		--exclude='venv' \
		--exclude='__pycache__' \
		--exclude='.git' \
		--exclude='*.pyc' \
		$(FESTIVAL_DIR) $(VENUE_DIR) requirements.txt README.md Makefile 2>/dev/null || true
	@echo "✓ Backup created in backups/"
	@ls -lh backups/*.tar.gz | tail -1

restore-latest:
	@echo "Available backups:"
	@ls -1t backups/*.tar.gz 2>/dev/null | head -5 || echo "No backups found"
	@echo ""
	@echo "To restore: tar -xzf backups/venue_research_agent_TIMESTAMP.tar.gz"

stats:
	@echo "═══════════════════════════════════════════════════════════"
	@echo "📊 Venue Research Agent Statistics"
	@echo "═══════════════════════════════════════════════════════════"
	@echo ""
	@echo "📁 Project Files:"
	@find . -name "*.py" -not -path "./venv/*" | wc -l | xargs echo "  Python files:"
	@find . -name "*.toml" -not -path "./venv/*" | wc -l | xargs echo "  Config files:"
	@find . -name "*.md" -not -path "./venv/*" | wc -l | xargs echo "  Documentation:"
	@echo ""
	@if [ -d "$(VENUE_DIR)/data" ]; then \
		echo "🎵 Venue Scout:"; \
		if [ -f "$(VENUE_DIR)/data/venues.db" ]; then \
			echo "  Database: ✓ initialized"; \
		else \
			echo "  Database: ✗ not initialized"; \
		fi; \
	fi
	@echo ""
	@if [ -d "$(FESTIVAL_DIR)/data" ]; then \
		echo "🎪 Festival Submit:"; \
		if [ -f "$(FESTIVAL_DIR)/data/submissions.db" ]; then \
			echo "  Database: ✓ initialized"; \
		else \
			echo "  Database: ✗ not initialized"; \
		fi; \
	fi
	@echo ""
	@echo "Last modified: $$(date)"
	@echo "═══════════════════════════════════════════════════════════"

# Cleanup
clean:
	@echo "Cleaning generated files..."
	@rm -rf __pycache__
	@rm -f *.pyc
	@cd $(FESTIVAL_DIR) && $(MAKE) clean
	@cd $(VENUE_DIR) && $(MAKE) clean
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Cleaned"

clean-all: clean
	@echo "Removing virtual environment..."
	@rm -rf $(VENV)
	@cd $(FESTIVAL_DIR) && $(MAKE) clean-all
	@cd $(VENUE_DIR) && $(MAKE) clean-all
	@echo "✓ Full cleanup complete"
	@echo "  Run 'make setup' to reinstall"

# Quick shortcuts
.PHONY: v f init
v: venue
f: festival
init: setup
