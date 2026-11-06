from django.contrib import admin
from kpi.models import KPIDefinition, UserKPI, KPIWeight


@admin.register(KPIDefinition)
class KPIDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'weight', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserKPI)
class UserKPIAdmin(admin.ModelAdmin):
    list_display = ('user', 'month', 'total_score', 'calculated_at')
    list_filter = ('month', 'calculated_at')
    search_fields = ('user__email',)
    readonly_fields = ('calculated_at', 'created_at', 'updated_at')
    
    fieldsets = (
        ('User & Period', {'fields': ('user', 'month')}),
        ('KPI Metrics', {
            'fields': (
                'completion_rate',
                'on_time_rate',
                'quality_score',
                'rejection_rate',
                'productivity_score'
            )
        }),
        ('Score', {'fields': ('total_score',)}),
        ('Metadata', {'fields': ('calculated_at', 'created_at', 'updated_at')}),
    )


@admin.register(KPIWeight)
class KPIWeightAdmin(admin.ModelAdmin):
    list_display = ('id', 'completion_rate_weight', 'on_time_rate_weight', 'quality_score_weight', 'productivity_score_weight')
    
    def has_add_permission(self, request):
        return not KPIWeight.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
