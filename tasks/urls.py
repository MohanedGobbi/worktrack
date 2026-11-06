from django.urls import path, include
from rest_framework.routers import DefaultRouter
from tasks.views import TaskViewSet

router = DefaultRouter()
router.register(r'', TaskViewSet, basename='task-api')

urlpatterns = [
    path('', include(router.urls)),
]
