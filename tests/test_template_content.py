from types import SimpleNamespace

from django.test import RequestFactory

from netbox_sqids.template_content import SqidButton


def render_button(sqid):
    context = {
        "object": SimpleNamespace(sqid=sqid),
        "request": RequestFactory().get("/dcim/devices/42/"),
    }
    return SqidButton(context).buttons()


class TestSqidButton:
    def test_shows_sqid_and_copies_absolute_short_link(self, settings):
        settings.PLUGINS_CONFIG = {
            **settings.PLUGINS_CONFIG,
            "netbox_sqids": {"monkeypatched_url_prefix": "go"},
        }

        html = render_button("WK1J")

        assert 'data-clipboard-text="http://testserver/go/WK1J/"' in html
        assert "copy-content" in html
        assert "WK1J</a>" in html

    def test_renders_nothing_without_sqid(self):
        assert render_button(None) == ""
