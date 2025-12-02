from rest_framework.serializers import ModelSerializer
from seo.models import(
    SERankingKeyword,
    Competitor,
    SimilarKeyword,
    RelatedKeyword,
    DomainHistory
)

class SERankingKeywordSerializer(ModelSerializer):
    class Meta:
        model = SERankingKeyword
        fields = "__all__"

class CompetittorSerializer(ModelSerializer):
    class Meta:
        model = Competitor
        fields = ['domain', 'common_keywords']

class SimilarKeywordSerializer(ModelSerializer):
    class Meta:
        model = SimilarKeyword
        fields = "__all__"

class RelatedKeywordSerializer(ModelSerializer):
    class Meta:
        model = RelatedKeyword
        fields = "__all__"

class DomainHistorySerializer(ModelSerializer):
    class Meta:
        model = DomainHistory
        fields = "__all__"