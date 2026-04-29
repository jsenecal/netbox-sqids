# Getting Started

This page walks you through installing NetBox SQIDs into an existing NetBox
deployment and confirming the plugin is wired up correctly.

## Requirements

| Dependency | Version  | Notes |
|------------|----------|-------|
| NetBox     | >= 4.5.0 | Plugin uses the standard `PluginConfig` API |
| Python     | >= 3.12  | Matches NetBox 4.5's supported runtimes |
| sqids      | >= 0.4.1 | Pulled in automatically by `pip` |

The plugin makes no assumptions about your underlying database, web server,
or worker configuration. It does not register any background tasks.

## Install

Install the package into the same Python environment that runs NetBox:

```bash
pip install netbox-sqids
```

If you manage NetBox with the official Docker image or a virtualenv, install
the plugin there. The plugin must be importable by the NetBox process.

## Enable the plugin

Add `netbox_sqids` to the `PLUGINS` list in your NetBox `configuration.py`:

```python
PLUGINS = [
    # ... your existing plugins ...
    "netbox_sqids",
]
```

All plugin settings are optional. If you want to override defaults, add a
block to `PLUGINS_CONFIG`:

```python
PLUGINS_CONFIG = {
    "netbox_sqids": {
        "min_length": 4,                   # Minimum SQID string length
        "blocklist": None,                 # Word blocklist (None = built-in)
        "monkeypatched_url_prefix": "s",   # Short URL prefix, or None to disable
    },
}
```

See [Configuration](configuration.md) for the full reference.

## Restart NetBox

Restart the NetBox web and worker processes so the plugin is picked up:

```bash
sudo systemctl restart netbox netbox-rq
```

If you run NetBox in containers, recreate the affected services. The plugin
patches every registered model at startup, so it must be loaded into a fresh
process.

## No migrations required

This plugin does not create any database tables or columns. The `sqid`
property is computed on the fly from the object's content type and primary
key. There is nothing to `manage.py migrate`. If you have a CI step that
verifies migrations are clean, no new migrations should appear when this
plugin is installed.

## Verify the install

### Plugin admin page

Browse to the NetBox UI and open **Admin -> Installed Plugins**. NetBox
SQIDs should appear with version `0.1.1` or higher and status `enabled`.

### Django shell

Open a Django shell from the NetBox install root:

```bash
python manage.py shell
```

Pick any object and access its `sqid`:

```python
>>> from dcim.models import Device
>>> device = Device.objects.first()
>>> device.sqid
'WK1J'
>>> type(device).sqid    # Class access returns the descriptor itself
<netbox_sqids.sqids.SqidDescriptor object at 0x...>
```

If `device.sqid` returns a string, the descriptor is attached and the
encoder is producing output.

### Redirect view

Open `/plugins/sqids/<sqid>/` in your browser, substituting a real SQID
from the previous step:

```
https://netbox.example.com/plugins/sqids/WK1J/
```

You should land on the object's detail page after a 302 redirect. If the
short URL prefix is enabled (default `s`), the same SQID at `/s/WK1J/`
works as well.

## Upgrading

Upgrade with pip and restart NetBox:

```bash
pip install --upgrade netbox-sqids
sudo systemctl restart netbox netbox-rq
```

While the plugin is in alpha, watch the [changelog](../changelog.md) for
encoding-affecting changes. If you have shared SQID links externally,
upgrades that change the alphabet, minimum length, or encoding scheme will
break those links. Such changes will be flagged explicitly in release
notes.

## Uninstall

Remove `netbox_sqids` from `PLUGINS`, drop the entry from `PLUGINS_CONFIG`
if present, restart NetBox, and `pip uninstall netbox-sqids`. Because the
plugin owns no database state, removal leaves nothing behind.

## Next steps

- Learn how to use the new property in your code: [Using SQIDs](using-sqids.md)
- Explore configuration options: [Configuration](configuration.md)
- Browse practical examples: [Recipes](recipes.md)
