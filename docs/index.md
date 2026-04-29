# NetBox SQIDs

**Short, URL-safe, globally unique identifiers for every NetBox object.**

!!! warning "Alpha"
    This plugin is functional but under active development. The API and SQID
    encoding may change before 1.0. Encoding-affecting changes invalidate any
    SQIDs you have already shared and will be called out explicitly in the
    [changelog](changelog.md).

NetBox SQIDs is a plugin that adds a computed `sqid` property to every Django
model in your NetBox instance. SQIDs encode the content type and primary key
into a compact string that can be shared, bookmarked, and resolved back to
the original object.

## Why SQIDs?

NetBox object URLs leak two pieces of information in their default form:

- The **app and model** (`/dcim/devices/`, `/ipam/prefixes/`, ...)
- The **integer primary key**, which roughly correlates with creation order

That makes URLs verbose and hard to share over chat or in tickets. SQIDs
solve both problems in a single short token:

```
https://netbox.example.com/dcim/devices/4127/        ->  19 chars after host
https://netbox.example.com/s/WK1J/                   ->  6  chars after host
```

The same token works in the REST API, in scripts, in printed labels, and in
any place where pasting a full NetBox URL would be awkward.

## How it works

1. Every Django model gets a read-only `sqid` property at startup, attached
   by the plugin's `ready()` hook.
2. The property encodes a tuple of `(content_type_id, pk)` using the
   [sqids](https://sqids.org/) algorithm with a custom 33-character alphabet.
3. The redirect view decodes the SQID, looks up the model via Django's
   `ContentType` framework, and 302s to the object's detail page.

No tables. No migrations. No middleware. The full plugin is well under 200
lines of Python.

## Quick example

```python
>>> device = Device.objects.first()
>>> device.sqid
'WK1J'

>>> from netbox_sqids.sqids import resolve_sqid
>>> resolve_sqid('WK1J')
<Device: my-switch>
```

In the browser, visiting `/s/WK1J/` redirects to the device's detail page.
In the API, `/api/s/WK1J/` redirects to the REST detail endpoint.

## Features

- **Zero-config.** Install the plugin and every model gets a `.sqid`
  property automatically.
- **No migrations.** Pure computed properties, no database changes.
- **Globally unique.** SQIDs are unique across all models, not just within
  a table.
- **URL-safe.** Curated 33-character alphabet with no ambiguous characters
  (no B, I, or O).
- **Redirect views.** Resolve any SQID to its object via browser or REST
  API.
- **Short URLs.** Optional monkey-patched routes like `/s/WK1J/` at the
  root level.

## Where to next

- New here? Start with [Getting Started](user/getting-started.md).
- Looking up daily usage? See [Using SQIDs](user/using-sqids.md) and the
  [Recipes](user/recipes.md).
- Hitting a problem? Check [Troubleshooting](user/troubleshooting.md) or
  the [FAQ](user/faq.md).
- Curious about internals? See [Architecture](developer/architecture.md)
  and the [Encoding deep dive](developer/encoding.md).

## Requirements

| Dependency | Version  |
|------------|----------|
| NetBox     | >= 4.5.0 |
| Python     | >= 3.12  |
| sqids      | >= 0.4.1 |

## License

Apache 2.0
