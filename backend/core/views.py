from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Link
from .serializers import LinkSerializer


class HealthView(APIView):
    def get(self, request):
        return Response({"status": "ok"})


class LinkCreateView(APIView):
    throttle_scope = "link-create"

    def post(self, request):
        serializer = LinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        link = Link.create_with_unique_code(serializer.validated_data["url"])
        return Response(LinkSerializer(link).data, status=status.HTTP_201_CREATED)


def follow_link(request, code):
    link = Link.objects.filter(code=code, expires_at__gt=timezone.now()).first()
    if link is None:
        # The SPA renders its not-found page. In dev there's no built SPA
        # here (Vite serves it), so fall back to Django's plain 404.
        if not settings.FRONTEND_DIST.is_dir():
            raise Http404
        return TemplateResponse(request, "index.html", status=404)
    # 302, not 301: browsers cache a 301 indefinitely, past the link's expiry.
    return HttpResponseRedirect(link.url)
