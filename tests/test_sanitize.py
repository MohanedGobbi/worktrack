from django.contrib.auth import get_user_model
from django.test import TestCase

from core.sanitize import clean_rich, clean_text, script_json
from messaging.models import Message
from tasks.models import Task, TaskComment

User = get_user_model()


class CleanTextTests(TestCase):
    def test_plain_text_kept(self):
        for s in ('Hello', 'مرحبا بكم', 'a < b and 3 > 2', 'x <= y', '', None):
            self.assertEqual(clean_text(s), s)

    def test_tags_removed(self):
        self.assertEqual(clean_text('Hi <img src=x onerror=alert(1)>there'), 'Hi there')
        self.assertEqual(clean_text('<script>alert(1)</script>ok'), 'alert(1)ok')
        self.assertEqual(clean_text('a<!-- c -->b'), 'ab')
        self.assertNotIn('<', clean_text('<<b>script>alert(1)<</b>/script>'))
        # A stray '<' is text, not markup; output escaping keeps it harmless.
        for s in ('if x<y', 'price<USD 5', 'a < b & c'):
            self.assertEqual(clean_text(s), s)


class CleanRichTests(TestCase):
    def test_allowlist(self):
        self.assertEqual(clean_rich('<b>bold</b> <i>x</i><br>'), '<b>bold</b> <i>x</i><br/>')
        out = clean_rich('<a href="/tasks/5/" onclick="x()">t</a>')
        self.assertEqual(out, '<a href="/tasks/5/">t</a>')

    def test_dangerous_removed(self):
        self.assertEqual(clean_rich('<img src=x onerror=alert(1)>hi'), 'hi')
        self.assertEqual(clean_rich('<script>alert(1)</script>hi'), 'hi')
        self.assertEqual(clean_rich('<a href="javascript:alert(1)">x</a>'), 'x')
        self.assertEqual(clean_rich('<b style="x" onmouseover="y">z</b>'), '<b>z</b>')
        self.assertIn('&lt;', clean_rich('<b>1 < 2</b>'))

    def test_nested_containers_do_not_crash(self):
        for s in ('<svg><a href=x>', '<template><b>x</b></template>', '<object><i>a</i></object>',
                  '<noscript><p title="</noscript><img src=x onerror=alert(1)>">', '<math><mtext><b>x</b>'):
            self.assertNotIn('<img', clean_rich(s))

    def test_plain_message_unchanged(self):
        self.assertEqual(clean_rich('a < b & c'), 'a < b & c')


class ScriptJsonTests(TestCase):
    def test_cannot_close_script(self):
        out = script_json({'t': '</script><script>alert(1)</script>'})
        self.assertNotIn('<', out)
        self.assertNotIn('>', out)


class SaveHookTests(TestCase):
    def setUp(self):
        self.a = User.objects.create_user(email='a@t.local', password='x', username='a')
        self.b = User.objects.create_user(email='b@t.local', password='x', username='b')

    def test_message_cleaned_on_save(self):
        m = Message.objects.create(sender=self.a, recipient=self.b, content='<b>hi</b><img src=x onerror=alert(1)>')
        m.refresh_from_db()
        self.assertEqual(m.content, '<b>hi</b>')

    def test_task_and_comment_cleaned(self):
        from datetime import timedelta
        from django.utils import timezone
        t = Task.objects.create(title='<svg onload=alert(1)>Report', description='x<script>y</script>',
                                created_by=self.a, deadline=timezone.now() + timedelta(days=3))
        t.refresh_from_db()
        self.assertEqual(t.title, 'Report')
        self.assertNotIn('<', t.description)
        c = TaskComment.objects.create(task=t, author=self.a, message='ok <iframe src=//x></iframe>')
        c.refresh_from_db()
        self.assertEqual(c.message, 'ok ')

    def test_user_name_cleaned(self):
        self.a.first_name = '<img src=x onerror=alert(1)>Sara'
        self.a.save()
        self.a.refresh_from_db()
        self.assertEqual(self.a.first_name, 'Sara')


class EmailRenderTests(TestCase):
    def test_user_text_is_not_template_code(self):
        from core.email_notifications import render_premium_email
        u = User.objects.create_user(email='c@t.local', password='x', username='c', first_name='Ali')
        subject, html = render_premium_email('task_assigned', '{% debug %}<b>T</b>', 'Line 1\n<script>x</script>', u)
        self.assertIn('{% debug %}', html)  # printed literally, never executed
        self.assertNotIn('<script>x', html)
        self.assertIn('&lt;script&gt;', html)
