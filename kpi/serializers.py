from rest_framework import serializers
from kpi.models import KPIDefinition, UserKPI, KPIWeight


class KPIDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = KPIDefinition
        fields = ['id', 'name', 'description', 'weight', 'formula', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserKPISerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    month_display = serializers.SerializerMethodField()
    
    class Meta:
        model = UserKPI
        fields = [
            'id', 'user', 'user_email', 'month', 'month_display',
            'completion_rate', 'on_time_rate', 'quality_score',
            'rejection_rate', 'productivity_score', 'total_score',
            'calculated_at', 'created_at'
        ]
        read_only_fields = ['id', 'calculated_at', 'created_at']
    
    def get_month_display(self, obj):
        return obj.month.strftime('%B %Y')


class KPIWeightSerializer(serializers.ModelSerializer):
    class Meta:
        model = KPIWeight
        fields = [
            'completion_rate_weight', 'on_time_rate_weight',
            'quality_score_weight', 'productivity_score_weight', 'updated_at'
        ]
        read_only_fields = ['updated_at']
