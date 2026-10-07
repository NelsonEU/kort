from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView

from core.views import follow_link

urlpatterns = [
    path("api/", include("core.urls")),
    # Must stay in sync with the dev proxy regex in frontend/vite.config.ts.
    re_path(r"^(?P<code>[A-Za-z0-9]+)$", follow_link, name="follow-link"),
]

if settings.DEBUG:
    urlpatterns.insert(0, path("django-admin/", admin.site.urls))

urlpatterns += [
    re_path(r"^(?!api/|assets/).*$", TemplateView.as_view(template_name="index.html")),
]
