from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    RegisterView, 
    ProtectedView, 
    StudentProfileViewSet, 
    MentorProfileViewSet,
    StudentProjectViewSet,
    MentorshipRequestViewSet,
    MentorListView,
    MessageAPIView,
    MessageStreamView
)

app_name = 'users'

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'student-profiles', StudentProfileViewSet, basename='student-profile')
router.register(r'mentor-profiles', MentorProfileViewSet, basename='mentor-profile')
router.register(r'student-projects', StudentProjectViewSet, basename='student-project')
router.register(r'mentorship-requests', MentorshipRequestViewSet, basename='mentorship-request')

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('protected/', ProtectedView.as_view(), name='protected_view'),
    path('api/', include(router.urls)),
    path('api/mentors/', MentorListView.as_view(), name='mentor-list'),
    path('messages/', MessageAPIView.as_view(), name='send_message'),
    path('messages/<int:user_id>/', MessageAPIView.as_view(), name='message_history'),
    path('messages/stream/<int:user_id>/', MessageStreamView.as_view(), name='message_stream'),
]
