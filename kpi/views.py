from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from kpi.models import KPIDefinition, UserKPI, KPIWeight
from kpi.serializers import KPIDefinitionSerializer, UserKPISerializer, KPIWeightSerializer
from kpi.engine import recalculate_user_kpi, recalculate_all_kpis
from core.permissions import IsSuperAdmin


class KPIDefinitionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing KPI definitions."""
    queryset = KPIDefinition.objects.all()
    serializer_class = KPIDefinitionSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    search_fields = ['name']


class UserKPIViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing user KPIs."""
    queryset = UserKPI.objects.all()
    serializer_class = UserKPISerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['user', 'month']
    ordering_fields = ['month', 'total_score']
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'super_admin':
            return UserKPI.objects.all()
        elif user.role == 'manager':
            from users.models import CustomUser
            team_users = CustomUser.objects.filter(department=user.department)
            return UserKPI.objects.filter(user__in=team_users)
        else:  # worker
            return UserKPI.objects.filter(user=user)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_kpi(self, request):
        """Get current user's latest KPI."""
        kpi = UserKPI.objects.filter(user=request.user).order_by('-month').first()
        if kpi:
            serializer = UserKPISerializer(kpi)
            return Response(serializer.data)
        return Response(
            {"detail": "No KPI records found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def history(self, request):
        """Get current user's KPI history."""
        kpis = UserKPI.objects.filter(user=request.user).order_by('-month')[:12]
        serializer = UserKPISerializer(kpis, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsSuperAdmin])
    def recalculate_all(self, request):
        """Recalculate KPIs for all users."""
        month = request.data.get('month')
        if month:
            from datetime import datetime
            month = datetime.strptime(month, '%Y-%m-%d').date().replace(day=1)
        
        kpis = recalculate_all_kpis(month)
        serializer = UserKPISerializer(kpis, many=True)
        return Response(
            {"detail": f"Recalculated {len(kpis)} KPIs", "data": serializer.data},
            status=status.HTTP_200_OK
        )


class KPIWeightViewSet(viewsets.ModelViewSet):
    """ViewSet for managing KPI weights."""
    queryset = KPIWeight.objects.all()
    serializer_class = KPIWeightSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    
    @action(detail=False, methods=['get', 'put'], permission_classes=[permissions.IsAuthenticated])
    def current(self, request):
        """Get or update current KPI weights."""
        weights = KPIWeight.get_weights()
        
        if request.method == 'PUT':
            serializer = KPIWeightSerializer(weights, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = KPIWeightSerializer(weights)
        return Response(serializer.data)
