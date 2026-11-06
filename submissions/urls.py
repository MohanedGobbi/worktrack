from django.urls import path, include
from rest_framework.routers import DefaultRouter
from submissions.views import SubmissionViewSet, SubmissionCommentViewSet

router = DefaultRouter()
router.register(r'', SubmissionViewSet, basename='submission')

urlpatterns = [
    path('', include(router.urls)),
]
