from django.db import models
from core.base_model import BaseModel
from user.models import User

class SERankingKeyword(BaseModel):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    keyword = models.CharField(max_length=255)
    domain = models.CharField(max_length=255)
    block_type = models.CharField(max_length=50, blank=True, null=True)
    block_position = models.IntegerField(blank=True, null=True)
    position = models.IntegerField(blank=True, null=True)
    prev_pos = models.IntegerField(blank=True, null=True)
    volume = models.IntegerField(blank=True, null=True)
    cpc = models.FloatField(blank=True, null=True)
    competition = models.FloatField(blank=True, null=True)
    url = models.URLField(max_length=500, blank=True, null=True)
    difficulty = models.IntegerField(blank=True, null=True)
    total_sites = models.IntegerField(blank=True, null=True)
    traffic = models.IntegerField(blank=True, null=True)
    traffic_percent = models.FloatField(blank=True, null=True)
    price = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.keyword} - {self.domain}"

class Competitor(BaseModel):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    domain = models.CharField(max_length=255)
    common_keywords = models.IntegerField()

    def __str__(self):
        return self.domain
    
class SimilarKeyword(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    keyword = models.CharField(max_length=255)
    cpc = models.FloatField(default=0)
    difficulty = models.IntegerField(default=0)
    volume = models.IntegerField(default=0)
    competition = models.FloatField(default=0)
    serp_features = models.JSONField(default=list)
    intents = models.JSONField(default=list)
    history_trend = models.JSONField(default=dict)

    def __str__(self):
        return self.keyword

class RelatedKeyword(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    keyword = models.CharField(max_length=255)
    cpc = models.FloatField(default=0)
    difficulty = models.IntegerField(default=0)
    volume = models.IntegerField(default=0)
    competition = models.FloatField(default=0)
    serp_features = models.JSONField(default=list)
    intents = models.JSONField(default=list)
    history_trend = models.JSONField(default=dict)

    def __str__(self):
        return self.keyword
    
class DomainHistory(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    domain = models.CharField(max_length=255)
    year = models.IntegerField()
    month = models.IntegerField()
    keywords_count = models.IntegerField()
    traffic_sum = models.IntegerField()
    top1_2 = models.IntegerField()
    top3_5 = models.IntegerField()
    top6_8 = models.IntegerField()
    top9_11 = models.IntegerField()
    price_sum = models.FloatField()

    def __str__(self):
        return f"{self.domain} - {self.year}/{self.month}"