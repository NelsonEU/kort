from urllib.parse import urlsplit

from django.core.validators import URLValidator
from rest_framework import serializers

from . import protection
from .models import EXPIRY_OPTIONS, Link


class LinkCreateSerializer(serializers.Serializer):
    # Django's default URLValidator also accepts ftp/ftps.
    url = serializers.URLField(max_length=2048, validators=[URLValidator(schemes=["http", "https"])])
    expires_in = serializers.ChoiceField(choices=list(EXPIRY_OPTIONS))
    turnstile_token = serializers.CharField(max_length=2048)

    def validate_url(self, value):
        host = urlsplit(value).hostname or ""
        if protection.is_blocked_host(host, self.context["request"].get_host()):
            raise serializers.ValidationError("This domain can't be shortened.", code="blocked_domain")
        return value


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ["code", "url", "expires_at"]
