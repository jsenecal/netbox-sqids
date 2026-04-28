# NetBox SQIDs

[![PyPI](https://img.shields.io/pypi/v/netbox-sqids.svg)](https://pypi.org/project/netbox-sqids/)
[![Python](https://img.shields.io/pypi/pyversions/netbox-sqids.svg)](https://pypi.org/project/netbox-sqids/)
[![NetBox](https://img.shields.io/badge/NetBox-4.5%2B-success.svg)](https://github.com/netbox-community/netbox)
[![CI](https://github.com/jsenecal/netbox-sqids/actions/workflows/ci.yml/badge.svg)](https://github.com/jsenecal/netbox-sqids/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/jsenecal/netbox-sqids/branch/main/graph/badge.svg)](https://codecov.io/gh/jsenecal/netbox-sqids)
[![Documentation](https://img.shields.io/badge/docs-jsenecal.github.io-blue)](https://jsenecal.github.io/netbox-sqids/)
![Status](https://img.shields.io/badge/status-alpha-orange)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

> **Alpha** -- this plugin is functional but under active development. The API and SQID encoding may change before 1.0.

Short, URL-safe, globally unique identifiers for every NetBox object.

NetBox SQIDs adds a computed `sqid` property to every model in your NetBox instance. SQIDs encode the content type and primary key into a compact string that can be shared, bookmarked, and resolved back to the original object — no database changes required.

## Quick Example

```python
>>> device = Device.objects.first()
>>> device.sqid
'WK1J'

>>> from netbox_sqids.sqids import resolve_sqid
>>> resolve_sqid('WK1J')
<Device: my-switch>
```

Visit `/s/WK1J/` in your browser to be redirected to the device's detail page.

## Features

- **Zero-config** — install and every model gets a `.sqid` property
- **No migrations** — pure computed properties, no database changes
- **Globally unique** — SQIDs are unique across all models
- **URL-safe** — curated 33-character alphabet, no ambiguous characters
- **Redirect views** — resolve any SQID via browser or API
- **Short URLs** — optional root-level routes like `/s/WK1J/`

## Requirements

| Dependency | Version  |
|------------|----------|
| NetBox     | >= 4.5.0 |
| Python     | >= 3.12  |

## Installation

```bash
pip install netbox-sqids
```

Add to your NetBox `configuration.py`:

```python
PLUGINS = ["netbox_sqids"]
```

Restart NetBox. That's it.

## Configuration

All settings are optional:

```python
PLUGINS_CONFIG = {
    "netbox_sqids": {
        "min_length": 4,                      # Minimum SQID length (default: 4)
        "blocklist": None,                    # Word blocklist (None = extended default)
        "monkeypatched_url_prefix": "s",      # Short URL prefix (None to disable)
    },
}
```

## URL Routes

| Route | Description |
|-------|-------------|
| `/plugins/sqids/<sqid>/` | Browser redirect to object |
| `/api/plugins/sqids/<sqid>/` | API redirect to object |
| `/s/<sqid>/` | Short browser redirect (configurable) |
| `/api/s/<sqid>/` | Short API redirect (configurable) |

## Documentation

Full documentation: [jsenecal.github.io/netbox-sqids](https://jsenecal.github.io/netbox-sqids/)

## License

MIT
