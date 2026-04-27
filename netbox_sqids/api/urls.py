from django.urls import path

from netbox_sqids.api.views import SqidApiRedirectView

urlpatterns = [
    path("<str:sqid>/", SqidApiRedirectView.as_view(), name="sqid_api_redirect"),
]
