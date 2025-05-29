from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'mentors'

router = DefaultRouter()
# Primary mentor endpoints - consolidate all mentor functionality here
router.register(r'profiles', views.MentorProfileViewSet, basename='profile')
router.register(r'mentorship-requests', views.MentorshipRequestViewSet, basename='mentorship-request')

urlpatterns = [
    path('', include(router.urls)),
    # Primary mentor browsing endpoint (replaces the duplicate in users app)
    path('browse/', views.MentorListView.as_view(), name='mentor-list'),
]
