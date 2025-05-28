from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'students'

router = DefaultRouter()
router.register(r'profiles', views.StudentProfileViewSet, basename='profile')
router.register(r'projects', views.StudentProjectViewSet, basename='project')

urlpatterns = [
    path('', include(router.urls)),
]
