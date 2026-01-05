.PHONY: help install build run clean

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make build      - Build the program"
	@echo "  make run        - Run the program (default mode)"
	@echo "  make run-dev    - Run in development mode"
	@echo "  make run-test   - Run in test mode"
	@echo "  make clean      - Remove build artifacts"

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

build:
	@echo "Building the program..."
	python setup.py build

run:
	@echo "Running venue-scout..."
	python -m venue_scout

run-dev:
	@echo "Running venue-scout in development mode..."
	python -m venue_scout --dev

run-test:
	@echo "Running tests..."
	python -m pytest tests/

clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

quick-start:
	@echo "Quick start: installing and running venue-scout..."
	pip install -r requirements.txt
	python -m venue_scout

gui:
	@echo "Opening venue-scout GUI..."
	python -m venue_scout --gui