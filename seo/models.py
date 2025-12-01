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
