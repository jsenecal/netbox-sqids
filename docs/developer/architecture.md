# Architecture

## Overview

NetBox SQIDs is intentionally minimal. It has no models, no migrations, no database footprint. The entire plugin consists of:

1. A **Python descriptor** (`SqidDescriptor`) that computes SQIDs on access
2. A **module-level Sqids instance** (lazy singleton) that handles encoding/decoding
3. Two **redirect views** (browser + API) that resolve SQIDs to objects
4. A **`ready()` hook** that patches all models and optionally injects short URLs

```
┌─────────────────────────────────────────────────────┐
│                  PluginConfig.ready()                │
│                                                     │
│  ┌─────────────────┐    ┌────────────────────────┐  │
│  │  _patch_models() │    │     _patch_urls()      │  │
│  │                  │    │                        │  │
│  │  for all models: │    │  Appends to            │  │
│  │  add_to_class(   │    │  netbox.urls:          │  │
│  │    'sqid',       │    │    /s/<sqid>/          │  │
│  │    SqidDescriptor│    │    /api/s/<sqid>/      │  │
│  │  )               │    │                        │  │
│  └─────────────────┘    └────────────────────────┘  │
└─────────────────────────────────────────────────────┘

         ┌──────────────────┐
         │   SqidDescriptor │
         │                  │
         │  __get__() ──────┼──► encode([ct_id, pk])
         │  __set__() ──────┼──► AttributeError
         └──────────────────┘
                 │
                 ▼
         ┌──────────────────┐
         │  _get_instance() │  Lazy singleton
         │                  │
         │  Sqids(          │
         │    alphabet=..., │
         │    min_length=4, │
         │    blocklist=... │
         │  )               │
         └──────────────────┘
```

## Module Layout

```
netbox_sqids/
├── __init__.py          # PluginConfig + ready() hooks
├── sqids.py             # Sqids instance, SqidDescriptor, resolve_sqid()
├── views.py             # SqidRedirectView (browser)
├── urls.py              # Browser URL pattern
└── api/
    ├── __init__.py
    ├── views.py         # SqidApiRedirectView (API)
    └── urls.py          # API URL pattern
```

## Key Design Decisions

### Why a Descriptor?

A Python descriptor is attached to models via `add_to_class()` rather than using a custom Django field because:

- **No migrations** — descriptors don't touch the database schema
- **Universal** — works on any model, including third-party and built-in Django models
- **Lazy** — the SQID is only computed when accessed, zero overhead otherwise
- **Read-only** — `__set__` raises `AttributeError`, preventing accidental writes

### Why a Lazy Singleton?

The `Sqids` instance is created on first use rather than at import time because:

- Plugin settings (`PLUGINS_CONFIG`) aren't available until Django finishes setup
- Instance construction involves blocklist processing — doing it once is sufficient
- The module-level `_sqids_instance` avoids per-access overhead

### Why Monkey-Patch URLs?

NetBox plugins get URL routes under `/plugins/<name>/`, but short URLs like `/s/WK1J/` require being in the root URL config. The plugin appends to `netbox.urls.urlpatterns` in `ready()`, wrapped in try/except so failure is non-fatal.

### Why ContentType ID in the SQID?

Encoding `[content_type_id, pk]` rather than just `pk` ensures global uniqueness. Without the content type, Device #42 and Site #42 would produce the same SQID. Django's `ContentType` framework caches lookups, so the content type ID is effectively free after first access per model.

## Data Flow

### Encoding (property access)

```
obj.sqid
  → SqidDescriptor.__get__()
    → ContentType.objects.get_for_model(obj).pk  # cached
    → _get_instance().encode([ct_id, obj.pk])
    → "WK1J"
```

### Decoding (redirect)

```
GET /s/WK1J/
  → SqidRedirectView.get()
    → resolve_sqid("WK1J")
      → _get_instance().decode("WK1J")  →  [ct_id, pk]
      → ContentType.objects.get_for_id(ct_id)
      → ct.get_object_for_this_type(pk=pk)
    → obj.get_absolute_url()
  → 302 redirect
```
