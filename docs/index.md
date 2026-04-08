# NetBox SQIDs

**Short, URL-safe, globally unique identifiers for every NetBox object.**

NetBox SQIDs is a plugin that adds a computed `sqid` property to every Django model in your NetBox instance. SQIDs encode the content type and primary key into a compact string that can be shared, bookmarked, and resolved back to the original object.

## Features

- **Zero-config** — install the plugin and every model gets a `.sqid` property automatically
- **No migrations** — pure computed properties, no database changes
- **Global uniqueness** — SQIDs are unique across all models, not just within a table
- **URL-safe** — uses a curated 33-character alphabet with no ambiguous characters
- **Redirect views** — resolve any SQID to its object via browser or API
- **Short URLs** — optional monkey-patched routes like `/s/WK1J/` at the root level

## Quick Example

```python
>>> device = Device.objects.first()
>>> device.sqid
'WK1J'

>>> from netbox_sqids.sqids import resolve_sqid
>>> resolve_sqid('WK1J')
<Device: my-switch>
```

In the browser, visiting `/s/WK1J/` redirects to the device's detail page.

## Requirements

| Dependency | Version |
|------------|---------|
| NetBox     | >= 4.4.0 |
| Python     | >= 3.12  |
| sqids      | >= 0.4.1 |

## License

MIT
