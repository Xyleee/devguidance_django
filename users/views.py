from django.shortcuts import render
from django.contrib.auth.models import User
from .serializers import RegisterSerializer
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# Create your views here.

def home(request):
    return render(request, 'users/home.html')

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,) # Allow anyone to register
    serializer_class = RegisterSerializer

class ProtectedView(APIView):
    permission_classes = [IsAuthenticated] # Require authentication

    def get(self, request):
        content = {'message': f'Hello, {request.user.username}! This is protected content.'}
        return Response(content)
