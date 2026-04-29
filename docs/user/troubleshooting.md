# Troubleshooting

Common issues and their causes. If you run into something not covered here,
please [open an issue](https://github.com/jsenecal/netbox-sqids/issues).

## `obj.sqid` returns `None`

The descriptor returns `None` in two cases:

1. **The object has not been saved.** `pk is None`. Save the object first.
2. **The primary key is not an integer.** The encoder only handles
   integer PKs. Models that use UUIDs or other custom primary key fields
   are not supported. NetBox core models all use integer PKs, so this
   only matters for third-party plugins.

```python
>>> Device(name="not-saved").sqid is None
True
>>> obj.pk = "uuid-string"
>>> obj.sqid is None
True
```

## `AttributeError: sqid is read-only`

The `sqid` property is intentionally read-only. The descriptor's `__set__`
always raises. If you need a writable identifier, use a regular field on
the model.

## `AttributeError: 'X' object has no attribute 'sqid'`

The plugin attaches `sqid` to every model registered with the application
registry at the moment `ready()` runs. If a model is added after that
point (rare, usually via dynamic class creation), it will not have the
descriptor. Reasons this can happen:

- The plugin is not in `PLUGINS`. Verify your `configuration.py`.
- NetBox was not restarted after enabling the plugin.
- Models defined inside a function or test fixture without going through
  Django's normal app loading path.

Restart NetBox. If the problem persists, check the NetBox logs for
warnings emitted by `netbox_sqids` at startup.

## Short URL `/s/<sqid>/` returns 404

The short URLs are added by patching `netbox.urls.urlpatterns` at startup.
If patching fails for any reason, the plugin logs a warning and falls back
to the standard `/plugins/sqids/<sqid>/` route.

Things to check:

- Is `monkeypatched_url_prefix` set in `PLUGINS_CONFIG["netbox_sqids"]`,
  or relying on the default `"s"`?
- Is something else mounted at `/s/`? NetBox itself does not use `/s/` by
  default, but custom routes or other plugins might.
- Search the NetBox log for `"Failed to monkey-patch short SQID URLs"`.

The `/plugins/sqids/<sqid>/` and `/api/plugins/sqids/<sqid>/` routes are
always registered through the standard plugin mechanism and should work
even if the patch fails.

## Redirect view returns 404 for a SQID I just generated

The redirect view returns 404 when:

- The token is empty or malformed -- decodes to the wrong number of
  components.
- The encoded content type id does not exist.
- The encoded primary key does not exist for that content type.
- The resolved model has no `get_absolute_url()` (browser view) or no API
  view name (API view).

Walk through `resolve_sqid()` directly to see which step fails:

```python
from netbox_sqids.sqids import resolve_sqid
resolve_sqid("WK1J")
```

If the function returns the object, the redirect view should also work --
unless the object's `get_absolute_url()` is missing.

## SQIDs changed after upgrade

Upgrading the plugin can change the encoding if the new version touches
the alphabet, encoding scheme, or default `min_length`. Check the
[changelog](../changelog.md) entry for the version you upgraded to. While
the plugin is in alpha, encoding-affecting changes are possible between
minor versions and will be flagged explicitly.

If you depend on stable SQIDs across upgrades:

- Pin the plugin version in your requirements.
- Wait for the 1.0 release before relying on long-lived SQID references.
- Keep `min_length` and `blocklist` constant.

## Same object yields different SQIDs on two NetBox instances

SQIDs depend on the `ContentType` id, which is allocated locally per
NetBox instance the first time a model is seen. Two instances can have the
same model at different `ContentType` ids if migrations were run in
different orders, the apps were installed in different orders, or one
instance has additional plugins.

This is expected. SQIDs are stable within a single NetBox database, not
across separate databases. To "carry" identifiers between instances, use
NetBox's natural keys or import-export tooling rather than SQIDs.

## SQID looks like a banned word

The plugin extends the sqids library's default blocklist with `["ck", "sex", "butt"]`
to filter out common offensive substrings. If a SQID slips through that
should not, add the offending word to the `blocklist` setting. Note that
changing the blocklist is encoding-affecting for the affected words.

## Decoding works in a shell but redirect returns 500

If `resolve_sqid()` returns an object and the browser redirect view 500s,
the most likely cause is an exception inside the resolved model's
`get_absolute_url()`. Check NetBox's error log. The plugin only catches
`ValueError` and `ObjectDoesNotExist` -- anything else propagates.
