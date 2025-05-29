from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    RegisterView, 
    ProtectedView, 
    MessageAPIView,
    MessageStreamView,
    RateLimitedRegisterView,
    RateLimitedTokenObtainPairView,
    RateLimitedTokenRefreshView,
    SimpleTestView
)

app_name = 'users'

# Remove duplicated router registrations - these will be handled in their respective apps
router = DefaultRouter()

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', RateLimitedRegisterView.as_view(), name='register'),
    path('protected/', ProtectedView.as_view(), name='protected_view'),
    # Remove the duplicated API routes
    path('messages/', MessageAPIView.as_view(), name='send_message'),
    path('messages/<int:user_id>/', MessageAPIView.as_view(), name='message_history'),
    path('messages/stream/<int:user_id>/', MessageStreamView.as_view(), name='message_stream'),
    path('test/', views.test_endpoint, name='test'),
    path('api-test/', SimpleTestView.as_view(), name='api-test'),
    path('simple/', views.super_simple_test, name='simple'),
]
