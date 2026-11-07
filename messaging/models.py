from django.db import models
from django.conf import settings

class Conversation(models.Model):
    """Model representing a chat session (1-on-1 or group)."""
    name = models.CharField(max_length=255, blank=True, help_text="Required for group chats")
    is_group = models.BooleanField(default=False)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        if self.is_group:
            return f"Group: {self.name or 'Unnamed group'}"
        return f"Private Conversation {self.id}"

class ConversationMember(models.Model):
    """Model linking users to conversations."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations')
    is_admin = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_timestamp = models.DateTimeField(auto_now_add=True)
    last_typing_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('conversation', 'user')

    def __str__(self):
        return f"{self.user} in {self.conversation}"

class Message(models.Model):
    """Model to store chat messages."""
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    # Moving towards conversation-based messaging
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages',
        null=True, # Allow null for transition
        blank=True
    )
    # Temporarily keeping recipient for data migration/compatibility
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='received_messages',
        null=True,
        blank=True
    )
    content = models.TextField()
    attachment = models.FileField(upload_to='chat_attachments/', null=True, blank=True)
    is_read = models.BooleanField(default=False)
    
    # Phase 2 Enhancements
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    reply_to = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='replies'
    )
    archived_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='archived_messages'
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"Msg {self.id} from {self.sender} at {self.timestamp}"

    def save(self, *args, **kwargs):
        if not self.conversation_id and self.recipient_id:
            # Find or create 1-on-1 conversation
            conversation = Conversation.objects.filter(
                is_group=False,
                members__user=self.sender
            ).filter(
                members__user=self.recipient
            ).first()
            if not conversation:
                conversation = Conversation.objects.create(is_group=False)
                ConversationMember.objects.create(conversation=conversation, user=self.sender)
                ConversationMember.objects.create(conversation=conversation, user=self.recipient)
                # last_read_timestamp is auto_now_add; on coarse clocks (Windows ~15 ms)
                # the opening message can share that instant and count as already read.
                from django.utils import timezone as _tz
                conversation.members.update(last_read_timestamp=_tz.now() - _tz.timedelta(seconds=1))
            self.conversation = conversation
        super().save(*args, **kwargs)


class MessageReaction(models.Model):
    """Model to store emoji reactions to messages."""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10) # Enough for most Unicode emojis
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('message', 'user', 'emoji') # A user can react with a specific emoji only once per message
        
    def __str__(self):
        return f"{self.user} reacted {self.emoji} on Message {self.message.id}"


class Poll(models.Model):
    """Model for polls in group chats."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='polls')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_closed = models.BooleanField(default=False)

    def __str__(self):
        return f"Poll: {self.question}"

class PollOption(models.Model):
    """Model for poll options."""
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.poll.question} - {self.text}"

class PollVote(models.Model):
    """Model to track user votes on polls."""
    poll_option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('poll_option', 'user') # User can vote once per option (or we can restrict to once per poll in logic)

    def __str__(self):
        return f"{self.user} voted for {self.poll_option.text}"


class ChatPermission(models.Model):
    """Model to manage which users a specific user can chat with."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_permissions'
    )
    allowed_contacts = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='allowed_in_chats'
    )
    
    class Meta:
        verbose_name = "Chat Permission"
        verbose_name_plural = "Chat Permissions"

    def __str__(self):
        return f"Chat permissions for {self.user.email}"
