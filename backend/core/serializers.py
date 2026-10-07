from django.core.validators import URLValidator
from rest_framework import serializers

from .models import Link


class LinkSerializer(serializers.ModelSerializer):
    # Django's default URLValidator also accepts ftp/ftps.
    url = serializers.URLField(max_length=2048, validators=[URLValidator(schemes=["http", "https"])])

    class Meta:
        model = Link
        fields = ["code", "url", "expires_at"]
        read_only_fields = ["code", "expires_at"]
