from django.urls import path,include 
from rest_framework.routers import DefaultRouter
from user.views import(
    Auth,
    UserProfile,
    PackageView
)

founder = DefaultRouter()
founder.register('user-auth',Auth,basename='user-auth')
founder.register('user-profile',UserProfile,basename='user-profile')
founder.register('user-packages',PackageView,basename='user-packages')

urlpatterns = [
    path('', include(founder.urls)),
]

