import uuid
from django.db import models
from core.choices import UserType
from user.manager import UserManager
from core.base_model import BaseModel
from django.contrib.auth.models import AbstractBaseUser
from django.core.validators import FileExtensionValidator

class User(AbstractBaseUser):
    """
    Custom user model using email instead of username.
    Includes personal info, user role, phone number, and status.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True, help_text="Optional phone number")
    role = models.SmallIntegerField(choices=UserType.choices, default=UserType.USER)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    username = None
    is_active = models.BooleanField(default=False)
    profile_image = models.ImageField(
        upload_to="user/profile/",
        default="user/profile/default.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg", ".jpg", "jpeg", "png", "webp"]
            )
        ],
        verbose_name="Profile Image",
        blank=True,
        null=True,
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.id}----{self.phone}--{self.first_name}--{self.profile_image}--{self.email} ({self.role})"


class UserWhitelistToken(BaseModel):
    """
    Stores whitelist of user tokens for active sessions.
    Includes token, refresh token, and login metadata.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_tokens')
    access_token_fingerprint = models.TextField()
    refresh_token_fingerprint = models.TextField()
    login_info = models.JSONField()

    def __str__(self):
        return f"User--{self.user.email}--login--info"
