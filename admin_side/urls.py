from django.urls import path, include
from rest_framework.routers import DefaultRouter
from admin_side.views import (
    Auth,
    AdminProfile,
    PackageAPI
)

admin_router = DefaultRouter()

admin_router.register(r'admin-auth', Auth, basename='admin-auth')
admin_router.register(r'admin-profile', AdminProfile, basename='admin-profile')
admin_router.register(r'admin-packages', PackageAPI, basename='admin-packages')

urlpatterns = [
    path('', include(admin_router.urls)),
]
