from django.contrib import admin

from .models import Link


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ["code", "url", "created_at", "expires_at", "disabled_at"]
    search_fields = ["code", "url"]
