from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import MentorProfile, MentorshipRequest
from .serializers import (
    MentorProfileSerializer, 
    MentorListSerializer,
    MentorshipRequestSerializer
)
from django.contrib.auth.models import User
from users.permissions import IsOwnerOrReadOnly, IsStudent, IsMentor
from .permissions import CanManageRequest
from django.db.models import Q

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

@extend_schema_view(
    list=extend_schema(
        operation_id='list_mentor_profiles',
        tags=['Mentors'],
        summary='List mentor profiles',
        description='Get a list of mentor profiles with search functionality',
        parameters=[
            OpenApiParameter(
                name='search',
                description='Search mentors by name or expertise tags',
                required=False,
                type=str,
                location=OpenApiParameter.QUERY
            )
        ]
    ),
    create=extend_schema(
        operation_id='create_mentor_profile',
        tags=['Mentors'],
        summary='Create mentor profile',
        description='Create a new mentor profile for the authenticated user'
    ),
    retrieve=extend_schema(
        operation_id='get_mentor_profile',
        tags=['Mentors'],
        summary='Get mentor profile',
        description='Retrieve a specific mentor profile by ID',
        parameters=[
            OpenApiParameter(
                name='id',
                description='ID of the mentor profile to retrieve',
                required=True,
                type=int,
                location=OpenApiParameter.PATH
            )
        ]
    ),
    update=extend_schema(
        operation_id='update_mentor_profile',
        tags=['Mentors'],
        summary='Update mentor profile',
        description='Update a mentor profile (full update)',
        parameters=[
            OpenApiParameter(
                name='id',
                description='ID of the mentor profile to update',
                required=True,
                type=int,
                location=OpenApiParameter.PATH
            )
        ]
    ),
    partial_update=extend_schema(
        operation_id='partial_update_mentor_profile',
        tags=['Mentors'],
        summary='Partially update mentor profile',
        description='Partially update a mentor profile',
        parameters=[
            OpenApiParameter(
                name='id',
                description='ID of the mentor profile to partially update',
                required=True,
                type=int,
                location=OpenApiParameter.PATH
            )
        ]
    ),
    destroy=extend_schema(
        operation_id='delete_mentor_profile',
        tags=['Mentors'],
        summary='Delete mentor profile',
        description='Delete a mentor profile',
        parameters=[
            OpenApiParameter(
                name='id',
                description='ID of the mentor profile to delete',
                required=True,
                type=int,
                location=OpenApiParameter.PATH
            )
        ]
    )
)
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
    
    @extend_schema(
        operation_id='get_my_mentor_profile',
        tags=['Mentors'],
        summary='Get my mentor profile',
        description='Retrieve the mentor profile of the authenticated user',
        responses={
            200: MentorProfileSerializer,
            404: OpenApiResponse(description='Profile not found')
        }
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        try:
            profile = MentorProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except MentorProfile.DoesNotExist:
            return Response({"detail": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
            
    @extend_schema(
        operation_id='find_mentors_by_expertise',
        tags=['Mentors', 'Search'],
        summary='Find mentors by expertise',
        description='Find mentor profiles that have a specific expertise tag',
        parameters=[
            OpenApiParameter(
                name='tag',
                description='Expertise tag to search for (e.g., "Python", "Web Development", "Mobile")',
                required=True,
                type=str,
                location=OpenApiParameter.QUERY,
                examples=[
                    OpenApiExample('Python', value='Python'),
                    OpenApiExample('Web Development', value='Web Development'),
                    OpenApiExample('Mobile', value='Mobile')
                ]
            )
        ],
        responses={
            200: MentorProfileSerializer(many=True),
            400: OpenApiResponse(description='Expertise tag parameter is required')
        }
    )
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

    @extend_schema(
        operation_id='get_mentor_availability',
        tags=['Mentors'],
        summary='Get mentor availability',
        description='Check if a mentor is available for new mentorships',
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='MentorAvailability',
                    fields={
                        'is_available': OpenApiTypes.BOOL,
                        'active_mentorships': OpenApiTypes.INT,
                        'max_mentorships': OpenApiTypes.INT
                    }
                ),
                description='Mentor availability status',
                examples=[
                    OpenApiExample(
                        'Available Mentor',
                        value={
                            "is_available": True,
                            "active_mentorships": 2,
                            "max_mentorships": 5
                        }
                    ),
                    OpenApiExample(
                        'Unavailable Mentor',
                        value={
                            "is_available": False,
                            "active_mentorships": 5,
                            "max_mentorships": 5
                        }
                    )
                ]
            )
        }
    )
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

@extend_schema(
    operation_id='browse_mentors',
    tags=['Mentors', 'Browse'],
    summary='Browse available mentors',
    description='''
    Browse and search through available mentors. This endpoint is designed for students
    to discover and find mentors that match their learning goals.
    
    **Features:**
    - Search by mentor name, username, or expertise
    - Filter mentors by specific technologies or domains
    - Discover mentors with proven experience
    ''',
    parameters=[
        OpenApiParameter(
            name='search',
            description='Search mentors by name, username, or expertise tags',
            required=False,
            type=str,
            location=OpenApiParameter.QUERY,
            examples=[
                OpenApiExample('Technology Search', value='Python'),
                OpenApiExample('Name Search', value='John'),
                OpenApiExample('Domain Search', value='Web Development')
            ]
        )
    ],
    responses={
        200: OpenApiResponse(
            response=MentorListSerializer(many=True),
            description='List of available mentors',
            examples=[
                OpenApiExample(
                    'Available Mentors',
                    value=[
                        {
                            "id": 1,
                            "username": "senior_dev",
                            "mentor_profile": {
                                "id": 1,
                                "name": "John Smith",
                                "bio": "Senior developer with 8+ years experience",
                                "expertise_tags": ["Python", "Django", "React"],
                                "years_of_experience": 8,
                                "company": "Tech Corp",
                                "is_available": True
                            }
                        }
                    ]
                )
            ]
        )
    }
)
class MentorListView(generics.ListAPIView):
    """View for students to browse available mentors"""
    queryset = User.objects.filter(mentors_profile__isnull=False)
    serializer_class = MentorListSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'mentors_profile__name', 'mentors_profile__expertise_tags']

@extend_schema_view(
    list=extend_schema(
        operation_id='list_mentorship_requests',
        tags=['Mentorship'],
        summary='List mentorship requests',
        description='Get mentorship requests based on user role (student sees their requests, mentor sees requests to them)'
    ),
    create=extend_schema(
        operation_id='create_mentorship_request',
        tags=['Mentorship'],
        summary='Create mentorship request',
        description='Create a new mentorship request (students can request mentorship from mentors)'
    ),
    retrieve=extend_schema(
        operation_id='get_mentorship_request',
        tags=['Mentorship'],
        summary='Get mentorship request',
        description='Retrieve a specific mentorship request by ID',
        parameters=[
            OpenApiParameter(
                name='id',
                description='ID of the mentorship request to retrieve',
                required=True,
                type=int,
                location=OpenApiParameter.PATH
            )
        ]
    ),
    update=extend_schema(
        operation_id='update_mentorship_request',
        tags=['Mentorship'],
        summary='Update mentorship request',
        description='Update a mentorship request (full update)',
        parameters=[
            OpenApiParameter(
                name='id',
                description='ID of the mentorship request to update',
                required=True,
                type=int,
                location=OpenApiParameter.PATH
            )
        ]
    ),
    partial_update=extend_schema(
        operation_id='partial_update_mentorship_request',
        tags=['Mentorship'],
        summary='Partially update mentorship request',
        description='Partially update a mentorship request',
        parameters=[
            OpenApiParameter(
                name='id',
                description='ID of the mentorship request to partially update',
                required=True,
                type=int,
                location=OpenApiParameter.PATH
            )
        ]
    ),
    destroy=extend_schema(
        operation_id='delete_mentorship_request',
        tags=['Mentorship'],
        summary='Delete mentorship request',
        description='Delete a mentorship request',
        parameters=[
            OpenApiParameter(
                name='id',
                description='ID of the mentorship request to delete',
                required=True,
                type=int,
                location=OpenApiParameter.PATH
            )
        ]
    )
)
class MentorshipRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for managing mentorship requests"""
    serializer_class = MentorshipRequestSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageRequest]
    
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
            Q(student=user) | Q(mentor=user)
        )
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        
        # Include student details if user is a mentor viewing requests
        if hasattr(user, 'mentors_profile'):
            context['include_student_details'] = True
        
        return context
    
    @extend_schema(
        operation_id='accept_mentorship_request',
        tags=['Mentorship'],
        summary='Accept mentorship request',
        description='Accept a mentorship request (mentors only)',
        responses={
            200: MentorshipRequestSerializer,
            403: OpenApiResponse(description='Permission denied - not the target mentor'),
            404: OpenApiResponse(description='Request not found')
        }
    )
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated, IsMentor])
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
    
    @extend_schema(
        operation_id='decline_mentorship_request',
        tags=['Mentorship'],
        summary='Decline mentorship request',
        description='Decline a mentorship request with optional reason (mentors only)',
        request=inline_serializer(
            name='DeclineRequest',
            fields={
                'rejection_reason': OpenApiTypes.STR
            }
        ),
        responses={
            200: MentorshipRequestSerializer,
            403: OpenApiResponse(description='Permission denied - not the target mentor'),
            404: OpenApiResponse(description='Request not found')
        }
    )
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated, IsMentor])
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
    
    @extend_schema(
        operation_id='get_student_mentorship_requests',
        tags=['Mentorship', 'Students'],
        summary='Get student mentorship requests',
        description='Get all mentorship requests made by the authenticated student',
        responses={
            200: MentorshipRequestSerializer(many=True)
        }
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsStudent])
    def student(self, request):
        """Endpoint for students to view their requests"""
        requests = MentorshipRequest.objects.filter(student=request.user)
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        operation_id='get_mentor_mentorship_requests',
        tags=['Mentorship', 'Mentors'],
        summary='Get mentor mentorship requests',
        description='Get all mentorship requests received by the authenticated mentor',
        responses={
            200: MentorshipRequestSerializer(many=True)
        }
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsMentor])
    def mentor(self, request):
        """Endpoint for mentors to view requests sent to them"""
        requests = MentorshipRequest.objects.filter(mentor=request.user)
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)
