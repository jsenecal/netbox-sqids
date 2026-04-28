"""API redirect view for resolving SQIDs to REST API detail endpoints."""

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.views import View
from utilities.views import get_viewname

from netbox_sqids.sqids import resolve_sqid


class SqidApiRedirectView(View):
    """Resolve a SQID and 302 redirect to the object's REST API detail endpoint."""

    def get(self, request, sqid):
        try:
            obj = resolve_sqid(sqid)
        except (ValueError, ObjectDoesNotExist) as exc:
            raise Http404 from exc

        try:
            viewname = get_viewname(obj, action="detail", rest_api=True)
            url = reverse(viewname, kwargs={"pk": obj.pk})
        except (AttributeError, Exception) as exc:
            raise Http404 from exc

        return HttpResponseRedirect(url)
