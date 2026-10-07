from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView

from core.views import follow_link

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/", include("core.urls")),
    # Must stay in sync with the dev proxy regex in frontend/vite.config.ts.
    re_path(r"^(?P<code>[A-Za-z0-9]+)$", follow_link, name="follow-link"),
]

urlpatterns += [
    re_path(r"^(?!api/|django-admin/|assets/).*$", TemplateView.as_view(template_name="index.html")),
]
