from django.contrib import admin
from seo.models import(
    SERankingKeyword,
    Competitor,
    SimilarKeyword,
    RelatedKeyword,
    DomainHistory,
    AuditReport
)

admin.site.register(SERankingKeyword)
admin.site.register(Competitor)
admin.site.register(SimilarKeyword)
admin.site.register(RelatedKeyword)
admin.site.register(DomainHistory)
admin.site.register(AuditReport)