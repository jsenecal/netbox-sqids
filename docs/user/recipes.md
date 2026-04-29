# Recipes

Practical, copy-pasteable patterns for common NetBox SQIDs use cases.

## Build a short shareable URL for any object

```python
from django.conf import settings

def shareable_url(obj):
    base = getattr(settings, "BASE_PATH", "")
    prefix = settings.PLUGINS_CONFIG.get("netbox_sqids", {}).get(
        "monkeypatched_url_prefix", "s"
    )
    if prefix:
        return f"/{base}{prefix}/{obj.sqid}/"
    return f"/{base}plugins/sqids/{obj.sqid}/"
```

In a template:

```jinja
{% raw %}https://netbox.example.com/s/{{ obj.sqid }}/{% endraw %}
```

## Add a "Copy SQID" link to every object page

In **Customization -> Custom Links**, create a link with the following
values:

- **Name:** `Short URL`
- **Content types:** select all object types you care about
- **Link text:** `{% raw %}{{ obj.sqid }}{% endraw %}`
- **Link URL:**
  `{% raw %}https://netbox.example.com/s/{{ obj.sqid }}/{% endraw %}`

The link will render in the object's right-side toolbar with the SQID as
its visible text.

## Print SQID barcodes on labels

Because SQIDs are uppercase alphanumeric and contain no ambiguous
characters, they encode well in Code 128 and QR. Wire your label exporter
to read `obj.sqid` and emit a barcode plus the human-readable SQID
underneath.

```python
for device in queryset:
    label.add_code128(device.sqid)
    label.add_text(device.sqid)
```

When someone scans the label, the resulting URL `https://netbox.example.com/s/WK1J/`
opens directly to the device.

## Add a SQID column to CSV exports

In **Customization -> Export Templates**, create a template scoped to the
content type you want to export:

```jinja
{% raw %}name,site,sqid
{% for obj in queryset %}{{ obj.name }},{{ obj.site }},{{ obj.sqid }}
{% endfor %}{% endraw %}
```

Resulting CSV:

```
name,site,sqid
edge-01,DC1,WK1J
edge-02,DC1,M2QH
```

Recipients can paste any SQID value into a browser's address bar to jump
straight to the underlying object.

## Resolve a list of SQIDs in bulk

`resolve_sqid()` is a single-object lookup. To resolve many SQIDs without
hammering the database, group by content type:

```python
from collections import defaultdict
from django.contrib.contenttypes.models import ContentType
from netbox_sqids.sqids import _get_instance

def resolve_many(sqids):
    instance = _get_instance()
    by_ct = defaultdict(list)
    for s in sqids:
        ids = instance.decode(s)
        if len(ids) == 2:
            by_ct[ids[0]].append(ids[1])

    results = {}
    for ct_id, pks in by_ct.items():
        ct = ContentType.objects.get_for_id(ct_id)
        model = ct.model_class()
        for obj in model.objects.filter(pk__in=pks):
            results[obj.sqid] = obj
    return results
```

Note that `_get_instance()` is an internal helper -- if you need a public
API for bulk resolution, please open an issue.

## Look up the API URL for a SQID without HTTP

The `SqidApiRedirectView` builds an API URL by calling NetBox's
`get_viewname()` and `reverse()`. You can do the same in code:

```python
from django.urls import reverse
from utilities.views import get_viewname
from netbox_sqids.sqids import resolve_sqid

def api_url_for(sqid):
    obj = resolve_sqid(sqid)
    viewname = get_viewname(obj, action="detail", rest_api=True)
    return reverse(viewname, kwargs={"pk": obj.pk})
```

## Detect malformed SQIDs in user input

When accepting SQIDs from user input (chat bots, ticketing webhooks, ...):

```python
from django.core.exceptions import ObjectDoesNotExist
from netbox_sqids.sqids import resolve_sqid

def safe_resolve(token):
    try:
        return resolve_sqid(token)
    except (ValueError, ObjectDoesNotExist):
        return None
```

`ValueError` covers empty strings, garbage input, and tokens that decode to
the wrong number of components. `ObjectDoesNotExist` covers tokens that
were once valid but point at deleted records.

## Generate a SQID without a saved instance

Sometimes you want a SQID for an object you have not committed yet -- for
example, in a transaction-aware preview. The descriptor returns `None`
for unsaved objects, so save the object first and read `sqid` afterwards:

```python
device = Device(name="new-edge", ...)
device.full_clean()
device.save()
print(device.sqid)
```

If you must compute a SQID for a synthetic id, call the encoder directly:

```python
from django.contrib.contenttypes.models import ContentType
from dcim.models import Device
from netbox_sqids.sqids import _get_instance

ct_id = ContentType.objects.get_for_model(Device).pk
sqid = _get_instance().encode([ct_id, 999_999])
```

This is most useful in tests; production code should rely on the
descriptor.
