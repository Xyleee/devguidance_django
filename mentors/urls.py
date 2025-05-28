from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'mentors'

router = DefaultRouter()
router.register(r'profiles', views.MentorProfileViewSet, basename='profile')
router.register(r'mentorship-requests', views.MentorshipRequestViewSet, basename='mentorship-request')

urlpatterns = [
    path('', include(router.urls)),
    path('browse/', views.MentorListView.as_view(), name='mentor-list'),
]
