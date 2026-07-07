.PHONY: help install-dev test test-cov lint format type-check build clean

VENV ?= .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(PYTHON) -m pytest

help:
	@echo "Available commands:"
	@echo "  make install-dev  - Install package and dev dependencies into $(VENV)/"
	@echo "  make test         - Run tests"
	@echo "  make test-cov     - Run tests with coverage report"
	@echo "  make lint         - Run linter (ruff)"
	@echo "  make format       - Format code (black)"
	@echo "  make type-check   - Run type checker (mypy)"
	@echo "  make build        - Build package"
	@echo "  make clean        - Clean build artifacts"

install-dev:
	$(PIP) install -e ".[dev]" build twine

test:
	$(PYTEST) tests/

test-cov:
	$(PYTEST) tests/ \
		--cov=fastapi_errors_plus \
		--cov-report=term-missing \
		--cov-report=html:tests/htmlcov \
		--cov-report=json:tests/coverage.json \
		--cov-report=xml:tests/coverage.xml \
		--cov-branch \
		--cov-fail-under=80
	@echo ""
	@echo "Coverage reports generated:"
	@echo "  - Terminal: displayed above"
	@echo "  - HTML: tests/htmlcov/index.html"
	@echo "  - JSON: tests/coverage.json"
	@echo "  - XML: tests/coverage.xml"

lint:
	$(PYTHON) -m ruff check fastapi_errors_plus/ tests/ examples/

format:
	$(PYTHON) -m black fastapi_errors_plus/ tests/ examples/

type-check:
	$(PYTHON) -m mypy fastapi_errors_plus/

build:
	$(PYTHON) -m build

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf fastapi_errors_plus.egg-info
	rm -rf tests/htmlcov/
	rm -f tests/coverage.json tests/coverage.xml tests/.coverage
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
