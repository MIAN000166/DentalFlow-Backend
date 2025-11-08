import uuid
import stripe
from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from user.models import User
from core.token import (
    UserGenerateToken,
    user_delete_token
)
from core.helpers import(
    handle_serializer_exception
)
from core.permission import(
    UserAuthenticated
)
from admin_side.models import Package, UserPackage
from django.conf import settings
from core.choices import UserType
from user.serializer import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    GetUserProfileSerializer,
    UpdateProfileSerializer,
    GetAllPackageSerializer
)

stripe.api_key = settings.STRIPE_SECRET_KEY

class Auth(ModelViewSet):

    @action(detail=False, methods=['POST'])
    def signup(self, request):
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save() 
                access_token, refresh_token, user = UserGenerateToken(user=user, request=request)

                user_data = {
                    "id": str(user.id),
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "role": user.role,
                    "phone":user.phone,
                }

                return Response({
                    "status": True,
                    "message": "Account Created and Logged in Successfully!",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "data": user_data
                }, status=status.HTTP_201_CREATED)

            return Response({
                "status": False,
                "message": handle_serializer_exception(serializer)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": False,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'])
    def login(self, request):
        try:
            serializer = UserLoginSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data["user"]
                if user.role == UserType.USER:
                    access_token, refresh_token, user = UserGenerateToken(user=user, request=request)
                    user_data = {
                        "id": str(user.id),
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "role": user.role,
                        "phone":user.phone,
                    }

                    return Response({
                        "status": True,
                        "message": "Login successful",
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "data": user_data
                    }, status=status.HTTP_200_OK)

                return Response({
                    "status": False,
                    "message": "Only users are allowed to login here."
                }, status=status.HTTP_403_FORBIDDEN)

            return Response({
                "status": False,
                "message": handle_serializer_exception(serializer)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)



class UserProfile(ModelViewSet):

    @action(detail=False,methods=['GET'],permission_classes=[UserAuthenticated])
    def profile(self,request):

        try:
            user = request.user

            serializer = GetUserProfileSerializer(user)

            return Response ({
                "status":True,
                "data":serializer.data,
            },status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False,methods=['PATCH'],permission_classes=[UserAuthenticated])
    def update_profile(self,request):
        try:
            user = request.user
            serializer = UpdateProfileSerializer(user,data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response ({
                    "status":True,
                    "data":serializer.data,
                },status=status.HTTP_200_OK)
            return Response({"status":False,"message":handle_serializer_exception(serializer)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PackageView(ModelViewSet):
    """User-side Package View"""

    @action(detail=False, methods=['GET'], permission_classes=[UserAuthenticated])
    def get_all_packages(self, request):
        """Fetch all available packages with features"""
        try:
            packages = Package.objects.prefetch_related('features').order_by('price_per_month')
            serializer = GetAllPackageSerializer(packages, many=True)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "message": f"Error fetching packages: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'],permission_classes=[UserAuthenticated])
    def stripe_checkout(self, request):
        package_id = request.data.get('package_id')
        user = request.user

        try:
            package = Package.objects.get(id=package_id)
        except Package.DoesNotExist:
            return Response({"status": False, "message": "Package not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Stripe Checkout session create karna
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': package.name,
                            'description': package.description,
                        },
                        'unit_amount': int(package.price_per_month * 100),  # cents me
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url="http://localhost:8000/success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url="http://localhost:8000/cancel",
                metadata={
                    "user_id": str(user.id),
                    "package_id": str(package.id)
                }
            )

            return Response({
                "status": True,
                "checkout_url": checkout_session.url
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    @method_decorator(csrf_exempt)
    @action(detail=False, methods=["POST"])
    def stripe_webhook(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return Response({'status': False, 'message': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError:
            return Response({'status': False, 'message': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            user_id = session['metadata'].get('user_id')
            package_id = session['metadata'].get('package_id')
            print("user   _____________________________________ ",user_id)
            print("package   _____________________________________ ",package_id)
            # Validate UUID
            try:
                user_uuid = uuid.UUID(user_id)
                package_uuid = uuid.UUID(package_id)
            except (ValueError, TypeError):
                return Response({'status': False, 'message': 'Invalid user_id or package_id in metadata'}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch user and package
            try:
                user = User.objects.get(id=user_uuid)
                package = Package.objects.get(id=package_uuid)
            except (User.DoesNotExist, Package.DoesNotExist):
                return Response({'status': False, 'message': 'User or Package not found'}, status=status.HTTP_404_NOT_FOUND)

            end_date = timezone.now() + timedelta(days=30)

            UserPackage.objects.update_or_create(
                user=user,
                package=package,
                defaults={
                    'start_date': timezone.now(),
                    'end_date': end_date,
                    'is_active': True,
                    'payment_status': 'paid'
                }
            )

        return Response({'status': True, 'message': 'Webhook received'}, status=status.HTTP_200_OK)

