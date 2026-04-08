MANAGE = /opt/netbox/netbox/manage.py
PYTHON = /opt/netbox/venv/bin/python

# Guard: all targets require the devcontainer environment
ifeq (,$(wildcard /opt/netbox))
$(error This Makefile must be run inside the devcontainer (/opt/netbox not found))
endif

.PHONY: help migrations migrate runserver createsuperuser shell dbshell \
	collectstatic check lint lint-fix format format-check test test-v test-cov \
	install install-dev showurls showmigrations clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Django management ---

migrations: ## Create new migrations for netbox_sqids
	$(PYTHON) $(MANAGE) makemigrations netbox_sqids

migrate: ## Apply all migrations
	$(PYTHON) $(MANAGE) migrate

runserver: ## Start the development server on 0.0.0.0:8000
	$(PYTHON) $(MANAGE) runserver 0.0.0.0:8000

createsuperuser: ## Create a superuser account
	$(PYTHON) $(MANAGE) createsuperuser

shell: ## Open Django interactive shell
	$(PYTHON) $(MANAGE) shell_plus 2>/dev/null || $(PYTHON) $(MANAGE) shell

dbshell: ## Open database shell
	$(PYTHON) $(MANAGE) dbshell

collectstatic: ## Collect static files
	$(PYTHON) $(MANAGE) collectstatic --no-input

check: ## Run Django system checks
	$(PYTHON) $(MANAGE) check

showurls: ## List all registered URL patterns
	$(PYTHON) $(MANAGE) show_urls 2>/dev/null || \
		$(PYTHON) $(MANAGE) shell -c "from django.urls import get_resolver; [print(p.pattern) for p in get_resolver().url_patterns]"

showmigrations: ## Show migration status
	$(PYTHON) $(MANAGE) showmigrations netbox_sqids

# --- Code quality ---

lint: ## Run ruff linter
	ruff check netbox_sqids/ tests/

lint-fix: ## Run ruff linter with auto-fix
	ruff check --fix netbox_sqids/ tests/

format: ## Run ruff formatter
	ruff format netbox_sqids/ tests/

format-check: ## Check formatting without modifying files
	ruff format --check netbox_sqids/ tests/

# --- Testing ---

test: ## Run test suite
	$(PYTHON) -m pytest

test-v: ## Run test suite with verbose output
	$(PYTHON) -m pytest -v

test-cov: ## Run tests with coverage report
	$(PYTHON) -m pytest --cov=netbox_sqids --cov-report=term-missing --cov-report=html

# --- Install / setup ---

install: ## Install plugin in editable mode
	uv pip install -e /opt/netbox-sqids

install-dev: ## Install plugin with dev dependencies
	uv pip install -e "/opt/netbox-sqids[dev]"

clean: ## Remove build artifacts
	rm -rf build/ dist/ *.egg-info/ htmlcov/ .coverage .pytest_cache/
