# Contributing

## Development Environment

This project uses a VS Code devcontainer with NetBox, PostgreSQL, and Redis pre-configured.

### Prerequisites

- Docker and Docker Compose
- VS Code with the Dev Containers extension

### Setup

1. Clone the repository
2. Open in VS Code — it will prompt to reopen in the devcontainer
3. Install the plugin in dev mode:

```bash
make install-dev
```

### Common Commands

All commands run inside the devcontainer:

```bash
make test          # Run test suite
make test-v        # Verbose test output
make test-cov      # Tests with coverage report
make lint          # Run ruff linter
make lint-fix      # Auto-fix lint issues
make format        # Run ruff formatter
make runserver     # Start dev server on port 8000
make shell         # Django interactive shell
make check         # Django system checks
make showurls      # List registered URL patterns
```

## Project Structure

```
netbox_sqids/          # Plugin package
├── __init__.py        # PluginConfig with ready() hooks
├── sqids.py           # Core logic: Sqids instance, descriptor, resolver
├── views.py           # Browser redirect view
├── urls.py            # Browser URL config
└── api/
    ├── views.py       # API redirect view
    └── urls.py        # API URL config

tests/                 # Test suite
├── test_sqids.py      # Unit tests for core logic
└── test_views.py      # View tests

docs/                  # Documentation (Zensical)
├── index.md
├── user/              # User-facing docs
└── developer/         # Developer docs
```

## Testing

Tests use pytest-django with mocked Django internals. The test suite does not require a running database — all ContentType lookups are patched.

```bash
make test-v
```

### Test Organization

- **`test_sqids.py`** — `TestSqidsInstance` (encoding/decoding), `TestSqidDescriptor` (property behavior), `TestResolveSqid` (resolution logic)
- **`test_views.py`** — `TestSqidRedirectView` (browser redirects), `TestSqidApiRedirectView` (API redirects)

### Writing Tests

Follow the existing TDD pattern:

1. Write a failing test
2. Implement the minimal code to pass
3. Refactor if needed
4. Ensure `make lint` passes

## Code Style

- **Formatter/linter:** ruff (configured in `pyproject.toml`)
- **Line length:** 120 characters
- **Target:** Python 3.12+
- **Import sorting:** ruff's isort rules

Run before committing:

```bash
make lint-fix
make format
```

## Documentation

Documentation is built with [Zensical](https://zensical.org/). Source files are in `docs/`.

To preview locally:

```bash
zensical serve
```

To build:

```bash
zensical build
```
