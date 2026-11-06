from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from notifications.models import Notification, NotificationPreference, EmailTemplate, EmailStyle
from notifications.serializers import NotificationSerializer, NotificationPreferenceSerializer

def admin_required(user):
    return user.is_active and user.role == 'super_admin'

@user_passes_test(admin_required)
def email_template_list(request):
    """List all email templates."""
    templates = EmailTemplate.objects.all()
    # Ensure all notification types have a template
    for n_type, n_label in Notification.NOTIFICATION_TYPES:
        EmailTemplate.objects.get_or_create(
            notification_type=n_type,
            defaults={
                'subject': f'[WorkTrack Pro] Notification: {n_label}',
                'body': f'Hello {{recipient_name}},\n\nYou have a new notification of type {n_label}.',
            }
        )
    
    style = EmailStyle.objects.first()
    if not style:
        style = EmailStyle.objects.create()

    return render(request, 'notifications/email_list.html', {
        'templates': templates,
        'style': style
    })

@user_passes_test(admin_required)
def email_template_edit(request, template_id):
    """Edit a specific email template."""
    template = get_object_or_404(EmailTemplate, id=template_id)
    if request.method == 'POST':
        template.subject = request.POST.get('subject')
        template.body = request.POST.get('body')
        template.save()
        messages.success(request, f'Template for {template.get_notification_type_display()} updated.')
        return redirect('notifications:email-list')
    
    return render(request, 'notifications/email_edit.html', {'template': template})

@user_passes_test(admin_required)
def email_style_edit(request):
    """Edit global email styling."""
    style = EmailStyle.objects.first()
    if not style:
        style = EmailStyle.objects.create()
        
    if request.method == 'POST':
        style.company_name = request.POST.get('company_name')
        style.primary_color = request.POST.get('primary_color')
        style.secondary_color = request.POST.get('secondary_color')
        style.logo_url = request.POST.get('logo_url')
        style.footer_text = request.POST.get('footer_text')
        style.save()
        messages.success(request, 'Global email styling updated.')
        return redirect('notifications:email-list')
    
    preview_template = EmailTemplate.objects.first()
    return render(request, 'notifications/email_style_edit.html', {
        'style': style,
        'preview_template': preview_template
    })


@user_passes_test(admin_required)
def email_preview(request, template_id):
    """Render a live preview of the email template."""
    template_obj = get_object_or_404(EmailTemplate, id=template_id)
    subject = request.POST.get('subject', template_obj.subject)
    body = request.POST.get('body', template_obj.body)
    
    from core.email_notifications import render_premium_email, _get_abs_url
    from tasks.models import Task
    
    # Optional task for realistic data
    task_id = request.GET.get('task_id')
    extra_context = {'subject': subject}
    
    if not task_id:
        # Default to latest task for better preview
        task = Task.objects.order_by('-created_at').first()
    else:
        task = Task.objects.filter(id=task_id).first()

    if task:
        extra_context.update({
            'status': task.get_status_display(),
            'priority': task.get_priority_display(),
            'progress': str(task.progress),
            'cover_image_url': _get_abs_url(task.cover_image.url) if task.cover_image else None
        })
    
    # Render with dummy/task data
    # Allow style overrides for live branding preview
    style_overrides = {
        'company_name': request.POST.get('company_name'),
        'primary_color': request.POST.get('primary_color'),
        'secondary_color': request.POST.get('secondary_color'),
        'logo_url': request.POST.get('logo_url'),
        'footer_text': request.POST.get('footer_text'),
    }
    # Filter out None/empty values to use defaults from DB if not provided in POST
    style_overrides = {k: v for k, v in style_overrides.items() if v is not None}

    subject, html_content = render_premium_email(
        template_obj.notification_type,
        "Sample Notification Title",
        body,
        request.user,
        extra_context=extra_context,
        style_override=style_overrides
    )
    
    return HttpResponse(html_content)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for managing notifications."""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['is_read', 'notification_type']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_read(self, request, pk=None):
        """Mark notification as read."""
        notification = self.get_object()
        if notification.recipient != request.user:
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        return Response(
            NotificationSerializer(notification).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        )
        count = notifications.count()
        notifications.update(is_read=True, read_at=timezone.now())
        
        return Response(
            {"detail": f"Marked {count} notifications as read"},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def unread_count(self, request):
        """Get unread notification count."""
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        
        return Response({"unread_count": count})


class NotificationPreferenceViewSet(viewsets.ViewSet):
    """ViewSet for notification preferences."""
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Get notification preferences."""
        preference = request.user.notification_preference
        serializer = NotificationPreferenceSerializer(preference)
        return Response(serializer.data)
    
    def update(self, request):
        """Update notification preferences."""
        preference = request.user.notification_preference
        serializer = NotificationPreferenceSerializer(
            preference,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
