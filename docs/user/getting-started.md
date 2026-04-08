# Getting Started

## Installation

Install the plugin from source or your package registry:

```bash
pip install netbox-sqids
```

## Enable the Plugin

Add `netbox_sqids` to your NetBox `configuration.py`:

```python
PLUGINS = ["netbox_sqids"]
```

Optionally configure plugin settings:

```python
PLUGINS_CONFIG = {
    "netbox_sqids": {
        "min_length": 4,             # Minimum SQID string length (default: 4)
        "blocklist": None,           # Custom word blocklist, or None for defaults
        "monkeypatched_url_prefix": "s",  # Short URL prefix, or None to disable
    },
}
```

## Restart NetBox

Restart your NetBox services for the plugin to take effect:

```bash
sudo systemctl restart netbox netbox-rq
```

## Verify Installation

Open a Django shell and check that the `sqid` property is available:

```bash
python manage.py shell
```

```python
>>> from dcim.models import Device
>>> device = Device.objects.first()
>>> device.sqid
'WK1J'
```

You can also visit the admin panel — **NetBox SQIDs** should appear in the installed plugins list.

## No Migrations Required

This plugin does not create any database tables or columns. The `sqid` property is computed on the fly from the object's content type and primary key. There is nothing to migrate.
