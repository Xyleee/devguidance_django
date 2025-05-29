from django.shortcuts import render
from django.contrib.auth.models import User
from .serializers import (
    RegisterSerializer, 
    MessageSerializer
)
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Message
from .permissions import IsMessageAllowed
from rest_framework.permissions import AllowAny
from django.db.models import Q
from django.http import StreamingHttpResponse, JsonResponse, HttpResponse
import json
import time
from django.conf import settings
import os
from django.utils import timezone
from .rate_limiting import rate_limit
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

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
                            "student_profile": {
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
            from .serializers import StudentProfileSerializer
            profile = user.student_profile
            profile_serializer = StudentProfileSerializer(profile)
            profile_type = 'student_profile'
        else:
            from .serializers import MentorProfileSerializer
            profile = user.mentor_profile
            profile_serializer = MentorProfileSerializer(profile)
            profile_type = 'mentor_profile'
            
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
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        content = {'message': f'Hello, {request.user.username}! This is a protected view.'}
        return Response(content)

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
        # Get receiver from the request data
        receiver_id = request.data.get('receiver')
        if not receiver_id:
            return Response(
                {"error": "Receiver is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return Response(
                {"error": "Receiver not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if this is a valid messaging pair
        if not self._check_valid_messaging_pair(request.user, receiver):
            return Response(
                {"error": "You can only message users you have a mentorship relationship with"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create the message
        message_data = request.data.copy()
        message_data['sender'] = request.user.id
        
        serializer = MessageSerializer(data=message_data, context={'request': request})
        
        if serializer.is_valid():
            # Handle file upload
            file = request.FILES.get('file')
            if file:
                # Validate file size (5MB limit)
                if file.size > 5 * 1024 * 1024:  # 5MB
                    return Response(
                        {"error": "File size exceeds 5MB limit"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Validate file type
                allowed_extensions = ['.pdf', '.docx', '.xlsx', '.pptx', '.txt', '.csv', '.png', '.jpeg', '.jpg', '.gif']
                file_extension = os.path.splitext(file.name)[1].lower()
                if file_extension not in allowed_extensions:
                    return Response(
                        {"error": f"File type {file_extension} not allowed"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            message = serializer.save(sender=request.user, receiver=receiver, file=file)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request, user_id=None):
        """Get message history with a specific user"""
        if not user_id:
            return Response(
                {"error": "User ID is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if this is a valid messaging pair
        if not self._check_valid_messaging_pair(request.user, other_user):
            return Response(
                {"error": "You can only view messages with users you have a mentorship relationship with"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get messages between these two users
        messages = Message.objects.filter(
            (Q(sender=request.user) & Q(receiver=other_user)) |
            (Q(sender=other_user) & Q(receiver=request.user))
        ).order_by('timestamp')
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    def _check_valid_messaging_pair(self, user1, user2):
        """Check if two users can message each other (mentor-student relationship)"""
        from .models import MentorshipRequest
        
        # Check if there's an accepted mentorship request between them
        mentorship_exists = MentorshipRequest.objects.filter(
            Q(student=user1, mentor=user2, status='accepted') |
            Q(student=user2, mentor=user1, status='accepted')
        ).exists()
        
        return mentorship_exists

class MessageStreamView(APIView):
    permission_classes = [IsAuthenticated, IsMessageAllowed]
    
    def get(self, request, user_id):
        """Stream real-time messages for a conversation"""
        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        
        # Check if this is a valid messaging pair
        message_api = MessageAPIView()
        if not message_api._check_valid_messaging_pair(request.user, other_user):
            return JsonResponse({"error": "Invalid messaging pair"}, status=403)
        
        # Create SSE response
        response = StreamingHttpResponse(
            self._event_stream(request.user, other_user),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['Connection'] = 'keep-alive'
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Headers'] = 'Cache-Control'
        
        return response
    
    def _event_stream(self, current_user, other_user):
        """Generator for SSE events"""
        last_check = timezone.now()
        
        while True:
            # Check for new messages
            new_messages = Message.objects.filter(
                sender=other_user,
                receiver=current_user,
                timestamp__gt=last_check
            ).order_by('timestamp')
            
            for message in new_messages:
                serializer = MessageSerializer(message)
                yield f"data: {json.dumps(serializer.data)}\n\n"
            
            if new_messages:
                last_check = new_messages.last().timestamp
            
            # Wait before checking again
            time.sleep(2)

class RateLimitedRegisterView(RegisterView):
    @rate_limit(max_requests=5, timeframe=60)  # 5 requests per minute
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class RateLimitedTokenObtainPairView(TokenObtainPairView):
    @rate_limit(max_requests=5, timeframe=60)  # 5 requests per minute
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class RateLimitedTokenRefreshView(TokenRefreshView):
    @rate_limit(max_requests=10, timeframe=60)  # 10 requests per minute
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

@csrf_exempt
def test_endpoint(request):
    if request.method == 'GET':
        return JsonResponse({
            'message': 'Test endpoint working',
            'method': 'GET',
            'user': request.user.username if request.user.is_authenticated else 'Anonymous'
        })
    elif request.method == 'POST':
        return JsonResponse({
            'message': 'Test endpoint working',
            'method': 'POST',
            'data': dict(request.POST)
        })

class SimpleTestView(APIView):
    """Simple API test view"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'message': 'API test endpoint working',
            'user': request.user.username if request.user.is_authenticated else 'Anonymous',
            'time': timezone.now()
        })
    
    def post(self, request):
        return Response({
            'message': 'POST request received',
            'data': request.data
        })

def super_simple_test(request):
    return HttpResponse("Super simple test working!")
