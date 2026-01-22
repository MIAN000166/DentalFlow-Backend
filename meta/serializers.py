from rest_framework import serializers
from .models import FacebookProfile

class FacebookConnectSerializer(serializers.Serializer):
    """Frontend se humein ye 3 cheezein milengi"""
    access_token = serializers.CharField(required=True)
    page_id = serializers.CharField(required=True)
    page_name = serializers.CharField(required=True)

class PostContentSerializer(serializers.Serializer):
    """Post karne k liye sirf message chahiye (Image optional hai)"""
    message = serializers.CharField(required=True)
    image_url = serializers.URLField(required=False, allow_blank=True)