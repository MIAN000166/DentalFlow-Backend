from django.db import models
from core.base_model import BaseModel
from user.models import User

class Package(BaseModel):
    PACKAGE_TYPE_CHOICES = [
        ('basic', 'Basic'),
        ('professional', 'Professional'),
        ('premium', 'Premium'),
    ]
    admin = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_packages"
    )
    name = models.CharField(max_length=100, choices=PACKAGE_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)
    price_per_month = models.DecimalField(max_digits=10, decimal_places=3)
    is_popular = models.BooleanField(default=False)  

    def __str__(self):
        return f"{self.name} ({self.admin.email})" if hasattr(self.admin, 'email') else self.name



class PackageFeature(BaseModel):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name="features")
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.package.name} - {self.name}"



class UserPackage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name="subscriptions")
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    payment_status = models.CharField(
        max_length=50,
        choices=[
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )

    def __str__(self):
        return f"{self.user} - {self.package.name}"

    class Meta:
        verbose_name = "User Package Subscription"
        verbose_name_plural = "User Package Subscriptions"



class Feature(BaseModel):
    admin = models.ForeignKey(User,on_delete=models.CASCADE,related_name='features')
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return f"{self.admin.first_name} - {self.name}"

