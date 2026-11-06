from django.contrib import admin
from .models import WorkModule

@admin.register(WorkModule)
class WorkModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon_class', 'color', 'created_at')
    prepopulated_fields = {'slug': ('name',)}

    def has_delete_permission(self, request, obj=None):
        if obj and obj.slug == 'contact-submissions':
            return False
        return super().has_delete_permission(request, obj)
