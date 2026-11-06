from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'file_type', 'uploaded_by', 'uploaded_at', 'is_public')
    list_filter = ('file_type', 'is_public', 'uploaded_at')
    search_fields = ('title', 'original_filename', 'uploaded_by__email')
    readonly_fields = ('uploaded_at', 'file_size')
    
    fieldsets = (
        ('Document Info', {'fields': ('title', 'file', 'original_filename', 'file_type', 'description')}),
        ('Context (Links)', {'fields': ('task', 'submission', 'submission_comment', 'task_comment')}),
        ('Ownership & Visibility', {'fields': ('uploaded_by', 'is_public')}),
        ('Metadata', {'fields': ('file_size', 'uploaded_at')}),
    )
