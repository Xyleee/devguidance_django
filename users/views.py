from django.shortcuts import render
from django.contrib.auth.models import User
from .serializers import (
    RegisterSerializer, 
    StudentProfileSerializer, 
    StudentProjectSerializer, 
    MentorProfileSerializer,
    MentorListSerializer,
    MentorshipRequestSerializer,
    MessageSerializer
)
from rest_framework import generics, viewsets, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import StudentProfile, StudentProject, MentorProfile, MentorshipRequest, Message
from .permissions import IsOwnerOrReadOnly, IsStudent, IsMentor, CanManageRequest, IsMessageAllowed
from rest_framework.permissions import AllowAny
from django.db import models
from django.db.models import Q
from django.http import StreamingHttpResponse
import json
import time
from django.conf import settings
import os
from django.utils import timezone
from .rate_limiting import rate_limit
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Create your views here.

def home(request):
    return render(request, 'users/home.html')

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Customize the response based on user type
        user_type = request.data.get('user_type')
        profile_type = f"{user_type}_profile"
        
        # Get the appropriate profile
        if user_type == 'student':
            profile = user.student_profile
            profile_serializer = StudentProfileSerializer(profile)
        else:
            profile = user.mentor_profile
            profile_serializer = MentorProfileSerializer(profile)
            
        return Response({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            },
            "profile": profile_serializer.data,
            "message": f"User registered successfully as a {user_type}."
        }, status=status.HTTP_201_CREATED)

class ProtectedView(APIView):
    permission_classes = [IsAuthenticated] # Require authentication

    def get(self, request):
        content = {'message': f'Hello, {request.user.username}! This is protected content.'}
        return Response(content)

class StudentProfileViewSet(viewsets.ModelViewSet):
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'tech_stack']
    
    def get_queryset(self):
        return StudentProfile.objects.filter(user=self.request.user)
    
    def get_object(self):
        return get_object_or_404(StudentProfile, user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        try:
            profile = StudentProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except StudentProfile.DoesNotExist:
            return Response({"detail": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

class StudentProjectViewSet(viewsets.ModelViewSet):
    serializer_class = StudentProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly, IsStudent]
    
    def get_queryset(self):
        return StudentProject.objects.filter(student__user=self.request.user)
    
    def perform_create(self, serializer):
        student_profile = get_object_or_404(StudentProfile, user=self.request.user)
        serializer.save(student=student_profile)

class MentorProfileViewSet(viewsets.ModelViewSet):
    serializer_class = MentorProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'expertise_tags']
    
    def get_queryset(self):
        # For list view, return all mentors for general browsing
        if self.action == 'list':
            return MentorProfile.objects.all()
        # For detailed operations, only return the user's own profile
        return MentorProfile.objects.filter(user=self.request.user)
    
    def get_object(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return get_object_or_404(MentorProfile, user=self.request.user)
        # For retrieve, use the pk from the URL
        return super().get_object()
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        try:
            profile = MentorProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except MentorProfile.DoesNotExist:
            return Response({"detail": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
            
    @action(detail=False, methods=['get'])
    def by_expertise(self, request):
        expertise = request.query_params.get('tag', None)
        if expertise:
            # Filter mentors containing the expertise tag
            queryset = MentorProfile.objects.filter(expertise_tags__contains=[expertise])
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response({"detail": "Expertise tag parameter is required"}, 
                        status=status.HTTP_400_BAD_REQUEST)

class MentorListView(generics.ListAPIView):
    """View for students to browse available mentors"""
    queryset = User.objects.filter(mentor_profile__isnull=False)
    serializer_class = MentorListSerializer
    permission_classes = [IsAuthenticated, IsStudent]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'mentor_profile__name', 'mentor_profile__expertise_tags']

class MentorshipRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for managing mentorship requests"""
    serializer_class = MentorshipRequestSerializer
    permission_classes = [IsAuthenticated, CanManageRequest]
    
    def get_queryset(self):
        user = self.request.user
        
        # If the action is 'list', filter based on user role
        if self.action == 'list':
            # Return based on which endpoint was accessed
            if hasattr(user, 'student_profile'):
                # Student viewing their own requests
                return MentorshipRequest.objects.filter(student=user)
            elif hasattr(user, 'mentor_profile'):
                # Mentor viewing requests they've received
                return MentorshipRequest.objects.filter(mentor=user)
            return MentorshipRequest.objects.none()
        
        # For other actions, return all requests the user is involved in
        return MentorshipRequest.objects.filter(
            models.Q(student=user) | models.Q(mentor=user)
        )
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        
        # Include student details if user is a mentor viewing requests
        if hasattr(user, 'mentor_profile'):
            context['include_student_details'] = True
        
        return context
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsMentor])
    def accept(self, request, pk=None):
        """Custom action for mentors to accept a request"""
        request_obj = self.get_object()
        
        # Ensure the mentor is the recipient of the request
        if request_obj.mentor != request.user:
            return Response(
                {"detail": "You can only accept requests sent to you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update status
        request_obj.status = 'accepted'
        request_obj.save()  # This will trigger the save method to decline other requests
        
        serializer = self.get_serializer(request_obj)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsMentor])
    def decline(self, request, pk=None):
        """Custom action for mentors to decline a request with a reason"""
        request_obj = self.get_object()
        
        # Ensure the mentor is the recipient of the request
        if request_obj.mentor != request.user:
            return Response(
                {"detail": "You can only decline requests sent to you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get rejection reason from request data
        rejection_reason = request.data.get('rejection_reason', '')
        
        # Update status and rejection reason
        request_obj.status = 'declined'
        request_obj.rejection_reason = rejection_reason
        request_obj.save()
        
        serializer = self.get_serializer(request_obj)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsStudent])
    def student(self, request):
        """Endpoint for students to view their requests"""
        requests = MentorshipRequest.objects.filter(student=request.user)
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsMentor])
    def mentor(self, request):
        """Endpoint for mentors to view requests sent to them"""
        requests = MentorshipRequest.objects.filter(mentor=request.user)
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)

class MessageAPIView(APIView):
    permission_classes = [IsAuthenticated, IsMessageAllowed]
    
    def post(self, request):
        """Send a message to another user"""
        # Get the receiver ID from the request data
        receiver_id = request.data.get('receiver')
        if not receiver_id:
            return Response({"detail": "Receiver ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return Response({"detail": "Receiver not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if the sender and receiver are in a valid mentorship relationship
        sender = request.user
        
        # Case 1: Sender is a student, receiver is a mentor
        if hasattr(sender, 'student_profile') and hasattr(receiver, 'mentor_profile'):
            # Check if there's an accepted mentorship request
            is_valid = MentorshipRequest.objects.filter(
                student=sender,
                mentor=receiver,
                status='accepted'
            ).exists()
            
            if not is_valid:
                return Response(
                    {"detail": "You can only message your accepted mentor"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Case 2: Sender is a mentor, receiver is a student
        elif hasattr(sender, 'mentor_profile') and hasattr(receiver, 'student_profile'):
            # Check if there's an accepted mentorship request
            is_valid = MentorshipRequest.objects.filter(
                student=receiver,
                mentor=sender,
                status='accepted'
            ).exists()
            
            if not is_valid:
                return Response(
                    {"detail": "You can only message your accepted mentees"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if mentor has exceeded the 5 mentee limit
            accepted_mentees = MentorshipRequest.objects.filter(
                mentor=sender,
                status='accepted'
            ).count()
            
            if accepted_mentees > 5:
                return Response(
                    {"detail": "You have reached the maximum limit of 5 mentees"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        else:
            return Response(
                {"detail": "Invalid user roles for messaging"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create the message
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(sender=sender, receiver=receiver)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request, user_id=None):
        """Get message history between current user and specified user"""
        if not user_id:
            return Response({"detail": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if the users are in a valid mentorship relationship
        is_valid = self._check_valid_messaging_pair(request.user, other_user)
        
        if not is_valid:
            return Response(
                {"detail": "You are not allowed to view messages with this user"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get messages between the two users
        messages = Message.objects.filter(
            (Q(sender=request.user) & Q(receiver=other_user)) |
            (Q(sender=other_user) & Q(receiver=request.user))
        ).order_by('timestamp')
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    def _check_valid_messaging_pair(self, user1, user2):
        """Check if two users are allowed to message each other"""
        # Check if there's an accepted mentorship request between them (in either direction)
        return MentorshipRequest.objects.filter(
            (Q(student=user1) & Q(mentor=user2)) |
            (Q(student=user2) & Q(mentor=user1)),
            status='accepted'
        ).exists()

class MessageStreamView(APIView):
    permission_classes = [IsAuthenticated, IsMessageAllowed]
    
    def get(self, request, user_id):
        """Stream new messages in real-time using SSE"""
        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if the users are in a valid mentorship relationship
        is_valid = MentorshipRequest.objects.filter(
            (Q(student=request.user) & Q(mentor=other_user)) |
            (Q(student=other_user) & Q(mentor=request.user)),
            status='accepted'
        ).exists()
        
        if not is_valid:
            return Response(
                {"detail": "You are not allowed to receive messages from this user"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Return a streaming response
        return StreamingHttpResponse(
            self._event_stream(request.user, other_user),
            content_type='text/event-stream'
        )
    
    def _event_stream(self, current_user, other_user):
        """Generate SSE events for new messages"""
        # Keep track of the latest message timestamp
        last_check = time.time()
        
        while True:
            # Query for new messages
            new_messages = Message.objects.filter(
                (Q(sender=current_user) & Q(receiver=other_user)) |
                (Q(sender=other_user) & Q(receiver=current_user)),
                timestamp__gt=timezone.datetime.fromtimestamp(last_check, tz=timezone.utc)
            ).order_by('timestamp')
            
            # Send each new message as an SSE event
            for message in new_messages:
                serializer = MessageSerializer(message)
                data = json.dumps(serializer.data)
                yield f"data: {data}\n\n"
            
            # Update the last check time
            last_check = time.time()
            
            # Sleep to avoid excessive database queries
            time.sleep(2)  # Check for new messages every 2 seconds

class RateLimitedRegisterView(RegisterView):
    """Rate-limited version of the register view"""
    @rate_limit(max_requests=5, timeframe=60)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class RateLimitedTokenObtainPairView(TokenObtainPairView):
    """Rate-limited version of the token obtain pair view"""
    @rate_limit(max_requests=5, timeframe=60)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class RateLimitedTokenRefreshView(TokenRefreshView):
    """Rate-limited version of the token refresh view"""
    @rate_limit(max_requests=10, timeframe=60)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
