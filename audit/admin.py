from django.contrib import admin
from audit.models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'object_type', 'user', 'object_str', 'created_at', 'ip_address')
    list_filter = ('action', 'object_type', 'created_at')
    search_fields = ('user__email', 'object_str', 'description')
    readonly_fields = ('created_at', 'changes')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
