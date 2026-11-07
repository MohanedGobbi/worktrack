from django.urls import path
from core.features import feature_required
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.messenger_page, name='index'),
    path('config/', feature_required('messenger_admin')(views.messaging_config), name='config'),
    path('update-permission/', views.update_chat_permission, name='update-permission'),
    path('inspect/<int:user_id>/', feature_required('messenger_admin')(views.user_message_log), name='user-message-log'),
    path('inspect/conv/<int:conv_id>/messages/', feature_required('messenger_admin')(views.admin_inspect_conversation), name='admin-inspect-conv'),
    path('inspect/<int:user_id>/activity/', feature_required('messenger_admin')(views.admin_user_activity), name='admin-user-activity'),
    path('inspect/<int:user_id>/search/', feature_required('messenger_admin')(views.admin_inspect_search), name='admin-inspect-search'),


    path('api/contacts/', views.get_contacts, name='api-get-contacts'),
    path('api/search-users/', views.search_users, name='api-search-users'),
    path('api/messages/<int:user_id>/', views.get_messages, name='api-get-messages'),
    path('api/messages/conv/<int:conv_id>/', views.get_conversation_messages, name='api-get-conv-messages'),
    path('api/send/', views.send_message, name='api-send-message'),
    path('api/unread-count/', views.get_unread_count, name='api-unread-count'),
    path('api/delete/<int:message_id>/', views.delete_message, name='api-delete-message'),
    path('api/edit/<int:message_id>/', views.edit_message, name='api-edit-message'),
    path('api/react/<int:message_id>/', views.react_message, name='api-react-message'),
    path('api/forward/<int:message_id>/', views.forward_message, name='api-forward-message'),
    path('api/conversations/', views.get_conversations, name='api-get-conversations'),
    path('api/conversations/create-group/', views.create_group_chat, name='api-create-group'),
    path('api/conversations/<int:conv_id>/add-member/', views.add_conversation_member, name='api-add-member'),
    path('api/conversations/archive/<int:conv_id>/', views.archive_conversation, name='api-archive-conversation'),
    path('api/conversations/delete/<int:conv_id>/', views.delete_conversation, name='api-delete-conversation'),
    path('api/conversations/search/<int:conv_id>/', views.search_conversation_messages, name='api-search-conversation'),
    path('api/conversations/typing-update/<int:conv_id>/', views.update_typing_status, name='api-typing-update'),
    path('api/conversations/typing-list/<int:conv_id>/', views.get_typing_indicators, name='api-typing-list'),
    path('api/messages/pin/<int:message_id>/', views.toggle_pin_message, name='api-pin-message'),
    path('api/conversations/polls/<int:conv_id>/', views.get_polls, name='api-get-polls'),
    path('api/conversations/polls/create/<int:conv_id>/', views.create_poll, name='api-create-poll'),
    path('api/conversations/polls/vote/<int:option_id>/', views.vote_poll, name='api-vote-poll'),
    
    # Bulk actions
    path('api/messages/bulk-delete/', views.bulk_delete_messages, name='api-bulk-delete-messages'),
    path('api/messages/bulk-archive/', views.bulk_archive_messages, name='api-bulk-archive-messages'),
    path('api/messages/bulk-export/', views.bulk_export_messages, name='api-bulk-export-messages'),
    
    path('api/conversations/polls/<int:poll_id>/close/', views.close_poll, name='api-close-poll'),
]
