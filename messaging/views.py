from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Count
from .models import Message, ChatPermission, Conversation, ConversationMember, MessageReaction, Poll, PollOption, PollVote
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()

def is_admin(user):
    return user.is_authenticated and user.role == 'super_admin'

@login_required
@user_passes_test(is_admin)
def messaging_config(request):
    """Admin view to manage user chat permissions."""
    from django.db.models import Count
    users = User.objects.all().exclude(id=request.user.id).annotate(
        msg_count=Count('sent_messages', distinct=True),
        allowed_count=Count('chat_permissions__allowed_contacts', distinct=True)
    ).order_by('email')
    
    # Pre-fetch permissions for the grid view
    permissions = ChatPermission.objects.all().select_related('user').prefetch_related('allowed_contacts')
    perm_map = {p.user_id: p for p in permissions}

    # Calculate statistics
    now = timezone.now()
    five_mins_ago = now - timezone.timedelta(minutes=5)
    total_users = User.objects.count()
    active_users = User.objects.filter(last_activity__gt=five_mins_ago).count()
    total_messages = Message.objects.count()
    
    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'total_messages': total_messages,
    }
    
    context = {
        'users': users,
        'perm_map': perm_map,
        'stats': stats,
    }
    return render(request, 'messaging/config.html', context)

@login_required
@user_passes_test(is_admin)
def user_message_log(request, user_id):
    """Admin view to audit a specific user's messaging history — mimic-messenger mode."""
    inspected_user = get_object_or_404(User, id=user_id)

    # All conversations this user is a member of
    active_conv_ids = ConversationMember.objects.filter(user=inspected_user).values_list('conversation_id', flat=True)
    conversations = Conversation.objects.filter(id__in=active_conv_ids).prefetch_related(
        'members', 'messages__sender', 'members__user__profile'
    ).annotate(msg_count=Count('messages')).order_by('-updated_at')

    # Total messages sent by this user
    total_sent = Message.objects.filter(sender=inspected_user).count()

    # Activity stats for timeline
    from django.db.models.functions import TruncDate
    daily_activity = (
        Message.objects
        .filter(sender=inspected_user)
        .annotate(day=TruncDate('timestamp'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    first_msg = Message.objects.filter(sender=inspected_user).order_by('timestamp').first()
    last_msg  = Message.objects.filter(sender=inspected_user).order_by('-timestamp').first()

    deleted_count = Message.objects.filter(sender=inspected_user, is_deleted=True).count()
    total_recv    = Message.objects.filter(
        conversation__in=active_conv_ids
    ).exclude(sender=inspected_user).count()

    # Get the users that the inspected user is allowed to chat with
    try:
        perm = inspected_user.chat_permission
        allowed_contacts = perm.allowed_contacts.all()
    except Exception:
        allowed_contacts = User.objects.none()

    context = {
        'inspected_user': inspected_user,
        'conversations': conversations,
        'total_sent': total_sent,
        'allowed_contacts': allowed_contacts,
        'daily_activity': list(daily_activity),
        'first_active': first_msg.timestamp.strftime('%b %d, %Y') if first_msg else '—',
        'last_active': last_msg.timestamp.strftime('%b %d, %Y %H:%M') if last_msg else '—',
        'deleted_count': deleted_count,
        'total_recv': total_recv,
        'conv_count': conversations.count(),
    }
    return render(request, 'messaging/inspect_user.html', context)


@login_required
@user_passes_test(is_admin)
def admin_user_activity(request, user_id):
    """Admin AJAX: return daily message activity stats for a user."""
    from django.db.models.functions import TruncDate
    user = get_object_or_404(User, id=user_id)
    days = (
        Message.objects.filter(sender=user)
        .annotate(day=TruncDate('timestamp'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    return JsonResponse({'days': [{'date': str(d['day']), 'count': d['count']} for d in days]})


@login_required
@user_passes_test(is_admin)
def admin_inspect_search(request, user_id):
    """Admin AJAX: full-text search across ALL conversations of a user."""
    q = request.GET.get('q', '').strip()
    if not q or len(q) < 2:
        return JsonResponse({'results': []})

    user = get_object_or_404(User, id=user_id)
    conv_ids = ConversationMember.objects.filter(user=user).values_list('conversation_id', flat=True)

    messages = (
        Message.objects
        .filter(conversation_id__in=conv_ids, content__icontains=q, is_deleted=False)
        .select_related('sender', 'conversation')
        .order_by('-timestamp')[:50]
    )

    results = []
    for msg in messages:
        # Determine conv display name
        members = list(msg.conversation.members.select_related('user').all())
        if msg.conversation.is_group:
            conv_name = msg.conversation.name or 'Group Chat'
        else:
            partner = next((m.user for m in members if m.user_id != user.id), None)
            conv_name = partner.get_full_name() if partner else 'Direct'

        results.append({
            'msg_id': msg.id,
            'conv_id': msg.conversation_id,
            'conv_name': conv_name,
            'sender_name': msg.sender.get_full_name() or msg.sender.email,
            'sender_id': msg.sender.id,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%b %d, %Y %H:%M'),
        })

    return JsonResponse({'results': results, 'query': q})




@login_required
@user_passes_test(is_admin)
def admin_inspect_conversation(request, conv_id):
    """Admin AJAX endpoint: return a conversation's messages as JSON (ghost mode)."""
    conv = get_object_or_404(Conversation, id=conv_id)
    messages_qs = conv.messages.select_related('sender', 'sender__profile').order_by('timestamp')

    messages_data = []
    for msg in messages_qs:
        avatar_url = None
        try:
            if msg.sender.profile and msg.sender.profile.avatar:
                avatar_url = msg.sender.profile.avatar.url
        except Exception:
            pass

        attachment_url = None
        attachment_name = None
        if msg.attachment:
            attachment_url = msg.attachment.url
            attachment_name = msg.attachment.name.split('/')[-1]

        messages_data.append({
            'id': msg.id,
            'sender_id': msg.sender.id,
            'sender_name': msg.sender.get_full_name() or msg.sender.email,
            'sender_avatar': avatar_url,
            'content': msg.content or '',
            'timestamp': msg.timestamp.strftime('%b %d, %Y %H:%M'),
            'timestamp_full': msg.timestamp.isoformat(),
            'is_deleted': msg.is_deleted,
            'is_edited': msg.is_edited,
            'attachment_url': attachment_url,
            'attachment_name': attachment_name,
        })

    # Conversation name/partner info
    members = list(conv.members.select_related('user', 'user__profile').all())
    members_data = [{
        'id': m.user.id,
        'name': m.user.get_full_name() or m.user.email,
        'avatar': m.user.profile.avatar.url if (hasattr(m.user, 'profile') and m.user.profile and m.user.profile.avatar) else None,
    } for m in members]

    return JsonResponse({
        'conv_id': conv.id,
        'conv_name': conv.name if conv.is_group else '',
        'is_group': conv.is_group,
        'members': members_data,
        'messages': messages_data,
    })


@login_required
@user_passes_test(is_admin)
def update_chat_permission(request):
    """AJAX view to update chat permissions."""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        allowed_ids = request.POST.getlist('allowed_contacts')
        
        user = get_object_or_404(User, id=user_id)
        perm, created = ChatPermission.objects.get_or_create(user=user)
        
        perm.allowed_contacts.set(allowed_ids)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def get_contacts(request):
    """API to get contacts for the current user."""
    # 1. Start with allowed contacts from permissions
    try:
        permission = ChatPermission.objects.get(user=request.user)
        contacts_set = set(permission.allowed_contacts.all())
    except ChatPermission.DoesNotExist:
        contacts_set = set()
    
    # 2. If super_admin, they see everyone by default
    if request.user.role == 'super_admin':
        all_users = User.objects.exclude(id=request.user.id)
        contacts_set.update(all_users)
    else:
        # 3. For regular users, also include anyone they have a message history with
        recent_senders = Message.objects.filter(recipient=request.user).values_list('sender_id', flat=True)
        recent_recipients = Message.objects.filter(sender=request.user).values_list('recipient_id', flat=True)
        recent_ids = set(recent_senders) | set(recent_recipients)
        if recent_ids:
            recent_users = User.objects.filter(id__in=recent_ids)
            contacts_set.update(recent_users)

    # Convert to list and sort by name
    contacts = sorted(list(contacts_set), key=lambda x: x.get_full_name() or x.email)
    
    # Calculate online status (within 5 mins)
    now = timezone.now()
    five_mins_ago = now - timezone.timedelta(minutes=5)
    
    data = []
    for c in contacts:
        avatar_url = None
        if hasattr(c, 'profile') and c.profile.avatar:
            avatar_url = c.profile.avatar.url
            
        data.append({
            'id': c.id,
            'full_name': c.get_full_name() or c.email,
            'email': c.email,
            'role': c.get_role_display(),
            'initial': c.first_name[0].upper() if c.first_name else c.email[0].upper(),
            'is_online': c.last_activity and c.last_activity > five_mins_ago,
            'avatar_url': avatar_url
        })
    
    return JsonResponse({'contacts': data})

@login_required
def get_conversation_messages(request, conv_id):
    """API to fetch messages for a specific conversation ID."""
    conversation = get_object_or_404(Conversation, id=conv_id, members__user=request.user)
    
    # Activity Log
    User.objects.filter(id=request.user.id).update(last_activity=timezone.now())
    
    # Pagination
    offset = int(request.GET.get('offset', 0))
    limit = 20
    
    messages_query = conversation.messages.exclude(archived_by=request.user).order_by('-timestamp')
    
    total_messages = messages_query.count()
    has_more = (offset + limit) < total_messages
    
    messages = reversed(messages_query[offset:offset+limit])
    
    # Mark messages as read
    ConversationMember.objects.filter(conversation=conversation, user=request.user).update(last_read_timestamp=timezone.now())
    Message.objects.filter(conversation=conversation, recipient=request.user, is_read=False).update(is_read=True)
    
    data = []
    for m in messages:
        avatar_url = None
        if hasattr(m.sender, 'profile') and m.sender.profile.avatar:
            avatar_url = m.sender.profile.avatar.url
            
        msg_data = {
            'id': m.id,
            'sender_id': m.sender.id,
            'sender_name': m.sender.get_full_name() or m.sender.email,
            'sender_avatar': avatar_url,
            'recipient_id': m.recipient.id if m.recipient else None,
            'content': m.content,
            'timestamp': m.timestamp.strftime('%H:%M %b %d'),
            'attachment_url': m.attachment.url if m.attachment else None,
            'is_image': False,
            'is_edited': m.is_edited,
            'is_deleted': m.is_deleted,
            'is_pinned': m.is_pinned,
            'reply_to_id': m.reply_to.id if m.reply_to else None,
            'reactions': list(m.reactions.values('emoji', 'user__first_name', 'user__email', 'user_id'))
        }
        
        if m.is_deleted:
            msg_data['content'] = "This message was deleted."
            msg_data['attachment_url'] = None
            msg_data['is_image'] = False
        else:
            if m.attachment:
                ext = m.attachment.name.lower().split('.')[-1]
                if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    msg_data['is_image'] = True
                elif ext in ['webm', 'mp3', 'wav', 'ogg', 'm4a']:
                    msg_data['is_voice'] = True
                
        data.append(msg_data)
        
    return JsonResponse({
        'messages': data,
        'has_more': has_more,
        'total': total_messages,
        'conversation_id': conversation.id
    })

@login_required
def get_messages(request, user_id):
    """API to fetch messages by conversation_id or recipient_id."""
    # check if user_id is a conversation_id or a recipient_id
    # For now, we assume user_id is a RECIPIENT_ID (backwards compatibility)
    # but we will eventually transition to passing conversation IDs.
    
    recipient = get_object_or_404(User, id=user_id)
    
    # Activity Log
    User.objects.filter(id=request.user.id).update(last_activity=timezone.now())
    
    # Find conversation between these two
    conversation = Conversation.objects.filter(
        is_group=False,
        members__user=request.user
    ).filter(
        members__user=recipient
    ).first()
    
    if not conversation:
        conversation = Conversation.objects.create(is_group=False)
        ConversationMember.objects.create(conversation=conversation, user=request.user)
        ConversationMember.objects.create(conversation=conversation, user=recipient)
        return JsonResponse({
            'messages': [],
            'has_more': False,
            'total': 0,
            'conversation_id': conversation.id
        })

    # Pagination
    offset = int(request.GET.get('offset', 0))
    limit = 20
    
    messages_query = conversation.messages.exclude(archived_by=request.user).order_by('-timestamp')
    
    total_messages = messages_query.count()
    has_more = (offset + limit) < total_messages
    
    messages = reversed(messages_query[offset:offset+limit])
    
    # Mark messages as read in this conversation for current user
    # Actually, we should update ConversationMember.last_read_timestamp
    ConversationMember.objects.filter(conversation=conversation, user=request.user).update(last_read_timestamp=timezone.now())
    Message.objects.filter(conversation=conversation, recipient=request.user, is_read=False).update(is_read=True)
    
    data = []
    for m in messages:
        avatar_url = None
        if hasattr(m.sender, 'profile') and m.sender.profile.avatar:
            avatar_url = m.sender.profile.avatar.url
            
        msg_data = {
            'id': m.id,
            'sender_id': m.sender.id,
            'sender_name': m.sender.get_full_name() or m.sender.email,
            'sender_avatar': avatar_url,
            'recipient_id': m.recipient.id if m.recipient else None,
            'content': m.content,
            'timestamp': m.timestamp.strftime('%H:%M %b %d'),
            'attachment_url': m.attachment.url if m.attachment else None,
            'is_image': False,
            'is_edited': m.is_edited,
            'is_deleted': m.is_deleted,
            'reply_to_id': m.reply_to.id if m.reply_to else None,
            'reactions': list(m.reactions.values('emoji', 'user__first_name', 'user__email', 'user_id'))
        }
        
        # If deleted, hide the content and attachment
        if m.is_deleted:
            msg_data['content'] = "This message was deleted."
            msg_data['attachment_url'] = None
            msg_data['is_image'] = False
        else:
            if m.attachment:
                ext = m.attachment.name.lower().split('.')[-1]
                if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    msg_data['is_image'] = True
                elif ext in ['webm', 'mp3', 'wav', 'ogg', 'm4a']:
                    msg_data['is_voice'] = True
                
        data.append(msg_data)
        
    return JsonResponse({
        'messages': data,
        'has_more': has_more,
        'total': total_messages,
        'conversation_id': conversation.id
    })

@login_required
def send_message(request):
    """API to send a message."""
    if request.method == 'POST':
        try:
            # Robust data extraction (supports JSON and Form/Multipart)
            data = {}
            if request.POST:
                data = request.POST
            elif request.content_type == 'application/json':
                try:
                    data = json.loads(request.body)
                except Exception:
                    data = {}
            else:
                # Fallback to POST as it might have been read by CSRF/Middleware
                data = request.POST

            recipient_id = data.get('recipient_id')
            conversation_id = data.get('conversation_id')
            content = data.get('content', '')
            attachment = request.FILES.get('attachment')
            reply_to_id = data.get('reply_to_id')
            
            if not content and not attachment:
                return JsonResponse({'status': 'error', 'message': 'Empty message'}, status=400)
                
            conversation = None
            recipient = None
            
            if conversation_id:
                conversation = get_object_or_404(Conversation, id=conversation_id, members__user=request.user)
            elif recipient_id:
                recipient = get_object_or_404(User, id=recipient_id)
                # Find or create 1-on-1 conversation
                conversation = Conversation.objects.filter(
                    is_group=False,
                    members__user=request.user
                ).filter(
                    members__user=recipient
                ).first()
                
                if not conversation:
                    conversation = Conversation.objects.create(is_group=False)
                    ConversationMember.objects.create(conversation=conversation, user=request.user)
                    ConversationMember.objects.create(conversation=conversation, user=recipient)
            
            if not conversation:
                return JsonResponse({'status': 'error', 'message': 'No conversation specified'}, status=400)

            message = Message.objects.create(
                sender=request.user,
                recipient=recipient, # keep for compatibility / direct targeting
                conversation=conversation,
                content=content,
                attachment=attachment
            )
            
            # Update conversation updated_at
            conversation.save() # triggers auto_now=True
            
            if reply_to_id:
                try:
                    reply_msg = Message.objects.get(id=reply_to_id)
                    message.reply_to = reply_msg
                    message.save()
                except Message.DoesNotExist:
                    pass
            
            # Activity Log
            User.objects.filter(id=request.user.id).update(last_activity=timezone.now())
            
            avatar_url = None
            if hasattr(message.sender, 'profile') and message.sender.profile.avatar:
                avatar_url = message.sender.profile.avatar.url

            return JsonResponse({
                'status': 'success',
                'message': {
                    'content': message.content,
                    'timestamp': message.timestamp.strftime('%H:%M %b %d'),
                    'sender_id': message.sender.id,
                    'sender_name': message.sender.get_full_name() or message.sender.email,
                    'sender_avatar': avatar_url,
                    'attachment_url': message.attachment.url if message.attachment else None,
                    'conversation_id': conversation.id
                }
            })
        except PermissionDenied as e:
            return JsonResponse({'status': 'error', 'error': str(e), 'message': str(e), 'security_guard_enforced': True}, status=403)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def delete_message(request, message_id):
    """API to mark a message as deleted."""
    if request.method == 'POST':
        message = get_object_or_404(Message, id=message_id, sender=request.user)
        message.is_deleted = True
        message.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def edit_message(request, message_id):
    """API to edit a message content."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_content = data.get('content', '').strip()
            if not new_content:
                return JsonResponse({'status': 'error', 'message': 'Empty content'}, status=400)
                
            message = get_object_or_404(Message, id=message_id, sender=request.user)
            if message.is_deleted:
                return JsonResponse({'status': 'error', 'message': 'Cannot edit deleted message'}, status=400)
                
            message.content = new_content
            message.is_edited = True
            message.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def react_message(request, message_id):
    """API to add or remove a reaction to a message."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            emoji = data.get('emoji')
            if not emoji:
                return JsonResponse({'status': 'error', 'message': 'Emoji is required'}, status=400)
                
            message = get_object_or_404(Message, id=message_id)
            
            # Check if user can actually see this message (is a member of the conversation)
            if message.conversation:
                if not ConversationMember.objects.filter(conversation=message.conversation, user=request.user).exists():
                    return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
            elif request.user != message.sender and request.user != message.recipient:
                return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
                
            # Toggle reaction
            existing = MessageReaction.objects.filter(message=message, user=request.user, emoji=emoji).first()
            if existing:
                existing.delete()
                action = 'removed'
            else:
                MessageReaction.objects.create(message=message, user=request.user, emoji=emoji)
                action = 'added'
                
            return JsonResponse({'status': 'success', 'action': action})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def messenger_page(request):
    """Main dedicated messenger page."""
    return render(request, 'messaging/messenger_page.html')

@login_required
def search_users(request):
    """API to search for any user in the system."""
    query = request.GET.get('q', '').strip()
    if len(query) < 1:
        return JsonResponse({'users': []})
    
    # Search by name, username, or email with multi-word support
    q_filter = Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query)
    if hasattr(User, 'username'):
        q_filter |= Q(username__icontains=query)
    
    parts = query.split()
    if len(parts) > 1:
        part_filter = Q()
        for p in parts:
            part_filter &= (Q(first_name__icontains=p) | Q(last_name__icontains=p) | Q(email__icontains=p))
        q_filter |= part_filter

    users = User.objects.filter(q_filter).exclude(id=request.user.id)[:15]
    
    # Activity Log
    User.objects.filter(id=request.user.id).update(last_activity=timezone.now())
    
    now = timezone.now()
    five_mins_ago = now - timezone.timedelta(minutes=5)
    
    data = []
    for u in users:
        avatar_url = None
        if hasattr(u, 'profile') and u.profile.avatar:
            avatar_url = u.profile.avatar.url
            
        data.append({
            'id': u.id,
            'full_name': u.get_full_name() or u.email,
            'email': u.email,
            'role': u.get_role_display(),
            'initial': u.first_name[0].upper() if u.first_name else u.email[0].upper(),
            'is_online': u.last_activity and u.last_activity > five_mins_ago,
            'avatar_url': avatar_url
        })
    
    return JsonResponse({'users': data})

@login_required
def get_unread_count(request):
    """API to get total unread messages count for current user across all conversations."""
    # Activity Log
    User.objects.filter(id=request.user.id).update(last_activity=timezone.now())
    
    total_unread = 0
    memberships = ConversationMember.objects.filter(user=request.user, is_archived=False)
    for m in memberships:
        unread = m.conversation.messages.filter(timestamp__gt=m.last_read_timestamp).exclude(sender=request.user).count()
        total_unread += unread
        
    return JsonResponse({'unread_count': total_unread})

@login_required
def get_conversations(request):
    """API to get list of conversations for the current user."""
    show_archived = request.GET.get('archived', 'false').lower() == 'true'
    memberships = ConversationMember.objects.filter(user=request.user, is_archived=show_archived).select_related('conversation').order_by('-conversation__updated_at')
    
    data = []
    now = timezone.now()
    five_mins_ago = now - timezone.timedelta(minutes=5)

    for membership in memberships:
        conv = membership.conversation
        last_msg = conv.messages.last()
        
        # Calculate unread count based on last_read_timestamp
        unread_count = conv.messages.filter(timestamp__gt=membership.last_read_timestamp).exclude(sender=request.user).count()
        
        last_msg_text = "No messages yet"
        if last_msg:
            # If the last message contains HTML (e.g. shared widget), keep it simple for the preview
            if '<div' in last_msg.content and 'class=' in last_msg.content:
                if 'Task:' in last_msg.content or 'task' in last_msg.content.lower():
                    last_msg_text = "Shared a task"
                elif 'Module:' in last_msg.content or 'module' in last_msg.content.lower():
                    last_msg_text = "Shared a module"
                else:
                    last_msg_text = "Shared an item"
            else:
                last_msg_text = last_msg.content

        conv_data = {
            'id': conv.id,
            'name': conv.name,
            'is_group': conv.is_group,
            'updated_at': conv.updated_at.strftime('%H:%M %b %d'),
            'last_message': last_msg_text,
            'unread_count': unread_count,
            'is_archived': membership.is_archived,
        }
        
        if not conv.is_group:
            # For 1-on-1, get the other member's info
            other_member = conv.members.exclude(user=request.user).first()
            if other_member:
                u = other_member.user
                conv_data['name'] = u.get_full_name() or u.email
                conv_data['initial'] = u.first_name[0].upper() if u.first_name else u.email[0].upper()
                conv_data['is_online'] = u.last_activity and u.last_activity > five_mins_ago
                conv_data['other_user_id'] = u.id
                conv_data['email'] = u.email
                conv_data['role'] = u.profile.role if hasattr(u, 'profile') and hasattr(u.profile, 'role') else 'Team Member'
                conv_data['status'] = u.profile.bio or 'Available' if hasattr(u, 'profile') else 'Available'
                
                # Check for avatar
                if hasattr(u, 'profile') and u.profile.avatar:
                    conv_data['avatar_url'] = u.profile.avatar.url
                else:
                    conv_data['avatar_url'] = None
            else:
                conv_data['initial'] = "?"
                conv_data['avatar_url'] = None
        else:
            conv_data['initial'] = conv.name[0].upper() if conv.name else "G"
            conv_data['avatar_url'] = None
            
        data.append(conv_data)
        
    return JsonResponse({'conversations': data})

@login_required
def create_group_chat(request):
    """API to create a new group conversation."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            member_ids = data.get('member_ids', []) # List of user IDs
            
            if not name:
                return JsonResponse({'status': 'error', 'message': 'Group name is required'}, status=400)
            
            conv = Conversation.objects.create(name=name, is_group=True, creator=request.user)
            
            # Add creator as admin
            ConversationMember.objects.create(conversation=conv, user=request.user, is_admin=True)
            
            # Add other members
            for uid in member_ids:
                try:
                    user = User.objects.get(id=uid)
                    ConversationMember.objects.get_or_create(conversation=conv, user=user)
                except User.DoesNotExist:
                    continue
            
            return JsonResponse({'status': 'success', 'conversation_id': conv.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def add_conversation_member(request, conv_id):
    """API to add a new member to an existing group chat."""
    if request.method == 'POST':
        conv = get_object_or_404(Conversation, id=conv_id, is_group=True)
        # Check if requester is already a member
        if not ConversationMember.objects.filter(conversation=conv, user=request.user).exists():
             return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
             
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            user = get_object_or_404(User, id=user_id)
            
            ConversationMember.objects.get_or_create(conversation=conv, user=user)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def archive_conversation(request, conv_id):
    """API to archive a conversation for the current user."""
    if request.method == 'POST':
        membership = get_object_or_404(ConversationMember, conversation_id=conv_id, user=request.user)
        membership.is_archived = not membership.is_archived
        membership.save()
        return JsonResponse({'status': 'success', 'is_archived': membership.is_archived})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def delete_conversation(request, conv_id):
    """API to delete (remove local access) a conversation for the current user."""
    if request.method == 'POST':
        membership = get_object_or_404(ConversationMember, conversation_id=conv_id, user=request.user)
        # We don't necessarily delete the conversation for everyone, just remove this member
        # (or mark as deleted for them). For simplicity, let's just delete the membership.
        membership.delete()
        
        # If no members left, we could delete the conversation entirely
        conv = Conversation.objects.filter(id=conv_id).first()
        if conv and not conv.members.exists():
            conv.delete()
            
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def search_conversation_messages(request, conv_id):
    """API to search for messages within a specific conversation."""
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'messages': []})
        
    conversation = get_object_or_404(Conversation, id=conv_id, members__user=request.user)
    messages = conversation.messages.filter(content__icontains=query).order_by('-timestamp')[:50]
    
    data = []
    for m in messages:
        data.append({
            'id': m.id,
            'sender_id': m.sender.id,
            'sender_name': m.sender.get_full_name() or m.sender.email,
            'content': m.content,
            'timestamp': m.timestamp.strftime('%H:%M %b %d')
        })
        
    return JsonResponse({'messages': data})

@login_required
@require_POST
def toggle_pin_message(request, message_id):
    """API to pin or unpin a message."""
    message = get_object_or_404(Message, id=message_id)
    # Check if user is a member of the conversation
    if not ConversationMember.objects.filter(conversation=message.conversation, user=request.user).exists():
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
        
    message.is_pinned = not message.is_pinned
    message.save()
    return JsonResponse({'status': 'success', 'is_pinned': message.is_pinned})

@login_required
@require_POST
def update_typing_status(request, conv_id):
    """API to update the typing status for the current user in a conversation."""
    membership = get_object_or_404(ConversationMember, conversation_id=conv_id, user=request.user)
    membership.last_typing_at = timezone.now()
    membership.save(update_fields=['last_typing_at'])
    return JsonResponse({'status': 'success'})

@login_required
def get_typing_indicators(request, conv_id):
    """API to get users who are currently typing in a conversation."""
    # Consider typing if last_typing_at is within the last 5 seconds
    five_seconds_ago = timezone.now() - timezone.timedelta(seconds=5)
    typing_members = ConversationMember.objects.filter(
        conversation_id=conv_id,
        last_typing_at__gte=five_seconds_ago
    ).exclude(user=request.user).select_related('user')
    
    data = [{
        'id': m.user.id,
        'name': m.user.get_full_name() or m.user.email
    } for m in typing_members]
    
    return JsonResponse({'typing_users': data})

@login_required
@require_POST
def create_poll(request, conv_id):
    """API to create a poll in a conversation."""
    conversation = get_object_or_404(Conversation, id=conv_id, members__user=request.user)
    try:
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        options = data.get('options', [])
        
        if not question or not options:
            return JsonResponse({'status': 'error', 'message': 'Question and options are required'}, status=400)
            
        poll = Poll.objects.create(conversation=conversation, creator=request.user, question=question)
        for opt_text in options:
            if opt_text.strip():
                PollOption.objects.create(poll=poll, text=opt_text.strip())
                
        return JsonResponse({'status': 'success', 'poll_id': poll.id})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
def vote_poll(request, option_id):
    """API to vote for a poll option."""
    option = get_object_or_404(PollOption, id=option_id)
    poll = option.poll
    # Check if user is a member of the conversation
    if not ConversationMember.objects.filter(conversation=poll.conversation, user=request.user).exists():
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
        
    if poll.is_closed:
        return JsonResponse({'status': 'error', 'message': 'Poll is closed'}, status=400)
        
    # User can only vote once per poll (business rule choice)
    # Removing any previous votes by this user in this poll
    PollVote.objects.filter(poll_option__poll=poll, user=request.user).delete()
    
    # Create new vote
    PollVote.objects.create(poll_option=option, user=request.user)
    return JsonResponse({'status': 'success'})

@login_required
@require_POST
def close_poll(request, poll_id):
    """API to close a poll. Only the creator can close it."""
    poll = get_object_or_404(Poll, id=poll_id)
    if poll.creator != request.user:
        return JsonResponse({'status': 'error', 'message': 'Only the creator can close this poll.'}, status=403)
        
    poll.is_closed = True
    poll.save()
    return JsonResponse({'status': 'success'})

@login_required
def get_polls(request, conv_id):
    """API to get active polls for a conversation."""
    conversation = get_object_or_404(Conversation, id=conv_id, members__user=request.user)
    polls = Poll.objects.filter(conversation=conversation).order_by('-created_at')[:5]
    
    data = []
    for poll in polls:
        options_data = []
        for opt in poll.options.all():
            options_data.append({
                'id': opt.id,
                'text': opt.text,
                'votes': opt.votes.count(),
                'voted_by_me': opt.votes.filter(user=request.user).exists()
            })
            
        data.append({
            'id': poll.id,
            'question': poll.question,
            'is_closed': poll.is_closed,
            'created_at': poll.created_at.strftime('%H:%M %b %d'),
            'creator_name': poll.creator.get_full_name() or poll.creator.email,
            'creator_id': poll.creator.id,
            'options': options_data
        })
        
    return JsonResponse({'polls': data})

@login_required
def forward_message(request, message_id):
    """API to forward a message to other users."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            recipient_ids = data.get('recipient_ids', [])
            if not recipient_ids:
                return JsonResponse({'status': 'error', 'message': 'No recipients selected'}, status=400)
            
            original_message = get_object_or_404(Message, id=message_id)
            
            # Check permission: User must be a member of the conversation, or be sender/recipient
            if original_message.conversation:
                if not ConversationMember.objects.filter(conversation=original_message.conversation, user=request.user).exists():
                    return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
            elif request.user != original_message.sender and request.user != original_message.recipient:
                return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
            
            if original_message.is_deleted:
                return JsonResponse({'status': 'error', 'message': 'Cannot forward a deleted message'}, status=400)
            
            forwarded_count = 0
            
            # Support both conversation_ids (new) and recipient_ids (legacy)
            conv_ids = data.get('conversation_ids', [])
            recipient_ids = data.get('recipient_ids', [])
            
            if conv_ids:
                for conv_id in conv_ids:
                    try:
                        conv = Conversation.objects.get(id=conv_id, members__user=request.user)
                        # Get recipient for 1-on-1 chats (for compatibility field)
                        recipient = None
                        if not conv.is_group:
                            other = conv.members.exclude(user=request.user).first()
                            if other:
                                recipient = other.user
                        Message.objects.create(
                            sender=request.user,
                            recipient=recipient,
                            conversation=conv,
                            content=original_message.content,
                            attachment=original_message.attachment
                        )
                        conv.save()
                        forwarded_count += 1
                    except Conversation.DoesNotExist:
                        continue
            else:
                for r_id in recipient_ids:
                    try:
                        recipient = User.objects.get(id=r_id)
                        conv = Conversation.objects.filter(
                            is_group=False,
                            members__user=request.user
                        ).filter(
                            members__user=recipient
                        ).first()
                        
                        if not conv:
                            conv = Conversation.objects.create(is_group=False)
                            ConversationMember.objects.create(conversation=conv, user=request.user)
                            ConversationMember.objects.create(conversation=conv, user=recipient)

                        Message.objects.create(
                            sender=request.user,
                            recipient=recipient,
                            conversation=conv,
                            content=original_message.content,
                            attachment=original_message.attachment
                        )
                        conv.save()
                        forwarded_count += 1
                    except User.DoesNotExist:
                        continue

            
            return JsonResponse({'status': 'success', 'forwarded_count': forwarded_count})
        except PermissionDenied as e:
            return JsonResponse({'status': 'error', 'error': str(e), 'message': str(e), 'security_guard_enforced': True}, status=403)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=400)

@login_required
@require_POST
def bulk_delete_messages(request):
    """API to mark multiple messages as deleted for the current user."""
    try:
        data = json.loads(request.body)
        message_ids = data.get('message_ids', [])
        if not message_ids:
            return JsonResponse({'status': 'error', 'message': 'No messages selected'}, status=400)
        
        # We can only delete messages we sent
        Message.objects.filter(id__in=message_ids, sender=request.user).update(is_deleted=True)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
def bulk_archive_messages(request):
    """API to archive multiple messages for the current user."""
    try:
        data = json.loads(request.body)
        message_ids = data.get('message_ids', [])
        if not message_ids:
            return JsonResponse({'status': 'error', 'message': 'No messages selected'}, status=400)
            
        messages = Message.objects.filter(id__in=message_ids)
        # Assuming we only archive if we're part of the conversation or sender/recipient
        for msg in messages:
            if msg.conversation:
                if ConversationMember.objects.filter(conversation=msg.conversation, user=request.user).exists():
                    msg.archived_by.add(request.user)
            elif request.user == msg.sender or request.user == msg.recipient:
                msg.archived_by.add(request.user)
                
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

import csv
from django.http import HttpResponse
from django.utils.html import strip_tags
from bs4 import BeautifulSoup

@login_required
def bulk_export_messages(request):
    """API to export selected messages as an Excel (XLSX) or CSV file."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message_ids = data.get('message_ids', [])
            if not message_ids:
                return JsonResponse({'status': 'error', 'message': 'No messages selected'}, status=400)
            
            messages = Message.objects.filter(id__in=message_ids).order_by('timestamp')
            
            try:
                import openpyxl
                has_openpyxl = True
            except ImportError:
                has_openpyxl = False

            if has_openpyxl:
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "Chat Export"
                
                # Header row
                headers = ['Timestamp', 'Sender', 'Content']
                ws.append(headers)
                
                # Formatting for header
                for cell in ws[1]:
                    cell.font = openpyxl.styles.Font(bold=True)
            else:
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="chat_export.csv"'
                writer = csv.writer(response)
                writer.writerow(['Timestamp', 'Sender', 'Content'])
            
            for msg in messages:
                # verify permission to export
                has_perm = False
                if msg.conversation:
                    if ConversationMember.objects.filter(conversation=msg.conversation, user=request.user).exists():
                        has_perm = True
                elif request.user == msg.sender or request.user == msg.recipient:
                    has_perm = True
                    
                if has_perm and not msg.is_deleted:
                    # Clean up HTML so widget info is readable
                    soup = BeautifulSoup(msg.content, 'html.parser')
                    
                    # Optional: remove icons/unwanted text
                    for icon in soup.find_all('i'):
                        icon.decompose()
                        
                    # Extract text with smart separators
                    clean_content = soup.get_text(separator=' | ', strip=True)
                    # Clean up some common widget artifacts
                    clean_content = clean_content.replace('Command Center | ', '')
                    clean_content = clean_content.replace(' | Open Module', '')
                    clean_content = clean_content.replace(' | Open Task', '')
                    clean_content = clean_content.replace(' | | ', ' | ')
                    
                    ws.append([
                        msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        msg.sender.get_full_name() or msg.sender.email,
                        clean_content
                    ])
                    
            # Auto-adjust column widths
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = min(max_length + 2, 80) # Cap at 80 characters wide
                ws.column_dimensions[column].width = adjusted_width
                
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="messages_export.xlsx"'
            wb.save(response)
            return response
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=400)
