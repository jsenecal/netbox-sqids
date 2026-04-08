# API Reference

## `netbox_sqids.sqids`

### Constants

#### `ALPHABET`

```python
ALPHABET = "0123456789ACDEFGHJKLMNPQRSTUVWXYZ"
```

The 33-character alphabet used for all SQID encoding. Excludes B, I, and O to avoid visual ambiguity. This value is hardcoded and must never be changed — doing so would invalidate all existing SQIDs.

### Functions

#### `get_sqids_instance()`

```python
def get_sqids_instance(
    min_length: int = 4,
    blocklist: list[str] | None = None,
) -> Sqids
```

Create a new `Sqids` encoder/decoder instance.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_length` | `int` | `4` | Minimum output string length |
| `blocklist` | `list[str] \| None` | `None` | Word blocklist. `None` uses the extended default |

**Returns:** A configured `Sqids` instance.

When `blocklist` is `None`, the instance uses the sqids library's default blocklist extended with `["ck", "sex", "butt"]`.

---

#### `resolve_sqid()`

```python
def resolve_sqid(sqid_str: str) -> Model
```

Decode a SQID string and return the corresponding Django model instance.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `sqid_str` | `str` | The SQID string to decode |

**Returns:** The Django model instance.

**Raises:**

| Exception | Condition |
|-----------|-----------|
| `ValueError` | The string is empty or decodes to an unexpected number of components |
| `ObjectDoesNotExist` | The content type or object doesn't exist in the database |

**Example:**

```python
from netbox_sqids.sqids import resolve_sqid

device = resolve_sqid("WK1J")
```

### Classes

#### `SqidDescriptor`

A Python descriptor that provides a computed, read-only `sqid` property on model instances.

**Behavior:**

| Access | Returns |
|--------|---------|
| `MyModel.sqid` (class access) | The descriptor instance itself |
| `obj.sqid` where `obj.pk is None` | `None` |
| `obj.sqid` where `pk` is not an `int` | `None` |
| `obj.sqid` where `pk` is an `int` | The encoded SQID string |
| `obj.sqid = value` | Raises `AttributeError("sqid is read-only")` |

This descriptor is not meant to be used directly — it is automatically attached to all models by `PluginConfig.ready()`.

---

## `netbox_sqids.views`

### `SqidRedirectView`

A Django `View` that resolves a SQID and redirects to the object's `get_absolute_url()`.

**URL:** `/plugins/sqids/<sqid>/` (and optionally `/<prefix>/<sqid>/`)

**Method:** `GET`

**Responses:**

| Status | Condition |
|--------|-----------|
| 302 | SQID resolved successfully — redirects to object URL |
| 404 | Invalid SQID, object not found, or model has no `get_absolute_url()` |

---

## `netbox_sqids.api.views`

### `SqidApiRedirectView`

A Django `View` that resolves a SQID and redirects to the object's REST API detail endpoint.

**URL:** `/api/plugins/sqids/<sqid>/` (and optionally `/api/<prefix>/<sqid>/`)

**Method:** `GET`

**Responses:**

| Status | Condition |
|--------|-----------|
| 302 | SQID resolved successfully — redirects to API URL |
| 404 | Invalid SQID, object not found, or no API viewname available |

Uses NetBox's `get_viewname()` utility to derive the API endpoint from the resolved object.

---

## `NetBoxSqidsConfig`

The plugin configuration class, registered as `config` in `netbox_sqids/__init__.py`.

### Default Settings

```python
default_settings = {
    "min_length": 4,
    "blocklist": None,
    "monkeypatched_url_prefix": "s",
}
```

### `ready()`

Called by Django when the app is ready. Performs two actions:

1. **`_patch_models()`** — iterates all registered models and attaches a `SqidDescriptor` via `add_to_class('sqid', ...)`
2. **`_patch_urls()`** — if `monkeypatched_url_prefix` is set, appends short URL routes to `netbox.urls.urlpatterns`
