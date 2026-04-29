# Architecture

## Overview

NetBox SQIDs is intentionally minimal. It has no models, no migrations, no
database footprint. The entire plugin consists of:

1. A **Python descriptor** (`SqidDescriptor`) that computes SQIDs on access.
2. A **module-level Sqids instance** (lazy singleton) that handles
   encoding and decoding.
3. Two **redirect views** (browser and API) that resolve SQIDs to objects.
4. A **`ready()` hook** that patches all models and optionally injects
   short URLs.

```
+-----------------------------------------------------+
|                  PluginConfig.ready()                |
|                                                     |
|  +-----------------+    +------------------------+  |
|  | _patch_models() |    |     _patch_urls()      |  |
|  |                 |    |                        |  |
|  | for all models: |    | Appends to             |  |
|  | add_to_class(   |    | netbox.urls:           |  |
|  |   'sqid',       |    |   /<prefix>/<sqid>/    |  |
|  |   SqidDescriptor|    |   /api/<prefix>/...    |  |
|  | )               |    |                        |  |
|  +-----------------+    +------------------------+  |
+-----------------------------------------------------+

         +------------------+
         |   SqidDescriptor |
         |                  |
         |  __get__() ------+--> encode([ct_id, pk])
         |  __set__() ------+--> AttributeError
         +------------------+
                 |
                 v
         +------------------+
         |  _get_instance() |  Lazy singleton
         |                  |
         |  Sqids(          |
         |    alphabet=..., |
         |    min_length=4, |
         |    blocklist=... |
         |  )               |
         +------------------+
```

## Module layout

```
netbox_sqids/
+-- __init__.py          # PluginConfig + ready() hooks
+-- sqids.py             # Sqids instance, SqidDescriptor, resolve_sqid()
+-- views.py             # SqidRedirectView (browser)
+-- urls.py              # Browser URL pattern
+-- api/
    +-- __init__.py
    +-- views.py         # SqidApiRedirectView (API)
    +-- urls.py          # API URL pattern

tests/
+-- test_sqids.py        # Unit tests for core logic
+-- test_views.py        # View tests

docs/                    # Zensical documentation
```

The full implementation is roughly 130 lines of Python. The simplicity is
the point.

## Component responsibilities

### `netbox_sqids/__init__.py`

Defines `NetBoxSqidsConfig`, the `PluginConfig` subclass NetBox loads at
startup. The `ready()` method runs two patches:

- `_patch_models()` walks every model in the application registry and
  calls `model.add_to_class("sqid", SqidDescriptor())`. This is how every
  NetBox model gains a `sqid` property without subclassing or schema
  changes.
- `_patch_urls()` appends two URL patterns to `netbox.urls.urlpatterns`.
  The patch is wrapped in `try/except` and logs a warning on failure --
  the plugin's standard `/plugins/sqids/` routes always work regardless.

### `netbox_sqids/sqids.py`

The core module. Contains:

- The `ALPHABET` constant.
- `get_sqids_instance(min_length, blocklist)` -- a factory that builds
  configured `Sqids` instances. Used by tests directly.
- `_get_instance()` -- the lazy module-level singleton. Reads
  `PLUGINS_CONFIG["netbox_sqids"]` on first call and caches the result.
- `SqidDescriptor` -- the descriptor attached to every model.
- `resolve_sqid()` -- the decode + lookup helper.

### `netbox_sqids/views.py` and `api/views.py`

Two thin Django `View` subclasses. Both:

1. Resolve the SQID via `resolve_sqid()`.
2. Translate `ValueError` and `ObjectDoesNotExist` to `Http404`.
3. Build the redirect target -- `obj.get_absolute_url()` for the browser,
   `reverse(get_viewname(obj, action='detail', rest_api=True), ...)` for
   the API.
4. Return `HttpResponseRedirect`.

The browser view returns 404 if the resolved model has no
`get_absolute_url()`. The API view returns 404 if `get_viewname()` fails
or `reverse()` cannot resolve the view name.

### `netbox_sqids/urls.py` and `api/urls.py`

Standard plugin URL configs that wire the views to
`<sqid>` path parameters. NetBox mounts these under `/plugins/sqids/` and
`/api/plugins/sqids/` respectively.

## Key design decisions

### Why a descriptor?

A Python descriptor is attached to models via `add_to_class()` rather than
using a custom Django field because:

- **No migrations.** Descriptors do not touch the database schema.
- **Universal.** Works on any model, including third-party and built-in
  Django models.
- **Lazy.** The SQID is only computed when accessed -- zero overhead
  otherwise.
- **Read-only.** `__set__` raises `AttributeError`, preventing accidental
  writes.

The trade-off is that descriptors are not visible in admin or in
form-rendered fields. They are runtime properties, not schema. That is
intentional -- there is nothing to migrate, dump, or restore.

### Why a lazy singleton?

The `Sqids` instance is created on first use rather than at import time
because:

- Plugin settings (`PLUGINS_CONFIG`) are not available until Django
  finishes setup.
- Instance construction processes the blocklist, which is mildly
  expensive -- doing it once per process is sufficient.
- The module-level `_sqids_instance` avoids per-access overhead.

This pattern -- module-level None plus an `_get_instance()` getter -- is
intentionally simple. There is no thread-local handling because
`Sqids` instances are read-only and safe to share across threads.

### Why monkey-patch URLs?

NetBox plugins get URL routes mounted under `/plugins/<name>/`. That is
fine for `/plugins/sqids/<sqid>/`, but the whole point of short URLs is
that they live at the *root* of the host. There is no plugin hook for
adding a root route, so the plugin appends to `netbox.urls.urlpatterns`
during `ready()`. The patch is wrapped in `try/except` so a NetBox
internal change cannot brick the plugin.

If you object to the monkey-patch, set `monkeypatched_url_prefix = None`
in your settings. The standard plugin routes still work.

### Why content type id in the SQID?

Encoding `[content_type_id, pk]` rather than just `pk` ensures global
uniqueness. Without the content type, Device #42 and Site #42 would
produce the same SQID. Django's `ContentType` framework caches lookups
per process, so the content type id is effectively free after first
access per model.

The downside is that SQIDs are not stable across NetBox instances --
two databases can assign different content type ids to the same model.
Within a single instance, content type ids are stable.

## Data flow

### Encoding (property access)

```
obj.sqid
  -> SqidDescriptor.__get__()
    -> ContentType.objects.get_for_model(obj).pk     # cached
    -> _get_instance().encode([ct_id, obj.pk])
    -> "WK1J"
```

The descriptor checks two early-return conditions: `obj.pk is None` and
`isinstance(obj.pk, int)`. Both return `None` rather than raising, so
unsaved or non-integer-PK objects are silently inert.

### Decoding (redirect)

```
GET /s/WK1J/
  -> SqidRedirectView.get()
    -> resolve_sqid("WK1J")
      -> _get_instance().decode("WK1J")     # -> [ct_id, pk]
      -> ContentType.objects.get_for_id(ct_id)
      -> ct.get_object_for_this_type(pk=pk)
    -> obj.get_absolute_url()
  -> 302 redirect
```

### Decoding (API)

```
GET /api/s/WK1J/
  -> SqidApiRedirectView.get()
    -> resolve_sqid("WK1J")                 # same as above
    -> get_viewname(obj, action="detail", rest_api=True)
    -> reverse(viewname, kwargs={"pk": obj.pk})
  -> 302 redirect
```

## Error handling

`resolve_sqid()` raises:

- `ValueError` for empty input or wrong-component-count decodes.
- `ObjectDoesNotExist` for missing content types or objects.

Both views translate those into `Http404`. They also produce 404 when:

- The browser view's resolved object has no `get_absolute_url()`.
- The API view fails to compute or reverse the API view name.

Anything else is allowed to propagate -- in particular, exceptions raised
inside `get_absolute_url()` or any model's `__init__` show up in
NetBox's normal error logs.

## Performance characteristics

| Operation | Cost |
|-----------|------|
| Module import | Zero -- singleton is `None` until first call |
| First `obj.sqid` per process | One `Sqids()` build (microseconds) + one ContentType lookup (cached after) + one encode |
| Subsequent `obj.sqid` | One ContentType cache hit + one encode (microseconds) |
| `resolve_sqid("...")` | One decode (microseconds) + one ContentType lookup + one DB query |
| Patch on startup | One pass over `apps.get_models()` and one `add_to_class` per model |

The startup patch is O(n) in the number of registered models. With a
typical NetBox install the cost is well under a second. The patched
descriptors are shared instances, so memory overhead is bounded.

## Threading and concurrency

The `Sqids` instance is constructed once per process and treated as
immutable. There is no shared mutable state in `netbox_sqids` after
startup. Using the descriptor or `resolve_sqid()` from any thread is
safe.

For more on the encoding scheme itself, including the alphabet rationale
and blocklist mechanics, see the [Encoding deep dive](encoding.md).
