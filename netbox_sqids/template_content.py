"""Template extension that shows an object's SQID on its detail page."""

from django.urls import reverse
from django.utils.html import format_html
from netbox.plugins import PluginTemplateExtension


class SqidButton(PluginTemplateExtension):
    """Add a button labelled with the object's SQID that copies its short link.

    ``models`` is left unset so the button renders on every object detail
    page. Objects without a SQID (non-integer primary keys) get no button.
    """

    def buttons(self):
        sqid = getattr(self.context["object"], "sqid", None)
        if sqid is None:
            return ""

        prefix = self.context["config"]["monkeypatched_url_prefix"]
        if prefix is None:
            path = reverse("plugins:netbox_sqids:sqid_redirect", args=[sqid])
        else:
            # The short routes are appended to the root URLconf after Django
            # has built its reverse lookup table, so they cannot be reversed.
            path = f"/{prefix}/{sqid}/"

        return format_html(
            '<a class="btn btn-outline-secondary copy-content" data-clipboard-text="{}" title="Copy short link">'
            '<i class="mdi mdi-link-variant" aria-hidden="true"></i> {}</a>',
            self.context["request"].build_absolute_uri(path),
            sqid,
        )


template_extensions = [SqidButton]
