import logging

from netbox.plugins import PluginConfig

__version__ = "0.1.2"

logger = logging.getLogger(__name__)


class NetBoxSqidsConfig(PluginConfig):
    name = "netbox_sqids"
    verbose_name = "NetBox SQIDs"
    description = "Short, URL-safe, globally unique identifiers for every NetBox object"
    version = __version__
    author = "Jonathan Senecal"
    author_email = "contact@jonathansenecal.com"
    base_url = "sqids"
    default_settings = {
        "min_length": 4,
        "blocklist": None,
        "monkeypatched_url_prefix": "s",
    }

    def ready(self):
        super().ready()
        self._patch_models()
        self._patch_urls()
        logger.info("%s plugin loaded", self.name)

    def _patch_models(self):
        from django.apps import apps

        from netbox_sqids.sqids import SqidDescriptor

        for model in apps.get_models():
            model.add_to_class("sqid", SqidDescriptor())

    def _patch_urls(self):
        from django.conf import settings
        from django.core.signals import request_started

        plugin_settings = settings.PLUGINS_CONFIG.get("netbox_sqids", {})
        prefix = plugin_settings.get("monkeypatched_url_prefix", self.default_settings["monkeypatched_url_prefix"])
        if prefix is None:
            return

        if getattr(self, "_url_patch_pending", False):
            return

        # Defer the actual patch until after every plugin's ready() has run.
        # Importing netbox.urls during ready() transitively imports
        # netbox.graphql.schema, freezing its Query MRO with a partial plugin
        # registry and dropping plugins loaded after sqids. See issue #15.
        def _install_short_routes(sender, **kwargs):
            try:
                import netbox.urls
                from django.urls import path

                from netbox_sqids.api.views import SqidApiRedirectView
                from netbox_sqids.views import SqidRedirectView

                names = {getattr(p, "name", None) for p in netbox.urls.urlpatterns}
                if "sqid_short_redirect" not in names:
                    netbox.urls.urlpatterns.append(
                        path(f"{prefix}/<str:sqid>/", SqidRedirectView.as_view(), name="sqid_short_redirect")
                    )
                if "sqid_short_api_redirect" not in names:
                    netbox.urls.urlpatterns.append(
                        path(
                            f"api/{prefix}/<str:sqid>/",
                            SqidApiRedirectView.as_view(),
                            name="sqid_short_api_redirect",
                        )
                    )
            except Exception:
                logger.warning(
                    "Failed to monkey-patch short SQID URLs. The standard /plugins/sqids/ routes still work.",
                    exc_info=True,
                )
            finally:
                request_started.disconnect(_install_short_routes)
                self._url_patch_pending = False

        self._url_patch_pending = True
        request_started.connect(_install_short_routes, weak=False)


config = NetBoxSqidsConfig
