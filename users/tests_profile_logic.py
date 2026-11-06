from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class ProfilePreferencesTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='worker@test.com', 
            password='password', 
            role='worker',
            first_name='Test',
            last_name='Worker'
        )
        self.client = Client()
        self.client.login(email='worker@test.com', password='password')

    def test_save_preferences(self):
        url = reverse('profile-preferences')
        data = {
            'email_notifications': 'on',
            'task_notifications': 'on',
            # submission_notifications is omitted (off)
            'theme': 'dark',
            'language': 'fr'
        }
        
        response = self.client.post(url, data)
        
        # Check redirect
        self.assertRedirects(response, reverse('profile'))
        
        # Refresh user from DB
        self.user.refresh_from_db()
        
        # Assertions
        self.assertTrue(self.user.email_notifications)
        self.assertTrue(self.user.task_notifications)
        self.assertFalse(self.user.submission_notifications)
        self.assertEqual(self.user.theme, 'dark')
        self.assertEqual(self.user.language, 'fr')

    def test_save_preferences_all_off(self):
        url = reverse('profile-preferences')
        data = {
            'theme': 'light',
            'language': 'en'
        }
        
        response = self.client.post(url, data)
        self.user.refresh_from_db()
        
        self.assertFalse(self.user.email_notifications)
        self.assertFalse(self.user.task_notifications)
        self.assertFalse(self.user.submission_notifications)
        self.assertEqual(self.user.theme, 'light')
        self.assertEqual(self.user.language, 'en')
