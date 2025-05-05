from rest_framework import permissions
from .models import MentorshipRequest

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if the object has a user attribute directly
        if hasattr(obj, 'user'):
            return obj.user == request.user
            
        # For StudentProject which has student.user
        if hasattr(obj, 'student'):
            return obj.student.user == request.user
            
        return False

class IsStudent(permissions.BasePermission):
    """
    Permission to only allow students to access.
    """
    def has_permission(self, request, view):
        return hasattr(request.user, 'student_profile')

class IsMentor(permissions.BasePermission):
    """
    Permission to only allow mentors to access.
    """
    def has_permission(self, request, view):
        return hasattr(request.user, 'mentor_profile')

class CanManageRequest(permissions.BasePermission):
    """
    Permission to allow students to create requests and both students and mentors
    to view their respective requests. Only allow modifications to their own requests.
    """
    def has_permission(self, request, view):
        # For list/create endpoints
        if view.action == 'create':
            # Only students can create requests
            return hasattr(request.user, 'student_profile')
        return True  # Other permissions will be checked in has_object_permission
    
    def has_object_permission(self, request, view, obj):
        # For retrieve/update/delete/accept/decline endpoints
        if view.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            # Students can only manage their own requests
            if hasattr(request.user, 'student_profile'):
                return obj.student == request.user
            # Mentors can only view requests sent to them
            elif hasattr(request.user, 'mentor_profile'):
                return obj.mentor == request.user
        
        # For accept/decline actions
        if view.action in ['accept', 'decline']:
            # Only mentors can accept/decline, and only their own requests
            if hasattr(request.user, 'mentor_profile'):
                return obj.mentor == request.user
        
        return False 

class IsMessageAllowed(permissions.BasePermission):
    """
    Custom permission to only allow messaging between matched mentors and students.
    """
    message = "You are not allowed to message this user."
    
    def has_permission(self, request, view):
        # Basic authentication check
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # For GET requests checking message history
        if request.method in permissions.SAFE_METHODS:
            # Only allow if user is either sender or receiver
            return request.user == obj.sender or request.user == obj.receiver
        
        # For POST requests creating messages
        return True  # The validation happens in the view 