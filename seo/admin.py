from django.contrib import admin
from seo.models import(
    SERankingKeyword,
    Competitor,
    SimilarKeyword,
    RelatedKeyword,
    DomainHistory
)

admin.site.register(SERankingKeyword)
admin.site.register(Competitor)
admin.site.register(SimilarKeyword)
admin.site.register(RelatedKeyword)
admin.site.register(DomainHistory)