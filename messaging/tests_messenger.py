from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from messaging.models import Message

User = get_user_model()

class MessengerAPITest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(email='user1@test.com', password='pass', username='user1')
        self.user2 = User.objects.create_user(email='user2@test.com', password='pass', username='user2')
        self.client = Client()
        self.client.force_login(self.user1)

    def test_get_unread_count(self):
        # Create unread messages
        Message.objects.create(sender=self.user2, recipient=self.user1, content="Hello 1")
        Message.objects.create(sender=self.user2, recipient=self.user1, content="Hello 2")
        
        # Another message for someone else
        user3 = User.objects.create_user(email='user3@test.com', password='pass', username='user3')
        Message.objects.create(sender=self.user2, recipient=user3, content="Hello 3")

        response = self.client.get(reverse('messaging:api-unread-count'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['unread_count'], 2)

    def test_mark_as_read_on_fetch(self):
        Message.objects.create(sender=self.user2, recipient=self.user1, content="Unread")
        
        # Count before
        self.assertEqual(Message.objects.filter(recipient=self.user1, is_read=False).count(), 1)
        
        # Fetch messages
        response = self.client.get(reverse('messaging:api-get-messages', args=[self.user2.id]))
        self.assertEqual(response.status_code, 200)
        
        # Count after
        self.assertEqual(Message.objects.filter(recipient=self.user1, is_read=False).count(), 0)

    def test_search_users(self):
        response = self.client.get(reverse('messaging:api-search-users'), {'q': 'user2'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['users']), 1)
        self.assertEqual(data['users'][0]['email'], 'user2@test.com')
    def test_admin_gets_all_contacts(self):
        admin = User.objects.create_superuser(email='admin@test.com', password='pass', username='admin')
        admin.role = 'super_admin'
        admin.save()
        self.client.force_login(admin)
        
        response = self.client.get(reverse('messaging:api-get-contacts'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Should see user1 and user2 (from setUp)
        self.assertEqual(len(data['contacts']), 2)

    def test_messenger_page_load(self):
        response = self.client.get(reverse('messaging:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'messaging/messenger_page.html')
