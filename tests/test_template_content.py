from types import SimpleNamespace

from django.test import RequestFactory

from netbox_sqids.template_content import SqidButton


def render_button(sqid, prefix="s"):
    context = {
        "object": SimpleNamespace(sqid=sqid),
        "request": RequestFactory().get("/dcim/devices/42/"),
        "config": {"monkeypatched_url_prefix": prefix},
    }
    return SqidButton(context).buttons()


class TestSqidButton:
    def test_shows_sqid_and_copies_short_link(self):
        html = render_button("WK1J")

        assert 'data-clipboard-text="http://testserver/s/WK1J/"' in html
        assert "copy-content" in html
        assert "WK1J</a>" in html

    def test_custom_prefix_is_used_in_copied_link(self):
        html = render_button("WK1J", prefix="go")

        assert 'data-clipboard-text="http://testserver/go/WK1J/"' in html

    def test_falls_back_to_plugin_route_when_prefix_disabled(self):
        html = render_button("WK1J", prefix=None)

        assert 'data-clipboard-text="http://testserver/plugins/sqids/WK1J/"' in html

    def test_renders_nothing_without_sqid(self):
        assert render_button(None) == ""
