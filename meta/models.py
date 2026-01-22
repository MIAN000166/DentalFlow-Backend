from django.db import models

from django.contrib.auth.models import User

class FacebookProfile(models.Model):
    # User ko link kar rahe hain taa ke pata ho ye kis client ka data hai
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='facebook')
    
    # Ye wo 'Chabi' (Token) hai jo hum Facebook se le kar save karenge
    access_token = models.TextField()
    
    # Ye wo Page hai jo User ne select kiya hai (e.g. mo_elias_d)
    page_id = models.CharField(max_length=50, blank=True, null=True)
    page_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Time stamp (kabhi debug karna para to kaam ayega)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"FB Connection: {self.user.username} - {self.page_name}"