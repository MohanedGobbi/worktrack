from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import CustomUserViewSet, DepartmentViewSet, RoleViewSet, UserProfileViewSet

router = DefaultRouter()
router.register(r'', CustomUserViewSet, basename='user')
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'profiles', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
]
