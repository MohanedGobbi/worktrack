from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate
from users.models import CustomUser, Department, Role, UserProfile
from users.serializers import (
    CustomUserSerializer, CustomUserDetailSerializer, UserRegistrationSerializer,
    DepartmentSerializer, RoleSerializer, UserProfileSerializer
)
from core.permissions import IsSuperAdmin, IsManager


class CustomUserViewSet(viewsets.ModelViewSet):
    """ViewSet for managing users."""
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # Accounts are created and changed in the admin pages (core.forms.UserAdminForm). Through the API only
        # administrators may write, so a worker cannot change a role or touch another account.
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsSuperAdmin()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CustomUserDetailSerializer
        elif self.action == 'create':
            return UserRegistrationSerializer
        return CustomUserSerializer
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return CustomUser.objects.all()
        if not self.request.user.department_id:
            return CustomUser.objects.filter(pk=self.request.user.pk)
        return CustomUser.objects.filter(department=self.request.user.department)
        
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user profile."""
        serializer = CustomUserDetailSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def team(self, request):
        """Get users in the same department (for managers)."""
        if request.user.role not in ['manager', 'super_admin']:
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        team_members = CustomUser.objects.filter(department=request.user.department) if request.user.department_id else CustomUser.objects.filter(pk=request.user.pk)
        serializer = CustomUserSerializer(team_members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_favorite(self, request, pk=None):
        """Toggle a user as favorite for the current user."""
        target_user = self.get_object()
        if target_user.pk == request.user.pk:
            return Response({'detail': 'You cannot favourite yourself.'}, status=status.HTTP_400_BAD_REQUEST)
        if request.user.favorite_users.filter(id=target_user.id).exists():
            request.user.favorite_users.remove(target_user)
            is_favorite = False
        else:
            request.user.favorite_users.add(target_user)
            is_favorite = True
        return Response({'is_favorite': is_favorite, 'user_id': target_user.id})


class DepartmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing departments."""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']


class RoleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing roles."""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    search_fields = ['name']


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user profiles."""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return UserProfile.objects.all()
        return UserProfile.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_profile(self, request):
        """Get current user's profile."""
        profile = request.user.profile
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
