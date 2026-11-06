from django.contrib import admin
from django.core.cache import cache
from .models import SiteConfiguration, AllowedHost, BlockedHostAttempt

@admin.register(AllowedHost)
class AllowedHostAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('hostname',)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Clear cache so changes take effect immediately
        cache.delete(f"allowed_host_{obj.hostname}")
        if obj.hostname == '*':
            cache.delete('allowed_host_wildcard')

@admin.register(BlockedHostAttempt)
class BlockedHostAttemptAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'ip_address', 'attempt_count', 'last_attempt')
    list_filter = ('last_attempt',)
    search_fields = ('hostname', 'ip_address')
    readonly_fields = ('hostname', 'ip_address', 'attempt_count', 'first_attempt', 'last_attempt')

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ('app_name', 'primary_color', 'secondary_color')
    
    def has_add_permission(self, request):
        # Only allow one SiteConfiguration object to be created
        if SiteConfiguration.objects.exists():
            return False
        return super().has_add_permission(request)
        
    def has_delete_permission(self, request, obj=None):
        # We don't want to allow deleting the configuration
        return False
        
    def changelist_view(self, request, extra_context=None):
        from django.shortcuts import redirect
        return redirect('site-settings')

    def add_view(self, request, form_url='', extra_context=None):
        from django.shortcuts import redirect
        return redirect('site-settings')

    def change_view(self, request, object_id, form_url='', extra_context=None):
        from django.shortcuts import redirect
        return redirect('site-settings')
