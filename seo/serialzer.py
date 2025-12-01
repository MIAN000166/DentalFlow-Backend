from rest_framework.serializers import ModelSerializer
from .models import SERankingKeyword

class SERankingKeywordSerializer(ModelSerializer):
    class Meta:
        model = SERankingKeyword
        fields = "__all__"
