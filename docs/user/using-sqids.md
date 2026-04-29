# Using SQIDs

This page covers everything you can do with a SQID once the plugin is
installed: read it from a model, paste it into a URL, and decode it back to
the original object.

## Accessing the SQID property

Every Django model registered with the application registry receives a
read-only `sqid` property. Access it like any other attribute:

```python
>>> from dcim.models import Site, Device
>>> from ipam.models import Prefix

>>> Site.objects.first().sqid
'A3KP'

>>> Device.objects.first().sqid
'WK1J'

>>> Prefix.objects.first().sqid
'M2QH'
```

The property is **read-only** -- attempting to set it raises
`AttributeError`:

```python
>>> Site.objects.first().sqid = "anything"
AttributeError: sqid is read-only
```

### Unsaved objects

If a model instance has not been saved yet, the SQID is undefined and the
property returns `None`:

```python
>>> Device(name="not-yet-saved").sqid is None
True
```

This also applies to copies created via `Model(**fields)` or `Model.objects.create(...)`
before commit.

### Non-integer primary keys

If a model uses a non-integer primary key (for example, a UUID), the
descriptor returns `None` rather than raising:

```python
>>> from somewhere.models import HasUuidPk
>>> obj = HasUuidPk.objects.first()
>>> obj.sqid is None
True
```

NetBox core models all use integer primary keys, so this only matters for
third-party plugins that opt out of the default.

## Resolving SQIDs

There are three ways to turn a SQID back into an object: a browser URL, an
API URL, and a Python helper. All three share the same decoding logic.

### Browser redirect

Visit the SQID URL in your browser to be redirected to the object's detail
page:

```
https://netbox.example.com/plugins/sqids/WK1J/
```

This issues a **302 redirect** to the object's `get_absolute_url()`.

If the short URL prefix is enabled (the default is `s`), you can also use
the short form:

```
https://netbox.example.com/s/WK1J/
```

Both routes accept the same SQID strings. The short routes live at the root
of the URL config and exist for convenience -- they are easier to share in
chat or paste into address bars.

### API redirect

The API endpoint works the same way, redirecting to the object's REST API
detail view:

```
https://netbox.example.com/api/plugins/sqids/WK1J/
```

Or with the short prefix:

```
https://netbox.example.com/api/s/WK1J/
```

The redirect target is computed from NetBox's `get_viewname()` helper, so
any model that has a registered REST detail view works automatically.

API clients should follow redirects (`curl -L`, `requests` with default
settings, etc.) to land on the actual JSON detail view.

### Programmatic resolution

In Python, call `resolve_sqid()` directly:

```python
from netbox_sqids.sqids import resolve_sqid

obj = resolve_sqid("WK1J")
print(obj)             # <Device: my-switch>
print(obj.pk)          # 42
print(type(obj))       # <class 'dcim.models.Device'>
```

The helper returns the actual model instance, fetched through Django's
`ContentType` framework. You can use the result anywhere you would use a
regular queryset result.

## Error handling

`resolve_sqid()` raises specific exceptions you can catch:

| Exception | Cause |
|-----------|-------|
| `ValueError` | SQID is empty, malformed, or decodes to the wrong number of components |
| `django.core.exceptions.ObjectDoesNotExist` | SQID is well-formed but the content type or object no longer exists |

The redirect views translate both of these into **HTTP 404**. They also
return 404 if the resolved model has no `get_absolute_url()` (for the
browser view) or no API view name (for the API view).

```python
from django.core.exceptions import ObjectDoesNotExist
from netbox_sqids.sqids import resolve_sqid

try:
    obj = resolve_sqid(token)
except ValueError:
    # Malformed token -- treat as not found
    obj = None
except ObjectDoesNotExist:
    # Token was valid but the underlying record has been deleted
    obj = None
```

## URL routes summary

| Route | Type | Condition |
|-------|------|-----------|
| `/plugins/sqids/<sqid>/` | Browser redirect | Always available |
| `/api/plugins/sqids/<sqid>/` | API redirect | Always available |
| `/<prefix>/<sqid>/` | Browser redirect (short) | When `monkeypatched_url_prefix` is set |
| `/api/<prefix>/<sqid>/` | API redirect (short) | When `monkeypatched_url_prefix` is set |

See [Configuration](configuration.md) for details on the prefix.

## Using SQIDs in templates

`sqid` behaves like any other model attribute, so it works in NetBox custom
templates and Jinja contexts.

### Custom links

NetBox custom links accept a Jinja2 template that has access to the object
as `obj`. A short link to the current object looks like:

```jinja
{{ obj.sqid }}
```

A clickable shareable URL with the short prefix:

```jinja
{% raw %}https://netbox.example.com/s/{{ obj.sqid }}/{% endraw %}
```

Wire this up in **Customization -> Custom Links**, scoped to whichever
content types you want the link to appear on.

### Object templates

In a custom template that already renders the object, simply read `obj.sqid`:

```html
<dt>SQID</dt>
<dd><code>{{ obj.sqid }}</code></dd>
```

### Export templates

Export templates iterate over a queryset. Add a `sqid` column to a CSV
export with:

```jinja
{% raw %}{% for obj in queryset %}{{ obj.name }},{{ obj.sqid }}
{% endfor %}{% endraw %}
```

Because the property is computed on access, large exports incur one
`ContentType` cache lookup per model class (cached after the first row) and
one encode call per row.

## Using SQIDs from scripts

In NetBox custom scripts, reports, or one-off management commands, treat
`sqid` like any other attribute:

```python
from extras.scripts import Script
from dcim.models import Device


class ListSqids(Script):
    def run(self, data, commit):
        for device in Device.objects.all():
            self.log_info(f"{device.name}: {device.sqid}")
```

## The alphabet

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

The alphabet is uppercase-only, so `L` and `1` are visually distinct on
most fonts. The alphabet is **hardcoded** -- changing it would invalidate
all existing SQIDs.

## How encoding works (in one paragraph)

Each SQID encodes two integers: the model's `ContentType` id and the
object's primary key. The encoder is configured with the 33-character
alphabet, a minimum length, and a blocklist of words to skip. Decoding
inverts the process: split into two integers, look up the content type,
and fetch the object. For the deeper version, see the
[Encoding deep dive](../developer/encoding.md).
