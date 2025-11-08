from passlib.hash import django_pbkdf2_sha256 as handler
from user.models import User
from core.utils import check_password_requirements
from core.choices import UserType
from admin_side.models import Package,PackageFeature
from rest_framework.serializers import(
    ModelSerializer,
    CharField,
    ValidationError,
    SerializerMethodField
)



class UserRegistrationSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ['id','first_name','last_name','email','phone','password','role','is_active']

    def validate_role(self, role):
        if role != UserType.USER:
            raise ValidationError("Only founder role is allowed for registration.")
        return role

    def validate_password(self,password):
        return handler.hash(password)


class UserLoginSerializer(ModelSerializer):
    email = CharField()
    password = CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email','password']

    def validate(self, attrs):

        email = attrs.get('email')
        password = attrs.get('password')

        user = User.objects.filter(email=email).first()

        if not user:
            raise ValidationError("Email not found . . .")

        verify_pass = handler.verify(password,user.password)

        if not verify_pass:
            raise ValidationError("wrong password")

        attrs["user"] = user

        return attrs

class GetUserProfileSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ['id','first_name','last_name','email','phone','role','profile_image']


class UpdateProfileSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ['id','first_name','last_name','email','phone','role','profile_image']

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.profile_image = validated_data.get('profile_image', instance.profile_image)

        instance.save()
        return instance

class PackageFeatureSerializer(ModelSerializer):
    class Meta:
        model = PackageFeature
        fields = ["id", "name"]

class GetAllPackageSerializer(ModelSerializer):
    features = PackageFeatureSerializer(many=True, read_only=True)

    class Meta:
        model = Package
        fields = [
            "id",
            "name",
            "description",
            "price_per_month",
            "is_popular",
            "features"
        ]
