from rest_framework import serializers
from users.models import CustomUser, Department, Role, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'position', 'hire_date', 'phone', 'bio', 'avatar', 'manager']
        # Who someone reports to and their photo are set in the admin pages / profile page, not through this API.
        read_only_fields = ['id', 'hire_date', 'avatar', 'manager']


class CustomUserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'department', 'is_active', 'profile', 'created_at']
        read_only_fields = ['id', 'created_at', 'role', 'is_active', 'department']


class CustomUserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'department', 'is_active', 'profile', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'role', 'is_active', 'department']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'password', 'password_confirm']
        
    def validate(self, data):
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return data
    
    def create(self, validated_data):
        # Never take a role from the request: new accounts are staff; administrators change roles in the admin pages.
        user = CustomUser.objects.create_user(role='worker', **validated_data)
        return user


class DepartmentSerializer(serializers.ModelSerializer):
    manager_email = serializers.CharField(source='manager.email', read_only=True)
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'manager', 'manager_email', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
