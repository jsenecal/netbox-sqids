# Configuration

All settings are configured in your NetBox `configuration.py` under `PLUGINS_CONFIG`:

```python
PLUGINS_CONFIG = {
    "netbox_sqids": {
        "min_length": 4,
        "blocklist": None,
        "monkeypatched_url_prefix": "s",
    },
}
```

## Settings Reference

### `min_length`

| | |
|---|---|
| **Type** | `int` |
| **Default** | `4` |

Minimum length of generated SQID strings. The sqids library pads shorter outputs to meet this minimum. Increase this if you prefer longer, more uniform-looking identifiers.

```python
"min_length": 6  # SQIDs will be at least 6 characters
```

### `blocklist`

| | |
|---|---|
| **Type** | `list[str]` or `None` |
| **Default** | `None` |

Word blocklist for the sqids encoder. When a generated SQID contains a blocked word, the library automatically re-encodes to avoid it.

- **`None`** (default) — uses the sqids library's built-in blocklist plus `["ck", "sex", "butt"]`
- **`[]`** (empty list) — disables the blocklist entirely
- **Custom list** — replaces the default blocklist with your own

```python
"blocklist": ["bad", "words"]  # Custom blocklist
"blocklist": []                 # No filtering
```

### `monkeypatched_url_prefix`

| | |
|---|---|
| **Type** | `str` or `None` |
| **Default** | `"s"` |

Prefix for short URLs injected into NetBox's root URL configuration. When set, the plugin adds these routes at startup:

- `/<prefix>/<sqid>/` — browser redirect
- `/api/<prefix>/<sqid>/` — API redirect

Set to `None` to disable short URLs entirely. The standard plugin routes at `/plugins/sqids/<sqid>/` and `/api/plugins/sqids/<sqid>/` always work regardless of this setting.

```python
"monkeypatched_url_prefix": "go"   # /go/WK1J/
"monkeypatched_url_prefix": None   # Disable short URLs
```

## URL Routes Summary

| Route | Type | Condition |
|-------|------|-----------|
| `/plugins/sqids/<sqid>/` | Browser redirect | Always available |
| `/api/plugins/sqids/<sqid>/` | API redirect | Always available |
| `/<prefix>/<sqid>/` | Browser redirect (short) | When `monkeypatched_url_prefix` is set |
| `/api/<prefix>/<sqid>/` | API redirect (short) | When `monkeypatched_url_prefix` is set |
