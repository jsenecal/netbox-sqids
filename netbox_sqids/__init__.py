import logging

from netbox.plugins import PluginConfig

__version__ = "0.1.0"

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

    def _patch_models(self):
        from django.apps import apps

        from netbox_sqids.sqids import SqidDescriptor

        for model in apps.get_models():
            model.add_to_class("sqid", SqidDescriptor())

    def _patch_urls(self):
        from django.conf import settings

        plugin_settings = settings.PLUGINS_CONFIG.get("netbox_sqids", {})
        prefix = plugin_settings.get("monkeypatched_url_prefix", self.default_settings["monkeypatched_url_prefix"])
        if prefix is None:
            return

        try:
            import netbox.urls
            from django.urls import path

            from netbox_sqids.api.views import SqidApiRedirectView
            from netbox_sqids.views import SqidRedirectView

            netbox.urls.urlpatterns.append(
                path(f"{prefix}/<str:sqid>/", SqidRedirectView.as_view(), name="sqid_short_redirect")
            )
            netbox.urls.urlpatterns.append(
                path(f"api/{prefix}/<str:sqid>/", SqidApiRedirectView.as_view(), name="sqid_short_api_redirect")
            )
        except Exception:
            logger.warning(
                "Failed to monkey-patch short SQID URLs. The standard /plugins/sqids/ routes still work.", exc_info=True
            )


config = NetBoxSqidsConfig
