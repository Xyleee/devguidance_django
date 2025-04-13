from django.urls import path
from . import views
from .views import RegisterView, ProtectedView

app_name = 'users'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('protected/', ProtectedView.as_view(), name='protected_view'),
]
