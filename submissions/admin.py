from django.contrib import admin
from submissions.models import Submission, SubmissionComment


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('task', 'worker', 'status', 'submitted_at', 'score', 'version')
    list_filter = ('status', 'submitted_at', 'reviewed_at')
    search_fields = ('task__title', 'worker__email', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'version')
    
    fieldsets = (
        ('Submission Info', {'fields': ('task', 'worker', 'version')}),
        ('Submission Content', {'fields': ('file', 'notes')}),
        ('Status & Review', {'fields': ('status', 'submitted_at', 'reviewed_at')}),
        ('Feedback & Score', {'fields': ('manager_feedback', 'score')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(SubmissionComment)
class SubmissionCommentAdmin(admin.ModelAdmin):
    list_display = ('submission', 'author', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('submission__task__title', 'author__email', 'comment')
    readonly_fields = ('created_at', 'updated_at')


