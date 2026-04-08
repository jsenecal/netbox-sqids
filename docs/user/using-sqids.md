# Using SQIDs

## Accessing the SQID Property

Once installed, every model in NetBox has a `.sqid` property:

```python
>>> from dcim.models import Site
>>> site = Site.objects.first()
>>> site.sqid
'A3KP'
```

The property is **read-only** — attempting to set it raises `AttributeError`:

```python
>>> site.sqid = "something"
AttributeError: sqid is read-only
```

### Unsaved and Non-Integer PK Objects

- Unsaved objects (`pk is None`) return `None`
- Models with non-integer primary keys (e.g., UUIDs) return `None`

## Resolving SQIDs

### Browser Redirect

Visit the SQID URL in your browser to be redirected to the object's detail page:

```
https://netbox.example.com/plugins/sqids/WK1J/
```

This issues a **302 redirect** to the object's `get_absolute_url()`.

If the short URL prefix is enabled (default: `s`), you can also use:

```
https://netbox.example.com/s/WK1J/
```

### API Redirect

The API endpoint works the same way, redirecting to the object's REST API detail view:

```
https://netbox.example.com/api/plugins/sqids/WK1J/
```

Or with the short prefix:

```
https://netbox.example.com/api/s/WK1J/
```

### Programmatic Resolution

Use `resolve_sqid()` in Python code:

```python
from netbox_sqids.sqids import resolve_sqid

obj = resolve_sqid("WK1J")
print(obj)  # <Device: my-switch>
```

This raises `ValueError` for invalid SQIDs and `ObjectDoesNotExist` for valid SQIDs pointing to deleted objects.

## Error Handling

All redirect views return **HTTP 404** when:

- The SQID string is invalid or malformed
- The encoded content type or object no longer exists
- The resolved model has no `get_absolute_url()` (browser view) or no API viewname (API view)

## The Alphabet

SQIDs use a curated 33-character alphabet:

```
0123456789ACDEFGHJKLMNPQRSTUVWXYZ
```

Three letters are excluded to avoid visual ambiguity:

| Excluded | Reason |
|----------|--------|
| **B**    | Looks like **8** |
| **I**    | Looks like **1** |
| **O**    | Looks like **0** |

The alphabet is uppercase-only, so `L` and `1` are visually distinct. This alphabet is **hardcoded** — changing it would invalidate all existing SQIDs.

## How Encoding Works

Each SQID encodes two integers:

```python
sqid = sqids.encode([content_type_id, object_pk])
```

- **`content_type_id`** — Django's `ContentType` primary key for the model (cached, no DB query after first access)
- **`object_pk`** — the object's integer primary key

The pair guarantees global uniqueness: no two objects of any type can produce the same SQID.
