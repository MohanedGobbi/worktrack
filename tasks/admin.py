from django.contrib import admin
from tasks.models import Task, Tag, TaskComment, Correspondence, CorrespondenceAcknowledgement, TaskTodo, TaskTodoAttachment




@admin.register(Correspondence)
class CorrespondenceAdmin(admin.ModelAdmin):
    list_display  = ('title', 'correspondence_type', 'priority', 'status', 'work_module', 'created_by', 'deadline', 'created_at')
    list_filter   = ('correspondence_type', 'priority', 'status', 'created_at')
    search_fields = ('title', 'reference_number', 'description', 'created_by__email')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('assigned_to',)
    fieldsets = (
        ('Basic Info', {'fields': ('title', 'description', 'correspondence_type', 'reference_number')}),
        ('Status & Priority', {'fields': ('priority', 'status', 'deadline')}),
        ('Module & Assignment', {'fields': ('work_module', 'created_by', 'assigned_to')}),
        ('Files', {'fields': ('attachment', 'cover_image')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(CorrespondenceAcknowledgement)
class CorrespondenceAcknowledgementAdmin(admin.ModelAdmin):
    list_display  = ('correspondence', 'user', 'acknowledged_at')
    list_filter   = ('acknowledged_at',)
    search_fields = ('correspondence__title', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('acknowledged_at',)



@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'deadline', 'priority', 'status', 'created_at')
    list_filter = ('status', 'priority', 'deadline', 'created_at')
    search_fields = ('title', 'description', 'created_by__email')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('assigned_to',)
    
    fieldsets = (
        ('Task Details', {'fields': ('title', 'description')}),
        ('Assignment', {'fields': ('created_by', 'assigned_to')}),
        ('Timeline & Priority', {'fields': ('deadline', 'priority', 'estimated_hours')}),
        ('KPI', {'fields': ('kpi_weight', 'status')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )




@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'created_at')
    search_fields = ('name',)


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('task__title', 'author__email', 'message')
    readonly_fields = ('created_at', 'updated_at')


class TaskTodoAttachmentInline(admin.TabularInline):
    model = TaskTodoAttachment
    extra = 0
    readonly_fields = ('uploaded_at',)


@admin.register(TaskTodo)
class TaskTodoAdmin(admin.ModelAdmin):
    list_display = ('title', 'task', 'status', 'priority', 'created_by', 'created_at')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('title', 'description', 'task__title', 'created_by__email')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    inlines = [TaskTodoAttachmentInline]
    fieldsets = (
        ('TODO Details', {'fields': ('task', 'title', 'description')}),
        ('Status', {'fields': ('status', 'priority', 'completed_at')}),
        ('Meta', {'fields': ('created_by', 'created_at', 'updated_at')}),
    )

