"""
URL Configuration for worktrack_pro project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
# from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from core.views import (
    site_settings_view, host_management_view, toggle_host_status, 
    whitelist_host_action, delete_host_action
)
from core.views_translations import (
    translation_manager, api_update_translation, api_bulk_update_translations, api_manage_translations,
)
from core.template_views import (
    # Auth views
    home, submit_contact_message, login_view, register_view, logout_view,
    # Dashboard views
    dashboard, admin_dashboard, module_dashboard, manager_portal, worker_portal, roadmap_gantt,
    module_create, module_edit, module_delete, update_module_order, archived_modules, module_bulk_action,
    available_modules, enroll_module, module_add_user, module_remove_user, module_unenroll,
    group_create, group_edit, group_delete, manage_groups, update_group_order,
    template_dashboard, template_create, template_edit, template_delete, template_bulk_delete, template_tasks_manage,
    # Correspondence page
    administrative_correspondence,
    corr_todo_management, corr_todo_add, corr_todo_update, corr_todo_toggle, corr_todo_delete, corr_todo_list_ajax, module_todo_clear, module_todo_wipe_all,
    organizational_intelligence_view, task_toggle_complete_ajax, sidebar_visibility_ajax, system_profiles_ajax, user_assign_profiles_ajax, system_profiles_management,
    reset_database_ajax,
    # Task views
    task_list, task_detail, task_create, task_edit, task_delete, delete_task_file, acknowledge_task, get_custom_fields, task_allow_resubmission, task_start_new_version,
    task_reactivate,
    # Submission views
    submission_list, submission_detail, submission_create, submission_edit, submission_delete, submission_update_status, submission_submit, submission_bulk_action,
    # Notification views
    notifications_list, notification_mark_as_read, notification_delete, notification_mark_all_as_read,
    # Profile views
    profile, profile_update, profile_preferences, profile_change_password,
    # Admin views
    user_management, user_toggle_status, get_user_data, user_delete, kpi_dashboard, audit_logs, admin_settings,
    # User registration view
    register_new_user,
    # Error handlers
    handler_404, handler_500,
    # -- NEW IMPROVEMENTS ----------------------------------------------
    # Notification live poll (Improvement #4)
    notifications_unread_count,
    # Task comments / discussion thread (Improvement #3)
    task_comment_add, task_comment_delete,
    # Global search (Improvement #11)
    global_search,
    # CSV exports (Improvement #7)
    export_tasks_csv, export_submissions_csv, export_performance_report_csv,
    # Analytics pages (Improvements #5 & #6)
    worker_performance, manager_analytics,
    # Avatar upload (Improvement #9)
    profile_avatar_upload,
    # Kanban board (Improvement #12)
    task_kanban, task_kanban_move,
    # Calendar view (Improvement #13)
    task_calendar,
    # Dark mode (Improvement #14)
    set_dark_mode,
    # Offline Map Hub
    offline_map_manager, map_tile_proxy,
    # Bulk task actions (Improvement #15)
    task_bulk_action,
    # Submission version comparison (Improvement #10)
    submission_versions, version_data_archive,
    # Submission summary exports
    submission_summary_export_xlsx, submission_summary_export_pdf,
    # Correspondence (separate model)
    correspondence_detail, correspondence_create, correspondence_edit,
    correspondence_acknowledge, correspondence_delete,
    # Admin TODO management
    task_todo_add, task_todo_update, task_todo_toggle, task_todo_delete,
    task_todo_upload, task_todo_delete_file,
    module_todo_delete_file,
    # Impersonation
    impersonate_user, revert_impersonation, login_as_page,
    # Global Map Dashboard
    global_map,
)

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
    path('admin/', admin.site.urls),
    
    # Attendance Route
    path('attendance/', include('attendance.urls')),
    
    # Messaging Route
    path('messaging/', include('messaging.urls')),
    
    # ========== HTML Template Routes ==========
    path('', home, name='home'),
    path('submit-contact/', submit_contact_message, name='submit-contact'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('register-user/', register_new_user, name='register-new-user'),
    path('logout/', logout_view, name='logout'),
    
    # Password Reset Routes
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='auth/password_reset.html',
        email_template_name='auth/password_reset_email.html',
        subject_template_name='auth/password_reset_subject.txt'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'), name='password_reset_complete'),
    
    # Dashboard routes
    path('dashboard/', dashboard, name='dashboard'),
    path('roadmap/', roadmap_gantt, name='roadmap-gantt'),
    path('manager-portal/', manager_portal, name='manager-portal'),
    path('worker-portal/', worker_portal, name='worker-portal'),
    path('modules/available/', available_modules, name='available-modules'),
    path('module/create/', module_create, name='module-create'),
    path('module/<str:module_slug>/', module_dashboard, name='module-dashboard'),
    path('module/<str:module_slug>/enroll/', enroll_module, name='enroll-module'),
    path('module/<str:module_slug>/unenroll/', module_unenroll, name='unenroll-module'),
    path('module/<str:module_slug>/add-user/', module_add_user, name='module-add-user'),
    path('module/<str:module_slug>/remove-user/<int:user_id>/', module_remove_user, name='module-remove-user'),
    path('module/<str:module_slug>/edit/', module_edit, name='module-edit'),
    path('module/<str:module_slug>/delete/', module_delete, name='module-delete'),
    path('group/create/', group_create, name='group-create'),
    path('group/<str:group_slug>/edit/', group_edit, name='group-edit'),
    path('group/<str:group_slug>/delete/', group_delete, name='group-delete'),
    path('groups/manage/', manage_groups, name='manage-groups'),
    path('modules/bulk-action/', module_bulk_action, name='module-bulk-action'),
    path('module/reorder/update/', update_module_order, name='update-module-order'),
    path('groups/reorder/update/', update_group_order, name='update-group-order'),
    path('modules/archived/', archived_modules, name='archived-modules'),
    path('templates/', template_dashboard, name='template-dashboard'),
    path('templates/create/', template_create, name='template-create'),
    path('templates/edit/<int:template_id>/', template_edit, name='template-edit'),
    path('templates/delete/<int:template_id>/', template_delete, name='template-delete'),
    path('templates/bulk-delete/', template_bulk_delete, name='template-bulk-delete'),
    path('templates/manage/<int:template_id>/', template_tasks_manage, name='template-tasks-manage'),
    path('correspondence/', administrative_correspondence, name='admin-correspondence'),
    path('correspondence/create/', correspondence_create, name='correspondence-create'),
    path('correspondence/<int:pk>/', correspondence_detail, name='correspondence-detail'),
    path('correspondence/<int:pk>/edit/', correspondence_edit, name='correspondence-edit'),
    path('correspondence/<int:pk>/delete/', correspondence_delete, name='correspondence-delete'),
    path('correspondence/<int:pk>/acknowledge/', correspondence_acknowledge, name='correspondence-acknowledge'),

    
    # Task routes
    path('tasks/', task_list, name='task-list'),
    path('tasks/<int:task_id>/', task_detail, name='task-detail'),
    path('tasks/create/', task_create, name='task-create'),
    path('tasks/<int:task_id>/edit/', task_edit, name='task-edit'),
    path('tasks/<int:task_id>/delete/', task_delete, name='task-delete'),
    path('tasks/<int:task_id>/delete-file/', delete_task_file, name='delete-task-file'),
    path('tasks/<int:task_id>/acknowledge/', acknowledge_task, name='task-acknowledge'),
    path('tasks/<int:task_id>/allow-resubmission/', task_allow_resubmission, name='task-allow-resubmission'),
    path('tasks/<int:task_id>/get-custom-fields/', get_custom_fields, name='get-custom-fields'),
    
    # Login As Engine
    path('admin-tools/login-as/', login_as_page, name='login-as-page'),
    path('admin-tools/login-as/<int:user_id>/', impersonate_user, name='impersonate-user'),
    path('admin-tools/revert-impersonation/', revert_impersonation, name='revert-impersonation'),
    path('tasks/<int:task_id>/summary/export/xlsx/', submission_summary_export_xlsx, name='submission-summary-xlsx'),
    path('tasks/<int:task_id>/summary/export/pdf/', submission_summary_export_pdf, name='submission-summary-pdf'),
    path('tasks/<int:task_id>/start-new-version/', task_start_new_version, name='task-start-new-version'),
    path('tasks/<int:task_id>/reactivate/', task_reactivate, name='task-reactivate'),
    # Task TODO routes (admin-only)
    path('tasks/<int:task_id>/todos/add/', task_todo_add, name='task-todo-add'),
    path('tasks/todos/<int:todo_id>/update/', task_todo_update, name='task-todo-update'),
    path('tasks/todos/<int:todo_id>/toggle/', task_todo_toggle, name='task-todo-toggle'),
    path('tasks/todos/<int:todo_id>/delete/', task_todo_delete, name='task-todo-delete'),
    path('tasks/todos/<int:todo_id>/upload/', task_todo_upload, name='task-todo-upload'),
    path('tasks/todos/files/<int:file_id>/delete/', task_todo_delete_file, name='task-todo-delete-file'),
    
    # Module TODO routes (Standalone Management)
    path('todos/<str:module_slug>/manage/', corr_todo_management, name='module-todo-management'),
    path('todos/<str:module_slug>/add/', corr_todo_add, name='module-todo-add'),
    path('todos/<str:module_slug>/list-ajax/', corr_todo_list_ajax, name='module-todo-list-ajax'),
    path('todos/<int:todo_id>/update/', corr_todo_update, name='module-todo-update'),
    path('todos/<int:todo_id>/toggle/', corr_todo_toggle, name='module-todo-toggle'),
    path('todos/<int:todo_id>/delete/', corr_todo_delete, name='module-todo-delete'),
    path('todos/<str:module_slug>/clear-completed/', module_todo_clear, name='module-todo-clear-completed'),
    path('todos/<str:module_slug>/wipe-all/', module_todo_wipe_all, name='module-todo-wipe-all'),
    path('todos/files/<int:file_id>/delete/', module_todo_delete_file, name='module-todo-delete-file'),
    
    # General Organizational Intelligence Dedicated Management Hub (Item 7)
    path('organizational-intelligence/', organizational_intelligence_view, name='organizational-intelligence'),
    
    # Task Quick Complete (Item 14)
    path('tasks/<int:task_id>/quick-complete/', task_toggle_complete_ajax, name='task-quick-complete'),
    
    # Admin Quick Tools API (Item 11 & Item 12)
    path('api/sidebar-visibility/', sidebar_visibility_ajax, name='api-sidebar-visibility'),
    path('api/system-profiles/', system_profiles_ajax, name='api-system-profiles'),
    path('api/users/<int:user_id>/assign-profiles/', user_assign_profiles_ajax, name='api-user-assign-profiles'),
    path('management/system-profiles/', system_profiles_management, name='system-profiles'),

    
    # Submission routes
    path('submissions/', submission_list, name='submission-list'),
    path('submissions/create/', submission_create, name='submission-create'),
    path('submissions/<int:submission_id>/', submission_detail, name='submission-detail'),
    path('submissions/<int:submission_id>/edit/', submission_edit, name='submission-edit'),
    path('submissions/<int:submission_id>/delete/', submission_delete, name='submission-delete'),
    path('submissions/<int:submission_id>/submit/', submission_submit, name='submission-submit'),
    path('submissions/<int:submission_id>/update-status/', submission_update_status, name='submission-update-status'),
    path('submissions/bulk-action/', submission_bulk_action, name='submission-bulk-action'),
    
    # Notification routes
    path('notifications/', notifications_list, name='notifications-list'),
    path('notifications/<int:notification_id>/mark-as-read/', notification_mark_as_read, name='notification-mark-as-read'),
    path('notifications/<int:notification_id>/delete/', notification_delete, name='notification-delete'),
    path('notifications/mark-all-as-read/', notification_mark_all_as_read, name='notification-mark-all-as-read'),
    
    # Profile routes
    path('profile/', profile, name='profile'),
    path('profile/update/', profile_update, name='profile-update'),
    path('profile/preferences/', profile_preferences, name='profile-preferences'),
    path('profile/change-password/', profile_change_password, name='profile-change-password'),
    
    # Admin management routes
    # User Management routes
    path('management/users/create/', user_management, name='user-create'),
    path('management/users/edit/<int:user_id>/', user_management, name='user-edit'),
    path('management/users/', user_management, name='user-management'),
    path('admin-dashboard/users/data/<int:user_id>/', get_user_data, name='get-user-data'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('translations/', translation_manager, name='translation-manager'),
    path('translations/api/update/', api_update_translation, name='api-update-translation'),
    path('translations/api/bulk-update/', api_bulk_update_translations, name='api-bulk-update-translations'),
    path('translations/api/manage/', api_manage_translations, name='api-manage-translations'),
    path('management/users/<int:user_id>/toggle-status/', user_toggle_status, name='user-toggle-status'),
    path('management/users/<int:user_id>/delete/', user_delete, name='user-delete'),
    path('management/kpi/', kpi_dashboard, name='kpi-dashboard'),
    path('management/audit-logs/', audit_logs, name='audit-logs'),
    path('management/settings/', admin_settings, name='admin-settings'),
    path('admin-dashboard/site-settings/', site_settings_view, name='site-settings'),
    
    # Host Management UI
    path('admin-dashboard/host-management/', host_management_view, name='host-management'),
    path('management/hosts/<int:host_id>/toggle/', toggle_host_status, name='toggle-host-status'),
    path('management/hosts/<int:host_id>/delete/', delete_host_action, name='delete-host-action'),
    path('management/hosts/whitelist/<int:attempt_id>/', whitelist_host_action, name='whitelist-host-action'),
    
    # ========== API JWT Endpoints ==========
    # path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # -- NEW IMPROVEMENT ROUTES --------------------------------
    # Notification live poll
    path('api/notifications/unread-count/', notifications_unread_count, name='notifications-unread-count'),
    # Task discussion comments
    path('tasks/<int:task_id>/comments/add/', task_comment_add, name='task-comment-add'),
    path('tasks/comments/<int:comment_id>/delete/', task_comment_delete, name='task-comment-delete'),
    # Global search
    path('search/', global_search, name='global-search'),
    # CSV exports
    path('export/tasks/', export_tasks_csv, name='export-tasks-csv'),
    path('export/submissions/', export_submissions_csv, name='export-submissions-csv'),
    path('export/performance/', export_performance_report_csv, name='export-performance-csv'),
    # Analytics pages
    path('performance/', worker_performance, name='worker-performance'),
    path('analytics/', manager_analytics, name='manager-analytics'),
    # Avatar upload
    path('profile/avatar/', profile_avatar_upload, name='profile-avatar-upload'),
    # Kanban board
    path('tasks/kanban/', task_kanban, name='task-kanban'),
    path('tasks/<int:task_id>/kanban-move/', task_kanban_move, name='task-kanban-move'),
    # Calendar view
    path('tasks/calendar/', task_calendar, name='task-calendar'),
    # Dark mode
    path('set-dark-mode/', set_dark_mode, name='set-dark-mode'),
    # Bulk task actions
    path('tasks/bulk-action/', task_bulk_action, name='task-bulk-action'),
    # Submission versions
    path('tasks/<int:task_id>/submission-versions/', submission_versions, name='submission-versions'),
    path('management/version-archive/', version_data_archive, name='version-data-archive'),
    # Offline Map Hub
    path('management/offline-maps/', offline_map_manager, name='offline-map-manager'),
    path('map-tiles/<str:layer_type>/<int:z>/<int:x>/<int:y>.png', map_tile_proxy, name='map-tile-proxy'),
    
    # Global Map Dashboard
    path('global-map/', global_map, name='global-map'),
    
    # System & Database Reset Engine (Super Admin Quick Tool)
    path('management/reset-database/', reset_database_ajax, name='reset-database-ajax'),

    # Task API (Rest Framework)
    path('api/tasks/', include('tasks.urls')),
    path('api/users/', include('users.urls')),
    path('email-manager/', include('notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    from django.views.static import serve
    urlpatterns += [
        re_path(r'^(?:.*/)?media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
        re_path(r'^(?:.*/)?static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    ]

# Error handlers
handler404 = handler_404
handler500 = handler_500