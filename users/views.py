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
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

logger = logging.getLogger(__name__) # Define logger at module level

# Create your views here.

def home(request):
    return render(request, 'users/home.html')

class RegisterView(generics.CreateAPIView):
    """
    Register a new user account
    
    Creates a new user account with either student or mentor profile based on user_type parameter.
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    
    @swagger_auto_schema(
        operation_description="Register a new user account as either a student or mentor",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'email', 'password', 'password2', 'user_type'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
                'password2': openapi.Schema(type=openapi.TYPE_STRING, description='Password confirmation'),
                'user_type': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Type of user account',
                    enum=['student', 'mentor']
                ),
            },
        ),
        responses={
            201: openapi.Response(
                description="User registered successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'username': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                        'profile': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: openapi.Response(description="Bad request - validation errors")
        },
        tags=['Authentication']
    )
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
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            },
            'profile': profile_serializer.data,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)

class ProtectedView(APIView):
    """
    Protected endpoint that requires authentication
    
    Returns a personalized message for authenticated users.
    """
    permission_classes = [IsAuthenticated] # Require authentication

    @swagger_auto_schema(
        operation_description="Access protected content - requires authentication",
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Personalized greeting message'
                        )
                    }
                )
            ),
            401: openapi.Response(description="Unauthorized - authentication required")
        },
        tags=['Authentication']
    )
    def get(self, request):
        content = {'message': f'Hello, {request.user.username}! This is protected content.'}
        return Response(content)

class StudentProfileViewSet(viewsets.ModelViewSet):
    """
    Student Profile Management
    
    Provides CRUD operations for student profiles. Users can only manage their own profiles.
    Supports searching by name and tech stack.
    """
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
    """
    Mentorship Request Management
    
    Allows students to create mentorship requests and mentors to accept/decline them.
    Students can view their own requests, mentors can view requests sent to them.
    """
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
    
    @swagger_auto_schema(
        operation_description="Accept a mentorship request",
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT, properties={}),
        responses={
            200: MentorshipRequestSerializer,
            403: openapi.Response(description="Forbidden - not your request or not a mentor"),
            404: openapi.Response(description="Request not found")
        },
        tags=['Mentorship Requests']
    )
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
    
    @swagger_auto_schema(
        operation_description="Decline a mentorship request with optional reason",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'rejection_reason': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Optional reason for declining the request'
                )
            }
        ),
        responses={
            200: MentorshipRequestSerializer,
            403: openapi.Response(description="Forbidden - not your request or not a mentor"),
            404: openapi.Response(description="Request not found")
        },
        tags=['Mentorship Requests']
    )
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
    """
    Messaging between mentors and students
    
    Allows sending and retrieving messages between matched mentors and students only.
    """
    permission_classes = [IsAuthenticated, IsMessageAllowed]
    
    @swagger_auto_schema(
        operation_description="Send a message to another user in your mentorship network",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['receiver', 'content'],
            properties={
                'receiver': openapi.Schema(
                    type=openapi.TYPE_INTEGER, 
                    description='ID of the message recipient'
                ),
                'content': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Message content'
                )
            }
        ),
        responses={
            201: MessageSerializer,
            400: openapi.Response(description="Bad request - missing receiver or invalid data"),
            403: openapi.Response(description="Forbidden - not allowed to message this user"),
            404: openapi.Response(description="Receiver not found")
        },
        tags=['Messaging']
    )
    def post(self, request):
        logger.info(f"MessageAPIView.post: Received request from user {request.user.id if request.user else 'Anonymous'}")
        logger.debug(f"MessageAPIView.post: Request data: {request.data}")
        try:
            receiver_id = request.data.get('receiver')
            content = request.data.get('content') # Get content for logging
            content_log_display = (content[:50] + '...') if content else '[No text content]'
            logger.info(f"MessageAPIView.post: Attempting to send message to receiver_id: {receiver_id} with content: '{content_log_display}'")

            if not receiver_id:
                logger.warning("MessageAPIView.post: Receiver ID is required")
                return Response({"detail": "Receiver ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                logger.debug("MessageAPIView.post: Fetching receiver user object.")
                receiver = User.objects.get(id=receiver_id)
                logger.info(f"MessageAPIView.post: Receiver user object fetched: {receiver.username}")
            except User.DoesNotExist:
                logger.warning(f"MessageAPIView.post: Receiver not found for ID: {receiver_id}")
                return Response({"detail": "Receiver not found"}, status=status.HTTP_404_NOT_FOUND)
            
            sender = request.user
            logger.info(f"MessageAPIView.post: Sender user: {sender.username}")

            if not (hasattr(sender, 'student_profile') or hasattr(sender, 'mentor_profile')):
                logger.warning(f"MessageAPIView.post: Sender {sender.username} lacks student/mentor profile.")
                return Response(
                    {"detail": "Sender must have either a student or mentor profile"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if not (hasattr(receiver, 'student_profile') or hasattr(receiver, 'mentor_profile')):
                logger.warning(f"MessageAPIView.post: Receiver {receiver.username} lacks student/mentor profile.")
                return Response(
                    {"detail": "Receiver must have either a student or mentor profile"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            logger.debug("MessageAPIView.post: Validating mentorship relationship.")
            if hasattr(sender, 'student_profile') and hasattr(receiver, 'mentor_profile'):
                is_valid = MentorshipRequest.objects.filter(
                    student=sender,
                    mentor=receiver,
                    status='accepted'
                ).exists()
                if not is_valid:
                    logger.warning(f"MessageAPIView.post: Student {sender.username} to Mentor {receiver.username} - No accepted mentorship.")
                    return Response(
                        {"detail": "You can only message your accepted mentor"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            elif hasattr(sender, 'mentor_profile') and hasattr(receiver, 'student_profile'):
                is_valid = MentorshipRequest.objects.filter(
                    student=receiver,
                    mentor=sender,
                    status='accepted'
                ).exists()
                if not is_valid:
                    logger.warning(f"MessageAPIView.post: Mentor {sender.username} to Student {receiver.username} - No accepted mentorship.")
                    return Response(
                        {"detail": "You can only message your accepted mentees"},
                        status=status.HTTP_403_FORBIDDEN
                    )
                accepted_mentees = MentorshipRequest.objects.filter(
                    mentor=sender,
                    status='accepted'
                ).count()
                if accepted_mentees >= 5: # Assuming 5 is the limit
                    logger.warning(f"MessageAPIView.post: Mentor {sender.username} has reached mentee limit ({accepted_mentees}).")
                    return Response(
                        {"detail": "You have reached the maximum limit of 5 mentees"}, # Ensure limit is correct
                        status=status.HTTP_403_FORBIDDEN
                    )
            else:
                logger.warning(f"MessageAPIView.post: Invalid roles for messaging between {sender.username} and {receiver.username}.")
                return Response(
                    {"detail": "Invalid user roles for messaging"},
                    status=status.HTTP_403_FORBIDDEN
                )
            logger.info("MessageAPIView.post: Mentorship relationship validated.")

            message_data = request.data.copy()
            # Ensure receiver in message_data is the ID, not the object, if serializer expects ID.
            # Serializer might handle `receiver` object correctly if PrimaryKeyRelatedField, but being explicit for debug.
            message_data['receiver'] = receiver.id 
            logger.debug(f"MessageAPIView.post: Preparing to serialize message_data: {message_data}")

            serializer = MessageSerializer(data=message_data, context={'request': request}) # Pass request to context if needed by serializer
            if serializer.is_valid():
                logger.info("MessageAPIView.post: Serializer is valid. Saving message.")
                serializer.save(sender=sender, receiver=receiver) # receiver object passed here
                logger.info(f"MessageAPIView.post: Message saved successfully. ID: {serializer.instance.id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"MessageAPIView.post: Serializer errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.exception(f"MessageAPIView.post: Unhandled exception: {str(e)}") # logger.exception includes traceback
            return Response(
                {"detail": "An internal error occurred. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_description="Get message history with another user",
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_PATH,
                description="ID of the other user to get message history with",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Message history",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT)
                )
            ),
            400: openapi.Response(description="Bad request - user ID required"),
            403: openapi.Response(description="Forbidden - not allowed to view messages with this user"),
            404: openapi.Response(description="User not found")
        },
        tags=['Messaging']
    )
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
        logger.info(f"MessageStreamView.get: Stream request from user {request.user.id} for user_id: {user_id}")
        try:
            try:
                logger.debug("MessageStreamView.get: Fetching other_user object.")
                other_user = User.objects.get(id=user_id)
                logger.info(f"MessageStreamView.get: other_user object fetched: {other_user.username}")
            except User.DoesNotExist:
                logger.warning(f"MessageStreamView.get: User not found for ID: {user_id}")
                return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
            current_user = request.user
            logger.info(f"MessageStreamView.get: Current user: {current_user.username}")

            if not (hasattr(current_user, 'student_profile') or hasattr(current_user, 'mentor_profile')):
                logger.warning(f"MessageStreamView.get: Current user {current_user.username} lacks student/mentor profile.")
                return Response(
                    {"detail": "User must have either a student or mentor profile"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if not (hasattr(other_user, 'student_profile') or hasattr(other_user, 'mentor_profile')):
                logger.warning(f"MessageStreamView.get: Target user {other_user.username} lacks student/mentor profile.")
                return Response(
                    {"detail": "Target user must have either a student or mentor profile"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            logger.debug("MessageStreamView.get: Validating mentorship relationship for stream.")
            is_valid = MentorshipRequest.objects.filter(
                (Q(student=current_user) & Q(mentor=other_user)) |
                (Q(student=other_user) & Q(mentor=current_user)),
                status='accepted'
            ).exists()
            
            if not is_valid:
                logger.warning(f"MessageStreamView.get: No accepted mentorship between {current_user.username} and {other_user.username} for stream.")
                return Response(
                    {"detail": "You are not allowed to receive messages from this user"},
                    status=status.HTTP_403_FORBIDDEN
                )
            logger.info("MessageStreamView.get: Mentorship relationship for stream validated.")

            return StreamingHttpResponse(
                self._event_stream(current_user, other_user),
                content_type='text/event-stream'
            )
            
        except Exception as e:
            logger.exception(f"MessageStreamView.get: Unhandled exception: {str(e)}")
            # For a streaming view, returning a standard HTTP Response on error might be tricky.
            # The client might already be expecting a stream. This error might not reach the client cleanly.
            # However, it will be logged.
            return Response(
                {"detail": "An internal error occurred during stream setup. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _event_stream(self, current_user, other_user):
        logger.info(f"MessageStreamView._event_stream: Starting event stream between {current_user.username} and {other_user.username}")
        try:
            last_check = timezone.now() # Use timezone.now() for consistency with Django model timestamps
            
            while True:
                # Query for new messages
                # Ensure timestamp comparison is timezone-aware if model timestamp is timezone-aware
                new_messages = Message.objects.filter(
                    (Q(sender=current_user) & Q(receiver=other_user)) |
                    (Q(sender=other_user) & Q(receiver=current_user)),
                    timestamp__gt=last_check 
                ).order_by('timestamp')
                
                for message in new_messages:
                    logger.debug(f"MessageStreamView._event_stream: Streaming message ID {message.id}")
                    try:
                        serializer = MessageSerializer(message)
                        data = json.dumps(serializer.data)
                        yield f"data: {data}\n\n"
                        last_check = message.timestamp # Update last_check to the timestamp of the last sent message
                    except Exception as e:
                        logger.exception(f"MessageStreamView._event_stream: Error serializing message ID {message.id}: {str(e)}")
                
                # time.sleep(2) # Check for new messages every 2 seconds (consider making this configurable or use a different mechanism if possible)
                # Using a simple sleep. For production, consider Django Channels or other async solutions for push notifications.
                # For now, keeping it simple with polling for debugging.
                time.sleep(settings.MESSAGE_STREAM_POLL_INTERVAL if hasattr(settings, 'MESSAGE_STREAM_POLL_INTERVAL') else 2)

        except Exception as e:
            logger.exception(f"MessageStreamView._event_stream: Error in message stream: {str(e)}")
            yield f"data: {json.dumps({'error': 'Streaming error occurred', 'detail': str(e)})}\n\n"

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
