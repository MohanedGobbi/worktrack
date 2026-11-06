from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """Permission for Super Admin only."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'super_admin'


class IsManager(permissions.BasePermission):
    """Permission for Manager role."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['manager', 'super_admin']


class IsWorker(permissions.BasePermission):
    """Permission for Worker role."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['worker', 'manager', 'super_admin']


class IsTaskOwner(permissions.BasePermission):
    """Permission to check if user is the task creator."""
    
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user


class IsTaskAssignee(permissions.BasePermission):
    """Permission to check if user is assigned to the task."""
    
    def has_object_permission(self, request, view, obj):
        return request.user in obj.assigned_to.all()


class IsSubmissionOwner(permissions.BasePermission):
    """Permission to check if user is the submission creator."""
    
    def has_object_permission(self, request, view, obj):
        return obj.worker == request.user or obj.task.created_by == request.user
