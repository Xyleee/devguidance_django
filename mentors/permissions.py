from rest_framework import permissions

class CanManageRequest(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Allow if the user is either the student who created the request
        # or the mentor who received it
        return request.user == obj.student or request.user == obj.mentor
