from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import protection
from .models import EXPIRY_OPTIONS, Link
from .serializers import LinkCreateSerializer, LinkSerializer


class HealthView(APIView):
    def get(self, request):
        return Response({"status": "ok"})


def error_response(code, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({"error": code}, status=status_code)


class LinkCreateView(APIView):
    throttle_scope = "link-create"

    def post(self, request):
        serializer = LinkCreateSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            first_error = next(iter(serializer.errors.values()))[0]
            return error_response(first_error.code)
        data = serializer.validated_data

        if not protection.verify_turnstile(data["turnstile_token"]):
            return error_response("captcha_failed")
        try:
            if protection.find_unsafe_urls([data["url"]]):
                return error_response("unsafe_url")
        except protection.SafeBrowsingUnavailable:
            # Fail closed: an unchecked link is exactly what this guards against.
            return error_response("safety_check_unavailable", status.HTTP_503_SERVICE_UNAVAILABLE)

        expires_at = timezone.now() + EXPIRY_OPTIONS[data["expires_in"]]
        link = Link.create_with_unique_code(data["url"], expires_at)
        return Response(LinkSerializer(link).data, status=status.HTTP_201_CREATED)


def follow_link(request, code):
    link = Link.objects.active().filter(code=code).first()
    if link is None:
        # The SPA renders its not-found page. In dev there's no built SPA
        # here (Vite serves it), so fall back to Django's plain 404.
        if not settings.FRONTEND_DIST.is_dir():
            raise Http404
        return TemplateResponse(request, "index.html", status=404)
    # 302, not 301: browsers cache a 301 indefinitely, past the link's expiry.
    return HttpResponseRedirect(link.url)
