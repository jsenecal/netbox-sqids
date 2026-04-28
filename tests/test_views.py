from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory

from netbox_sqids.api.views import SqidApiRedirectView
from netbox_sqids.views import SqidRedirectView


class TestSqidRedirectView:
    def setup_method(self):
        self.factory = RequestFactory()

    @patch("netbox_sqids.views.resolve_sqid")
    def test_redirects_to_absolute_url(self, mock_resolve):
        mock_obj = MagicMock()
        mock_obj.get_absolute_url.return_value = "/dcim/devices/42/"
        mock_resolve.return_value = mock_obj

        request = self.factory.get("/plugins/sqids/ABCD/")
        response = SqidRedirectView.as_view()(request, sqid="ABCD")

        assert response.status_code == 302
        assert response.url == "/dcim/devices/42/"

    @patch("netbox_sqids.views.resolve_sqid")
    def test_invalid_sqid_returns_404(self, mock_resolve):
        from django.http import Http404

        mock_resolve.side_effect = ValueError("Invalid SQID")

        request = self.factory.get("/plugins/sqids/XXXX/")
        with pytest.raises(Http404):
            SqidRedirectView.as_view()(request, sqid="XXXX")

    @patch("netbox_sqids.views.resolve_sqid")
    def test_object_not_found_returns_404(self, mock_resolve):
        from django.core.exceptions import ObjectDoesNotExist
        from django.http import Http404

        mock_resolve.side_effect = ObjectDoesNotExist()

        request = self.factory.get("/plugins/sqids/ABCD/")
        with pytest.raises(Http404):
            SqidRedirectView.as_view()(request, sqid="ABCD")

    @patch("netbox_sqids.views.resolve_sqid")
    def test_no_get_absolute_url_returns_404(self, mock_resolve):
        from django.http import Http404

        mock_obj = MagicMock(spec=[])  # no get_absolute_url
        mock_resolve.return_value = mock_obj

        request = self.factory.get("/plugins/sqids/ABCD/")
        with pytest.raises(Http404):
            SqidRedirectView.as_view()(request, sqid="ABCD")


class TestSqidApiRedirectView:
    def setup_method(self):
        self.factory = RequestFactory()

    @patch("netbox_sqids.api.views.reverse")
    @patch("netbox_sqids.api.views.get_viewname")
    @patch("netbox_sqids.api.views.resolve_sqid")
    def test_redirects_to_api_url(self, mock_resolve, mock_get_viewname, mock_reverse):
        mock_obj = MagicMock()
        mock_obj.pk = 42
        mock_resolve.return_value = mock_obj
        mock_get_viewname.return_value = "dcim-api:device-detail"
        mock_reverse.return_value = "/api/dcim/devices/42/"

        request = self.factory.get("/api/plugins/sqids/ABCD/")
        response = SqidApiRedirectView.as_view()(request, sqid="ABCD")

        assert response.status_code == 302
        assert response.url == "/api/dcim/devices/42/"
        mock_get_viewname.assert_called_once_with(mock_obj, action="detail", rest_api=True)
        mock_reverse.assert_called_once_with("dcim-api:device-detail", kwargs={"pk": 42})

    @patch("netbox_sqids.api.views.resolve_sqid")
    def test_invalid_sqid_returns_404(self, mock_resolve):
        from django.http import Http404

        mock_resolve.side_effect = ValueError("Invalid SQID")

        request = self.factory.get("/api/plugins/sqids/XXXX/")
        with pytest.raises(Http404):
            SqidApiRedirectView.as_view()(request, sqid="XXXX")

    @patch("netbox_sqids.api.views.resolve_sqid")
    def test_object_not_found_returns_404(self, mock_resolve):
        from django.core.exceptions import ObjectDoesNotExist
        from django.http import Http404

        mock_resolve.side_effect = ObjectDoesNotExist()

        request = self.factory.get("/api/plugins/sqids/ABCD/")
        with pytest.raises(Http404):
            SqidApiRedirectView.as_view()(request, sqid="ABCD")

    @patch("netbox_sqids.api.views.get_viewname")
    @patch("netbox_sqids.api.views.resolve_sqid")
    def test_no_api_viewname_returns_404(self, mock_resolve, mock_get_viewname):
        from django.http import Http404

        mock_obj = MagicMock()
        mock_resolve.return_value = mock_obj
        mock_get_viewname.side_effect = AttributeError()

        request = self.factory.get("/api/plugins/sqids/ABCD/")
        with pytest.raises(Http404):
            SqidApiRedirectView.as_view()(request, sqid="ABCD")
