# Configuration

All settings are configured in your NetBox `configuration.py` under
`PLUGINS_CONFIG`:

```python
PLUGINS_CONFIG = {
    "netbox_sqids": {
        "min_length": 4,
        "blocklist": None,
        "monkeypatched_url_prefix": "s",
    },
}
```

Every setting is optional. If you omit `PLUGINS_CONFIG["netbox_sqids"]`
entirely, the defaults below apply.

## Settings reference

### `min_length`

| | |
|---|---|
| **Type** | `int` |
| **Default** | `4` |
| **Encoding-affecting** | Yes |

Minimum length of generated SQID strings. The sqids library pads shorter
outputs to meet this minimum by injecting additional characters from the
alphabet, so the encoded string still decodes back to the same two
integers. Increasing the minimum produces longer, more uniform IDs:

```python
"min_length": 6   # SQIDs will be at least 6 characters
```

Changing `min_length` produces different SQIDs for the same `(content_type_id, pk)` pair.
Existing IDs become invalid after the change. Pick a value during initial
deployment and stick with it.

### `blocklist`

| | |
|---|---|
| **Type** | `list[str]` or `None` |
| **Default** | `None` |
| **Encoding-affecting** | Yes (in rare cases) |

Word blocklist for the sqids encoder. When a generated SQID contains a
blocked word, the library re-encodes with a different internal seed until
the output is clean.

- **`None`** (default) -- uses the sqids library's built-in English
  blocklist plus `["ck", "sex", "butt"]`.
- **`[]`** (empty list) -- disables filtering entirely. Generated IDs may
  contain any characters from the alphabet.
- **Custom list** -- replaces the default blocklist with your own. Useful
  if you want to extend the default with domain-specific terms or to
  localize the filter for non-English deployments.

```python
"blocklist": ["bad", "words", "internal-codename"]   # Custom blocklist
"blocklist": []                                      # No filtering
```

Most of the time, changing the blocklist does not affect existing SQIDs --
only IDs that happen to spell a now-blocked (or now-allowed) word will
shift. In practice this is rare for short IDs but more likely for higher
`min_length` values.

### `monkeypatched_url_prefix`

| | |
|---|---|
| **Type** | `str` or `None` |
| **Default** | `"s"` |
| **Encoding-affecting** | No |

Prefix for short URLs injected into NetBox's root URL configuration. When
set, the plugin appends two routes to `netbox.urls.urlpatterns` at startup:

- `/<prefix>/<sqid>/` -- browser redirect
- `/api/<prefix>/<sqid>/` -- API redirect

Set to `None` to disable short URLs entirely. The standard plugin routes
at `/plugins/sqids/<sqid>/` and `/api/plugins/sqids/<sqid>/` always work
regardless of this setting.

```python
"monkeypatched_url_prefix": "go"   # /go/WK1J/
"monkeypatched_url_prefix": "x"    # /x/WK1J/
"monkeypatched_url_prefix": None   # Disable short URLs
```

#### Choosing a prefix safely

The short URL is patched onto the root URL config. If your NetBox install
already has another route at `/<prefix>/`, the conflict can lead to one or
the other shadowing the request. Practical advice:

- Default `s` is short and almost never collides with NetBox built-ins.
- Avoid common NetBox path prefixes like `dcim`, `ipam`, `tenancy`,
  `extras`, `users`, `circuits`, `virtualization`, `wireless`, `core`,
  `plugins`, `api`, `admin`, `static`, `media`, `accounts`, `login`,
  `logout`, `search`.
- If in doubt, set `monkeypatched_url_prefix` to `None` and just use the
  longer `/plugins/sqids/<sqid>/` route.

## URL routes summary

| Route | Type | Condition |
|-------|------|-----------|
| `/plugins/sqids/<sqid>/` | Browser redirect | Always available |
| `/api/plugins/sqids/<sqid>/` | API redirect | Always available |
| `/<prefix>/<sqid>/` | Browser redirect (short) | When `monkeypatched_url_prefix` is set |
| `/api/<prefix>/<sqid>/` | API redirect (short) | When `monkeypatched_url_prefix` is set |

## Encoding-affecting changes

A change is "encoding-affecting" if it makes the encoder produce a
different output for the same `(content_type_id, pk)` pair. Today that
covers:

- Changing `min_length`.
- Changing `blocklist` (only impacts IDs that previously matched a blocked
  word, or now match one).
- Plugin upgrades that touch the alphabet or call structure.

Because the plugin is in alpha, future versions may also alter the
encoding scheme itself. Such changes are flagged in the
[changelog](../changelog.md). When sharing SQIDs externally (in tickets,
labels, runbooks, ...), be aware that encoding-affecting changes will
break those references.

## Where settings are read

`PLUGINS_CONFIG["netbox_sqids"]` is read once, on first use, when the
plugin's lazy `Sqids` singleton is constructed. To pick up changes you
must restart the NetBox process. Editing settings in a running shell does
not take effect until the singleton is rebuilt or the process is
recycled.

## Defaults

The literal defaults defined in `NetBoxSqidsConfig.default_settings`:

```python
default_settings = {
    "min_length": 4,
    "blocklist": None,
    "monkeypatched_url_prefix": "s",
}
```
