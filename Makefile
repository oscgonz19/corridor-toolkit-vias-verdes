# Green Corridor Cartography Engine
# Makefile for common development tasks

.PHONY: help install dev test lint format demo clean run

# Default target
help:
	@echo "Green Corridor Cartography Engine"
	@echo ""
	@echo "Available commands:"
	@echo "  make install    Install package in development mode"
	@echo "  make dev        Install with development dependencies"
	@echo "  make test       Run tests"
	@echo "  make lint       Run linter (ruff)"
	@echo "  make format     Format code (ruff)"
	@echo "  make demo       Generate demo data and run demo pipeline"
	@echo "  make clean      Clean generated files"
	@echo ""
	@echo "CLI commands (after install):"
	@echo "  vv run --help"
	@echo "  vv chainage --help"
	@echo "  vv export-dxf --help"

# Installation
install:
	pip install -e .

dev:
	pip install -e ".[dev]"

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src --cov-report=term-missing

# Linting
lint:
	ruff check src/ cli/ tests/

format:
	ruff format src/ cli/ tests/
	ruff check --fix src/ cli/ tests/

# Demo
demo: demo-data demo-run

demo-data:
	@echo "Generating synthetic demo data..."
	python examples/generate_demo_data.py

demo-run:
	@echo "Running demo pipeline..."
	python -m cli.main run \
		--tramo demo \
		--axis examples/demo_data/demo_axis.gpkg \
		--sources examples/demo_data/demo_sources.gpkg \
		--disposal examples/demo_data/demo_disposal.gpkg \
		--out examples/demo_outputs

demo-chainage:
	@echo "Generating chainage table..."
	python -m cli.main chainage \
		--axis examples/demo_data/demo_axis.gpkg \
		--interval 500 \
		--out examples/demo_outputs/chainage_table.csv

# Clean
clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache
	rm -rf src/__pycache__ cli/__pycache__ tests/__pycache__
	rm -rf *.egg-info dist build
	rm -rf temp_kml temp_kml_*
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

clean-outputs:
	rm -rf examples/demo_outputs/*
	rm -rf outputs/*

# Type checking
typecheck:
	mypy src/ cli/

# All checks
check: lint test typecheck
