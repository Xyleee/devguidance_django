from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import StudentProfile, StudentProject
from .serializers import StudentProfileSerializer, StudentProjectSerializer
from users.permissions import IsOwnerOrReadOnly, IsStudent
from django.utils import timezone
from mentors.models import MentorshipRequest

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

@extend_schema_view(
    list=extend_schema(
        operation_id='list_student_projects',
        tags=['Students', 'Projects'],
        summary='List student projects',
        description='Get a list of projects created by the authenticated student'
    ),
    create=extend_schema(
        operation_id='create_student_project',
        tags=['Students', 'Projects'],
        summary='Create student project',
        description='Create a new project for the authenticated student'
    ),
    retrieve=extend_schema(
        operation_id='get_student_project',
        tags=['Students', 'Projects'],
        summary='Get student project',
        description='Retrieve a specific student project by ID'
    ),
    update=extend_schema(
        operation_id='update_student_project',
        tags=['Students', 'Projects'],
        summary='Update student project',
        description='Update a student project (full update)'
    ),
    partial_update=extend_schema(
        operation_id='partial_update_student_project',
        tags=['Students', 'Projects'],
        summary='Partially update student project',
        description='Partially update a student project'
    ),
    destroy=extend_schema(
        operation_id='delete_student_project',
        tags=['Students', 'Projects'],
        summary='Delete student project',
        description='Delete a student project'
    )
)
class StudentProjectViewSet(viewsets.ModelViewSet):
    serializer_class = StudentProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly, IsStudent]
    
    def get_queryset(self):
        return StudentProject.objects.filter(student__user=self.request.user)
    
    def perform_create(self, serializer):
        student_profile = get_object_or_404(StudentProfile, user=self.request.user)
        serializer.save(student=student_profile)

    @extend_schema(
        operation_id='find_projects_by_tools',
        tags=['Students', 'Projects', 'Search'],
        summary='Find projects by tools used',
        description='Find student projects that use a specific tool or technology',
        parameters=[
            OpenApiParameter(
                name='tool',
                description='Tool or technology to search for (e.g., "React", "Django", "Python")',
                required=True,
                type=str,
                location=OpenApiParameter.QUERY,
                examples=[
                    OpenApiExample('React', value='React'),
                    OpenApiExample('Django', value='Django'),
                    OpenApiExample('Python', value='Python')
                ]
            )
        ],
        responses={
            200: StudentProjectSerializer(many=True),
            400: OpenApiResponse(description='Tool parameter is required')
        }
    )
    @action(detail=False, methods=['get'])
    def by_tools(self, request):
        tool = request.query_params.get('tool', None)
        if not tool:
            return Response({"detail": "Tool parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        projects = StudentProject.objects.filter(
            student__user=request.user,
            tools_used__icontains=tool.lower()
        )
        
        if not projects.exists():
            return Response({
                "detail": f"No projects found with tool: {tool}",
                "results": []
            })
        
        serializer = self.get_serializer(projects, many=True)
        return Response(serializer.data)
