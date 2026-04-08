from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponseRedirect
from django.views import View

from netbox_sqids.sqids import resolve_sqid


class SqidRedirectView(View):
    def get(self, request, sqid):
        try:
            obj = resolve_sqid(sqid)
        except (ValueError, ObjectDoesNotExist) as exc:
            raise Http404 from exc

        if not hasattr(obj, 'get_absolute_url'):
            raise Http404

        return HttpResponseRedirect(obj.get_absolute_url())
