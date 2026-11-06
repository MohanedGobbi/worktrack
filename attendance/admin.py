from django.contrib import admin
from .models import AttendanceRecord

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'check_in', 'check_out', 'status', 'total_hours')
    list_filter = ('date', 'status', 'user__role', 'user__department')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'notes')
    ordering = ('-date', '-check_in')
    readonly_fields = ('created_at', 'updated_at', 'total_hours')
    
    fieldsets = (
        ('User & Date', {
            'fields': ('user', 'date')
        }),
        ('Time Tracking', {
            'fields': ('check_in', 'check_out', 'total_hours')
        }),
        ('Status & Notes', {
            'fields': ('status', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        obj.calculate_hours()
        super().save_model(request, obj, form, change)
