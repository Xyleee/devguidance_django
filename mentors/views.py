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
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'mentors_profile__name', 'mentors_profile__expertise_tags']

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
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsStudent])
    def student(self, request):
        """Endpoint for students to view their requests"""
        requests = MentorshipRequest.objects.filter(student=request.user)
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsMentor])
    def mentor(self, request):
        """Endpoint for mentors to view requests sent to them"""
        requests = MentorshipRequest.objects.filter(mentor=request.user)
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)
