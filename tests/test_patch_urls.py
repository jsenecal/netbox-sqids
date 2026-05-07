"""Regression tests for issue #15.

`_patch_urls()` runs in `AppConfig.ready()`. If it eagerly imports
`netbox.urls`, that transitively imports `netbox.graphql.schema`,
whose module-level `Query` class is built once with whatever plugin
schemas are in the registry at that moment. Plugins whose `ready()`
runs after sqids are silently dropped from the merged GraphQL
schema.

The contract enforced here: `_patch_urls()` must not synchronously
import `netbox.urls` or `netbox.graphql.schema`. The append must be
deferred until after every plugin's `ready()` has completed.
"""

import sys

import pytest
from django.apps import apps
from django.core.signals import request_started

SENTINEL_MODULES = ("netbox.urls", "netbox.graphql.schema")


class TestPatchUrlsIsLazy:
    def setup_method(self):
        self._saved_modules = {m: sys.modules.pop(m, None) for m in SENTINEL_MODULES}
        self._receivers_before = list(request_started.receivers)

    def teardown_method(self):
        for receiver in list(request_started.receivers):
            if receiver not in self._receivers_before:
                request_started.receivers.remove(receiver)
        for name, mod in self._saved_modules.items():
            if mod is not None:
                sys.modules[name] = mod

    def test_patch_urls_does_not_import_netbox_urls(self):
        config = apps.get_app_config("netbox_sqids")

        config._patch_urls()

        for module in SENTINEL_MODULES:
            assert module not in sys.modules, (
                f"Issue #15 regression: _patch_urls() eagerly imported {module} "
                "during ready(). This freezes netbox.graphql.schema.Query with "
                "a partial plugin registry, dropping plugins loaded after sqids."
            )

    @pytest.mark.django_db
    def test_short_routes_appear_after_request_started(self):
        config = apps.get_app_config("netbox_sqids")
        config._patch_urls()

        for name, mod in self._saved_modules.items():
            if mod is not None:
                sys.modules[name] = mod
        self._saved_modules = {}

        import netbox.urls

        request_started.send(sender=self.__class__)

        names = {getattr(p, "name", None) for p in netbox.urls.urlpatterns}
        assert "sqid_short_redirect" in names
        assert "sqid_short_api_redirect" in names
