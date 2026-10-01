"""Template extension that shows an object's SQID on its detail page."""

from django.utils.html import format_html
from netbox.plugins import PluginTemplateExtension

from netbox_sqids.sqids import short_path


class SqidButton(PluginTemplateExtension):
    """Add a button labelled with the object's SQID that copies its short link.

    ``models`` is left unset so the button renders on every object detail
    page. Objects without a SQID (non-integer primary keys) get no button.
    """

    def buttons(self):
        sqid = getattr(self.context["object"], "sqid", None)
        if sqid is None:
            return ""

        return format_html(
            '<a class="btn btn-outline-secondary copy-content" data-clipboard-text="{}" title="Copy short link">'
            '<i class="mdi mdi-link-variant" aria-hidden="true"></i> {}</a>',
            self.context["request"].build_absolute_uri(short_path(sqid)),
            sqid,
        )


template_extensions = [SqidButton]
