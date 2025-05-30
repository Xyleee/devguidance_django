from django.shortcuts import render
from django.contrib.auth.models import User
from .serializers import (
    RegisterSerializer, 
    StudentProfileSerializer, 
    StudentProjectSerializer, 
    MentorProfileSerializer,
    MentorListSerializer,
    MentorshipRequestSerializer,
    MessageSerializer,
    CustomTokenObtainPairSerializer
)
from rest_framework import generics, viewsets, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from students.models import StudentProfile, StudentProject
from mentors.models import MentorProfile, MentorshipRequest
from .models import Message
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
from rest_framework_simplejwt.tokens import RefreshToken

# DRF Spectacular imports for API documentation
from drf_spectacular.utils import (
    extend_schema, 
    extend_schema_view, 
    OpenApiParameter, 
    OpenApiExample,
    OpenApiResponse,
    inline_serializer
)
from drf_spectacular.types import OpenApiTypes

# Create your views here.

def home(request):
    return render(request, 'users/home.html')

@extend_schema(
    operation_id='register_user',
    tags=['Authentication'],
    summary='Register a new user',
    description='''
    Register a new user account as either a student or mentor.
    
    **Features:**
    - Creates user account with authentication
    - Automatically creates appropriate profile (Student or Mentor)
    - Returns JWT tokens for immediate authentication
    - Supports profile photo upload during registration
    
    **Rate Limiting:** 5 requests per minute
    ''',
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(
            response=inline_serializer(
                name='RegisterResponse',
                fields={
                    'refresh': OpenApiTypes.STR,
                    'access': OpenApiTypes.STR,
                    'user': OpenApiTypes.OBJECT,
                }
            ),
            description='User successfully registered',
            examples=[
                OpenApiExample(
                    'Student Registration Success',
                    summary='Successful student registration',
                    description='Response when a student is successfully registered',
                    value={
                        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "user": {
                            "id": 1,
                            "username": "johndoe",
                            "email": "john@example.com",
                            "user_type": "student",
                            "students_profile": {
                                "id": 1,
                                "name": "John Doe",
                                "bio": "",
                                "year_level": 1,
                                "tech_stack": [],
                                "photo_url": None
                            }
                        }
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description='Validation errors',
            examples=[
                OpenApiExample(
                    'Password Mismatch',
                    summary='Password confirmation error',
                    value={
                        "password": ["Password fields didn't match."]
                    }
                ),
                OpenApiExample(
                    'Username Exists',
                    summary='Username already taken',
                    value={
                        "username": ["A user with that username already exists."]
                    }
                )
            ]
        ),
        429: OpenApiResponse(
            description='Rate limit exceeded',
            examples=[
                OpenApiExample(
                    'Rate Limited',
                    summary='Too many registration attempts',
                    value={
                        "detail": "Rate limit exceeded. Try again in 45 seconds."
                    }
                )
            ]
        )
    },
    examples=[
        OpenApiExample(
            'Student Registration',
            summary='Register as a student',
            description='Example request to register a new student account',
            value={
                "username": "johndoe",
                "email": "john@example.com", 
                "password": "securepassword123",
                "password2": "securepassword123",
                "user_type": "student",
                "name": "John Doe",
                "first_name": "John",
                "last_name": "Doe"
            }
        ),
        OpenApiExample(
            'Mentor Registration',
            summary='Register as a mentor',
            description='Example request to register a new mentor account',
            value={
                "username": "janementor",
                "email": "jane@example.com",
                "password": "securepassword123", 
                "password2": "securepassword123",
                "user_type": "mentor",
                "name": "Jane Smith",
                "first_name": "Jane",
                "last_name": "Smith"
            }
        )
    ]
)
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
        
        # Get the appropriate profile
        if user_type == 'student':
            profile = user.students_profile
            profile_serializer = StudentProfileSerializer(profile)
            profile_type = 'students_profile'
        else:
            profile = user.mentors_profile
            profile_serializer = MentorProfileSerializer(profile)
            profile_type = 'mentors_profile'
            
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
            
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'user_type': user_type,
                profile_type: profile_serializer.data
            }
        }, status=status.HTTP_201_CREATED)

@extend_schema(
    operation_id='protected_example',
    tags=['Users'],
    summary='Protected endpoint example',
    description='Example of a protected endpoint that requires authentication',
    responses={
        200: OpenApiResponse(
            response=inline_serializer(
                name='ProtectedResponse',
                fields={'message': OpenApiTypes.STR}
            ),
            description='Success response with personalized message'
        ),
        401: OpenApiResponse(description='Authentication required')
    }
)
class ProtectedView(APIView):
    permission_classes = [IsAuthenticated] # Require authentication

    def get(self, request):
        content = {'message': f'Hello, {request.user.username}! This is protected content.'}
        return Response(content)

@extend_schema_view(
    list=extend_schema(
        operation_id='list_student_profiles',
        tags=['Students'],
        summary='List student profiles',
        description='Get a list of student profiles with search functionality',
        parameters=[
            OpenApiParameter(
                name='search',
                description='Search students by name or tech stack',
                required=False,
                type=str,
                location=OpenApiParameter.QUERY
            )
        ]
    ),
    create=extend_schema(
        operation_id='create_student_profile',
        tags=['Students'],
        summary='Create student profile',
        description='Create a new student profile for the authenticated user'
    ),
    retrieve=extend_schema(
        operation_id='get_student_profile',
        tags=['Students'],
        summary='Get student profile',
        description='Retrieve a specific student profile by ID'
    ),
    update=extend_schema(
        operation_id='update_student_profile',
        tags=['Students'],
        summary='Update student profile',
        description='Update a student profile (full update)'
    ),
    partial_update=extend_schema(
        operation_id='partial_update_student_profile',
        tags=['Students'],
        summary='Partially update student profile',
        description='Partially update a student profile'
    ),
    destroy=extend_schema(
        operation_id='delete_student_profile',
        tags=['Students'],
        summary='Delete student profile',
        description='Delete a student profile'
    )
)
class StudentProfileViewSet(viewsets.ModelViewSet):
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'tech_stack']
    
    def get_queryset(self):
        return StudentProfile.objects.filter(user=self.request.user)
    
    def get_object(self):
        return get_object_or_404(StudentProfile, user=self.request.user)
    
    @extend_schema(
        operation_id='get_my_student_profile',
        tags=['Students'],
        summary='Get my student profile',
        description='Retrieve the student profile of the authenticated user',
        responses={
            200: StudentProfileSerializer,
            404: OpenApiResponse(description='Profile not found')
        }
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        try:
            profile = StudentProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except StudentProfile.DoesNotExist:
            return Response({"detail": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        operation_id='find_students_by_tech_stack',
        tags=['Students', 'Search'],
        summary='Find students by technology',
        description='Find student profiles that have a specific technology in their tech stack',
        parameters=[
            OpenApiParameter(
                name='tag',
                description='Technology tag to search for (e.g., "Python", "React", "Django")',
                required=True,
                type=str,
                location=OpenApiParameter.QUERY,
                examples=[
                    OpenApiExample('Python', value='Python'),
                    OpenApiExample('React', value='React'),
                    OpenApiExample('Django', value='Django')
                ]
            )
        ],
        responses={
            200: StudentProfileSerializer(many=True),
            400: OpenApiResponse(description='Tag parameter is required')
        }
    )
    @action(detail=False, methods=['get'])
    def by_tech_stack(self, request):
        tag = request.query_params.get('tag', None)
        if tag:
            profiles = StudentProfile.objects.filter(tech_stack__contains=[tag])
            serializer = self.get_serializer(profiles, many=True)
            return Response(serializer.data)
        return Response({"detail": "Tag parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        operation_id='find_students_by_year_level',
        tags=['Students', 'Search'],
        summary='Find students by year level',
        description='Find student profiles by their academic year level',
        parameters=[
            OpenApiParameter(
                name='level',
                description='Academic year level (1-4)',
                required=True,
                type=int,
                location=OpenApiParameter.QUERY,
                examples=[
                    OpenApiExample('First Year', value=1),
                    OpenApiExample('Second Year', value=2),
                    OpenApiExample('Third Year', value=3),
                    OpenApiExample('Fourth Year', value=4)
                ]
            )
        ],
        responses={
            200: StudentProfileSerializer(many=True),
            400: OpenApiResponse(description='Level parameter is required')
        }
    )
    @action(detail=False, methods=['get'])
    def by_year_level(self, request):
        level = request.query_params.get('level', None)
        if level:
            profiles = StudentProfile.objects.filter(year_level=level)
            serializer = self.get_serializer(profiles, many=True)
            return Response(serializer.data)
        return Response({"detail": "Level parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        operation_id='get_student_stats',
        tags=['Students'],
        summary='Get student statistics',
        description='Get statistics and metrics for a student profile',
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='StudentStats',
                    fields={
                        'projects_count': OpenApiTypes.INT,
                        'active_mentorships': OpenApiTypes.INT,
                        'tech_stack_count': OpenApiTypes.INT,
                        'days_since_joined': OpenApiTypes.INT
                    }
                ),
                description='Student statistics',
                examples=[
                    OpenApiExample(
                        'Student Stats',
                        value={
                            "projects_count": 5,
                            "active_mentorships": 2,
                            "tech_stack_count": 8,
                            "days_since_joined": 120
                        }
                    )
                ]
            )
        }
    )
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        profile = self.get_object()
        
        # Get stats
        project_count = profile.projects.count()
        active_mentorships = MentorshipRequest.objects.filter(
            student=profile.user, 
            status='accepted'
        ).count()
        
        return Response({
            "projects_count": project_count,
            "active_mentorships": active_mentorships,
            "tech_stack_count": len(profile.tech_stack),
            "days_since_joined": (timezone.now() - profile.created_at).days
        })

class StudentProjectViewSet(viewsets.ModelViewSet):
    serializer_class = StudentProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly, IsStudent]
    
    def get_queryset(self):
        return StudentProject.objects.filter(student__user=self.request.user)
    
    def perform_create(self, serializer):
        student_profile = get_object_or_404(StudentProfile, user=self.request.user)
        serializer.save(student=student_profile)

    @action(detail=False, methods=['get'])
    def by_tools(self, request):
        tool = request.query_params.get('tool', None)
        if not tool:
            return Response({"detail": "Tool parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Debug what's in the database
        all_projects = StudentProject.objects.filter(student__user=request.user)
        print(f"User has {all_projects.count()} projects")
        for project in all_projects:
            print(f"Project: {project.title}, Tools: {project.tools_used}")
        
        # Case-insensitive search may help
        projects = StudentProject.objects.filter(
            student__user=request.user,
            tools_used__icontains=tool.lower()  # Try case-insensitive search
        )
        
        if not projects.exists():
            # If no results, return empty list with a message
            return Response({
                "detail": f"No projects found with tool: {tool}",
                "results": []
            })
        
        serializer = self.get_serializer(projects, many=True)
        return Response(serializer.data)

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

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        profile = self.get_object()
        
        # Count active mentorships
        active_mentorships = MentorshipRequest.objects.filter(
            mentor=profile.user,
            status='accepted'
        ).count()
        
        # Assume a mentor can handle at most 5 mentees
        is_available = active_mentorships < 5
        
        return Response({
            "is_available": is_available,
            "active_mentorships": active_mentorships,
            "max_mentorships": 5
        })

class MentorListView(generics.ListAPIView):
    """View for students to browse available mentors"""
    queryset = User.objects.filter(mentors_profile__isnull=False)
    serializer_class = MentorListSerializer
    permission_classes = [IsAuthenticated, IsStudent]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'mentors_profile__name', 'mentors_profile__expertise_tags']

class MentorshipRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for managing mentorship requests"""
    serializer_class = MentorshipRequestSerializer
    permission_classes = [IsAuthenticated, CanManageRequest]
    
    def get_queryset(self):
        user = self.request.user
        
        # If the action is 'list', filter based on user role
        if self.action == 'list':
            # Return based on which endpoint was accessed
            if hasattr(user, 'students_profile'):
                # Student viewing their own requests
                return MentorshipRequest.objects.filter(student=user)
            elif hasattr(user, 'mentors_profile'):
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
        if hasattr(user, 'mentors_profile'):
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

@extend_schema_view(
    post=extend_schema(
        operation_id='send_message',
        tags=['Messages'],
        summary='Send a message',
        description='''
        Send a message to another user with optional file attachment.
        
        **Features:**
        - Text messages with optional file attachments
        - File size limit: 5MB
        - Supported formats: PDF, DOCX, XLSX, PPTX, TXT, CSV, PNG, JPEG, GIF
        - Automatic validation of sender-receiver relationship
        - Real-time message delivery
        ''',
        request=MessageSerializer,
        responses={
            201: OpenApiResponse(
                response=MessageSerializer,
                description='Message sent successfully',
                examples=[
                    OpenApiExample(
                        'Text Message',
                        summary='Simple text message',
                        value={
                            "id": 1,
                            "sender": 1,
                            "receiver": 2,
                            "sender_username": "student1",
                            "receiver_username": "mentor1",
                            "content": "Hello! I need help with my Django project.",
                            "file_url": None,
                            "timestamp": "2024-01-15T10:30:00Z"
                        }
                    ),
                    OpenApiExample(
                        'Message with File',
                        summary='Message with file attachment',
                        value={
                            "id": 2,
                            "sender": 1,
                            "receiver": 2,
                            "sender_username": "student1",
                            "receiver_username": "mentor1",
                            "content": "Here's my project code for review",
                            "file_url": "/media/message_files/project_code.zip",
                            "timestamp": "2024-01-15T10:35:00Z"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description='Validation errors',
                examples=[
                    OpenApiExample(
                        'Invalid Receiver',
                        value={"receiver": ["Invalid receiver selected."]}
                    ),
                    OpenApiExample(
                        'File Too Large',
                        value={"file": ["File size exceeds 5MB limit."]}
                    )
                ]
            ),
            403: OpenApiResponse(
                description='Permission denied - invalid messaging pair'
            )
        },
        examples=[
            OpenApiExample(
                'Simple Message',
                summary='Send a text message',
                value={
                    "receiver": 2,
                    "content": "Hello! Could you help me with my React project?"
                }
            ),
            OpenApiExample(
                'Message with File',
                summary='Send message with attachment',
                description='Use multipart/form-data for file uploads',
                value={
                    "receiver": 2,
                    "content": "Please review my code",
                    "file": "project_file.pdf"
                }
            )
        ]
    ),
    get=extend_schema(
        operation_id='get_message_history',
        tags=['Messages'],
        summary='Get message history',
        description='''
        Retrieve message history between the authenticated user and another user.
        
        **Features:**
        - Complete conversation history
        - Messages ordered by timestamp (oldest first)
        - Includes file attachments and metadata
        - Automatic validation of messaging permissions
        ''',
        parameters=[
            OpenApiParameter(
                name='user_id',
                description='ID of the other user in the conversation',
                required=True,
                type=int,
                location=OpenApiParameter.PATH
            )
        ],
        responses={
            200: OpenApiResponse(
                response=MessageSerializer(many=True),
                description='Message history retrieved successfully',
                examples=[
                    OpenApiExample(
                        'Conversation History',
                        value=[
                            {
                                "id": 1,
                                "sender": 1,
                                "receiver": 2,
                                "sender_username": "student1",
                                "receiver_username": "mentor1",
                                "content": "Hello! I need help with Django.",
                                "file_url": None,
                                "timestamp": "2024-01-15T10:00:00Z"
                            },
                            {
                                "id": 2,
                                "sender": 2,
                                "receiver": 1,
                                "sender_username": "mentor1", 
                                "receiver_username": "student1",
                                "content": "Sure! What specific issue are you facing?",
                                "file_url": None,
                                "timestamp": "2024-01-15T10:05:00Z"
                            }
                        ]
                    )
                ]
            ),
            403: OpenApiResponse(description='Permission denied - invalid messaging pair'),
            404: OpenApiResponse(description='User not found')
        }
    )
)
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
        if hasattr(sender, 'students_profile') and hasattr(receiver, 'mentors_profile'):
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
        elif hasattr(sender, 'mentors_profile') and hasattr(receiver, 'students_profile'):
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

    @action(detail=True, methods=['patch'])
    def read(self, request, pk=None):
        message = get_object_or_404(Message, id=pk)
        
        # Ensure the user is the receiver
        if message.receiver != request.user:
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)
        
        # Mark as read (you'd need to add a read field to the Message model)
        message.is_read = True
        message.save()
        
        return Response({"status": "Message marked as read"})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = Message.objects.filter(receiver=request.user, is_read=False).count()
        return Response({"unread_count": count})

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

@extend_schema(
    operation_id='login_user',
    tags=['Authentication'],
    summary='User login',
    description='''
    Authenticate user and obtain JWT tokens.
    
    **Features:**
    - Clean response format with success message
    - Returns user profile information
    - Provides JWT access and refresh tokens
    - Rate limited to prevent abuse
    
    **Rate Limiting:** 5 requests per minute
    ''',
    request=inline_serializer(
        name='LoginRequest',
        fields={
            'username': OpenApiTypes.STR,
            'password': OpenApiTypes.STR,
        }
    ),
    responses={
        200: OpenApiResponse(
            response=inline_serializer(
                name='LoginResponse',
                fields={
                    'message': OpenApiTypes.STR,
                    'user': OpenApiTypes.OBJECT,
                    'tokens': OpenApiTypes.OBJECT,
                }
            ),
            description='Login successful',
            examples=[
                OpenApiExample(
                    'Student Login Success',
                    summary='Successful student login',
                    description='Response when a student successfully logs in',
                    value={
                        "message": "Login successful",
                        "user": {
                            "id": 1,
                            "username": "johndoe",
                            "email": "john@example.com",
                            "user_type": "student",
                            "profile": {
                                "id": 1,
                                "name": "John Doe",
                                "bio": "Computer Science student",
                                "year_level": 3,
                                "tech_stack": ["Python", "React", "Django"],
                                "photo_url": "/media/profiles/john.jpg"
                            }
                        },
                        "tokens": {
                            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                        }
                    }
                ),
                OpenApiExample(
                    'Mentor Login Success',
                    summary='Successful mentor login',
                    description='Response when a mentor successfully logs in',
                    value={
                        "message": "Login successful",
                        "user": {
                            "id": 2,
                            "username": "janementor",
                            "email": "jane@example.com",
                            "user_type": "mentor",
                            "profile": {
                                "id": 1,
                                "name": "Jane Smith",
                                "bio": "Senior Software Engineer",
                                "years_of_experience": 5,
                                "expertise_tags": ["Python", "Django", "AWS"],
                                "company": "Tech Corp",
                                "position": "Senior Developer",
                                "photo_url": "/media/profiles/jane.jpg"
                            }
                        },
                        "tokens": {
                            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                        }
                    }
                )
            ]
        ),
        401: OpenApiResponse(
            description='Invalid credentials',
            examples=[
                OpenApiExample(
                    'Invalid Credentials',
                    summary='Login failed',
                    value={
                        "detail": "No active account found with the given credentials"
                    }
                )
            ]
        ),
        429: OpenApiResponse(
            description='Rate limit exceeded',
            examples=[
                OpenApiExample(
                    'Rate Limited',
                    summary='Too many login attempts',
                    value={
                        "detail": "Rate limit exceeded. Try again in 45 seconds."
                    }
                )
            ]
        )
    },
    examples=[
        OpenApiExample(
            'Login Request',
            summary='User login credentials',
            description='Example login request with username and password',
            value={
                "username": "johndoe",
                "password": "securepassword123"
            }
        )
    ]
)
class RateLimitedTokenObtainPairView(TokenObtainPairView):
    """Rate-limited version of the token obtain pair view with clean response format"""
    serializer_class = CustomTokenObtainPairSerializer
    
    @rate_limit(max_requests=5, timeframe=60)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class RateLimitedTokenRefreshView(TokenRefreshView):
    """Rate-limited version of the token refresh view"""
    @rate_limit(max_requests=10, timeframe=60)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
