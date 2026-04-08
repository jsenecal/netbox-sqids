from django.urls import path

from netbox_sqids.views import SqidRedirectView

urlpatterns = [
    path('<str:sqid>/', SqidRedirectView.as_view(), name='sqid_redirect'),
]
