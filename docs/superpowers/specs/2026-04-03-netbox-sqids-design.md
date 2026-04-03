# netbox-sqids Design Spec

**Date:** 2026-04-03
**Status:** Approved

## Overview

A NetBox plugin that adds a computed `sqid` property to every Django model via `add_to_class`. SQIDs encode `[content_type_id, object_pk]` to produce short, URL-safe, globally unique identifiers. The plugin also provides redirect views for resolving SQIDs back to objects.

No database columns, no migrations, no models. Pure computed properties and utility views.

## Alphabet

Hardcoded, never configurable (changing it breaks all existing SQIDs):

```
0123456789ACDEFGHJKLMNPQRSTUVWXYZ
```

33 characters. Excluded for visual ambiguity: **B** (vs 8), **I** (vs 1), **O** (vs 0). Uppercase only — `L` and `1` are distinct in caps.

## Encoding Scheme

```python
sqid = sqids.encode([content_type_id, object_pk])
```

- `content_type_id` — Django's `ContentType` PK for the model (cached by Django, no query per access)
- `object_pk` — the object's integer primary key
- The tuple guarantees global uniqueness across all models

Unsaved objects (`pk is None`) and non-integer PKs return `None`.

## Architecture

### SqidDescriptor

A Python descriptor class that encapsulates the encoding logic:

```python
class SqidDescriptor:
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if obj.pk is None:
            return None
        ct_id = ContentType.objects.get_for_model(obj).pk
        return sqids_instance.encode([ct_id, obj.pk])

    def __set__(self, obj, value):
        raise AttributeError("sqid is read-only")
```

- Read-only computed property
- `ContentType.objects.get_for_model()` is cached by Django — no DB hit after first access per model
- Single `Sqids()` instance at module level (instance construction is the expensive part; encode is ~5-15us)

### Auto-Discovery

In `PluginConfig.ready()`:

```python
def ready(self):
    super().ready()
    from django.apps import apps
    for model in apps.get_models():
        model.add_to_class('sqid', SqidDescriptor())
```

- Patches every registered model unconditionally
- Zero-cost: property is computed on access only, no DB column, no overhead on models that never use it
- No filtering by PK type — the descriptor returns `None` for non-integer PKs

### resolve_sqid()

```python
def resolve_sqid(sqid_str: str):
    """Decode a SQID string and return the corresponding model instance.

    Raises:
        ValueError: if sqid_str is empty or decodes to unexpected length
        ObjectDoesNotExist: if the content type or object doesn't exist
    """
    ids = sqids_instance.decode(sqid_str)
    if len(ids) != 2:
        raise ValueError(f"Invalid SQID: {sqid_str}")
    ct_id, obj_id = ids
    ct = ContentType.objects.get_for_id(ct_id)
    return ct.get_object_for_this_type(pk=obj_id)
```

## Views

### Browser Redirect — `/plugins/sqids/<sqid>/`

- Calls `resolve_sqid(sqid_str)`
- 302 redirects to `obj.get_absolute_url()`
- Returns 404 if the SQID is invalid, the object doesn't exist, or the model has no `get_absolute_url()`

### API Redirect — `/api/plugins/sqids/<sqid>/`

- Calls `resolve_sqid(sqid_str)`
- Resolves the API URL using NetBox's `get_viewname(obj, action='detail', rest_api=True)` + Django's `reverse()`
- 302 redirects to the object's API endpoint (e.g., `/api/dcim/devices/<pk>/`)
- Returns 404 on failure
- Respects NetBox authentication (`IsAuthenticated`)

### Monkey-Patched Short URLs

When `monkeypatched_url_prefix` is set (default: `"s"`), the plugin appends routes to NetBox's root and API urlconfs in `ready()`:

- `/<prefix>/<sqid>/` — browser redirect
- `/api/<prefix>/<sqid>/` — API redirect

Implementation: imports and mutates `netbox.urls.urlpatterns` and `netbox.api.urls.urlpatterns` directly. Wrapped in try/except so failure is logged but non-fatal — the standard `/plugins/sqids/` routes still work.

Set `monkeypatched_url_prefix` to `None` to disable.

## Plugin Settings

```python
default_settings = {
    "min_length": 4,                      # Minimum SQID string length
    "blocklist": None,                    # None = default extended blocklist
    "monkeypatched_url_prefix": "s",      # None to disable short URLs
}
```

**Default blocklist** (when `blocklist` is `None`):

```python
sqids.constants.DEFAULT_BLOCKLIST + ["ck", "sex", "butt"]
```

## File Structure

```
netbox-sqids/
├── .devcontainer/
│   ├── configuration/
│   │   ├── configuration.py        # NetBox config (standard PostgreSQL)
│   │   └── logging.py
│   ├── env/
│   │   ├── netbox.env
│   │   ├── postgres.env
│   │   └── redis.env
│   ├── home/
│   │   ├── .config/
│   │   │   ├── fish/conf.d/        # Fish shell configs
│   │   │   ├── omf/                # Oh My Fish config
│   │   │   └── Code/User/keybindings.json
│   │   └── .claude/.gitkeep
│   ├── .gitignore
│   ├── devcontainer.json
│   ├── docker-compose.yml
│   ├── Dockerfile-plugin_dev
│   ├── entrypoint-dev.sh
│   └── requirements-dev.txt
├── netbox_sqids/
│   ├── __init__.py                 # PluginConfig, ready() auto-discovery + monkey-patch
│   ├── sqids.py                    # Sqids instance, SqidDescriptor, resolve_sqid()
│   ├── api/
│   │   ├── __init__.py
│   │   ├── urls.py                 # /api/plugins/sqids/<sqid>/
│   │   └── views.py                # API redirect view
│   ├── urls.py                     # /plugins/sqids/<sqid>/
│   └── views.py                    # Browser redirect view
├── tests/
│   ├── __init__.py
│   ├── test_sqids.py               # Descriptor, encode/decode, resolve
│   └── test_views.py               # Redirect + API views
├── .gitignore
├── pyproject.toml
└── README.md
```

## Devcontainer

Adapted from netbox-pathways devcontainer. Key differences:

- **No GIS packages** — no PostGIS, GDAL, libgeos, libproj
- **Standard PostgreSQL engine** — `django.db.backends.postgresql` instead of PostGIS
- **Standard `postgres:16` image** — instead of `postgis/postgis:16-3.4`
- **No worker service** — this plugin has no background tasks
- **Simpler pyproject.toml** — no static/template package data

Same infrastructure: fish shell, oh-my-fish, Claude Code, GitHub CLI, ruff, pytest-django with `--reuse-db`.

## Testing

Tests run inside the devcontainer against a real NetBox + PostgreSQL instance using pytest-django.

- `test_sqids.py` — unit tests for SqidDescriptor, encode/decode round-trips, resolve_sqid with valid/invalid inputs, non-integer PK handling
- `test_views.py` — integration tests for browser redirect (302 + 404), API redirect (302 + 404 + auth), monkey-patched short URLs

pytest config: `DJANGO_SETTINGS_MODULE = "netbox.settings"`, `--reuse-db`, `--cov=netbox_sqids`.

## Dependencies

- `sqids>=0.4.1`
- NetBox `>=4.4.0`

## Non-Goals

- No database storage of SQIDs
- No admin UI or navigation menu
- No model registration or custom fields
- No support for UUID PKs (returns `None`)
- No bulk resolution endpoint
