from django.urls import path, include
from rest_framework.routers import DefaultRouter
from kpi.views import KPIDefinitionViewSet, UserKPIViewSet, KPIWeightViewSet

router = DefaultRouter()
router.register(r'definitions', KPIDefinitionViewSet, basename='kpi-definition')
router.register(r'user', UserKPIViewSet, basename='user-kpi')
router.register(r'weights', KPIWeightViewSet, basename='kpi-weight')

urlpatterns = [
    path('', include(router.urls)),
]
