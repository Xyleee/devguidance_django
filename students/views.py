from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import StudentProfile, StudentProject
from .serializers import StudentProfileSerializer, StudentProjectSerializer
from users.permissions import IsOwnerOrReadOnly, IsStudent
from django.utils import timezone
from mentors.models import MentorshipRequest

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

    @action(detail=False, methods=['get'])
    def by_tech_stack(self, request):
        tag = request.query_params.get('tag', None)
        if tag:
            profiles = StudentProfile.objects.filter(tech_stack__contains=[tag])
            serializer = self.get_serializer(profiles, many=True)
            return Response(serializer.data)
        return Response({"detail": "Tag parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_year_level(self, request):
        level = request.query_params.get('level', None)
        if level:
            profiles = StudentProfile.objects.filter(year_level=level)
            serializer = self.get_serializer(profiles, many=True)
            return Response(serializer.data)
        return Response({"detail": "Level parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

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
