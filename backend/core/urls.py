from django.urls import path

from .views import HealthView, LinkCreateView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("links/", LinkCreateView.as_view(), name="link-create"),
]
