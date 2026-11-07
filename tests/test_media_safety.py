import shutil
import uuid
from pathlib import Path

from django.conf import settings
from django.test import TestCase


class MediaServingTests(TestCase):
    """The media route is bound to MEDIA_ROOT when the URLconf loads, so the files go under it in a temp folder."""

    def setUp(self):
        self.name = f'wt-test-{uuid.uuid4().hex[:8]}'
        self.dir = Path(settings.MEDIA_ROOT) / self.name
        self.dir.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.dir, True)

    def test_html_is_downloaded_not_rendered(self):
        (self.dir / 'x.html').write_text('<script>alert(1)</script>')
        r = self.client.get(f'/media/{self.name}/x.html')
        self.assertEqual(r['Content-Disposition'], 'attachment')
        self.assertNotIn('html', r['Content-Type'])
        self.assertIn("script-src 'none'", r['Content-Security-Policy'])
        self.assertEqual(r['X-Content-Type-Options'], 'nosniff')

    def test_images_still_display(self):
        (self.dir / 'a.png').write_bytes(bytes([0x89]) + b'PNG' + bytes([13, 10, 26, 10]))
        r = self.client.get(f'/media/{self.name}/a.png')
        self.assertEqual(r['Content-Type'], 'image/png')
        self.assertFalse(r.get('Content-Disposition', 'inline').startswith('attachment'))
