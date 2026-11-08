"""Helpers for user uploads that are shown back to people (photos)."""
import uuid
from io import BytesIO

from django.core.files.base import ContentFile

MAX_PHOTO_BYTES = 5 * 1024 * 1024


class BadImage(ValueError):
    """The upload is not a JPEG, PNG, GIF or WebP image, or it is too large."""


def process_photo(upload, max_side=512):
    """Decode an uploaded photo and re-encode it as a clean JPEG or PNG under a server-made name.

    Nothing the uploader appended (HTML, scripts) survives, and the file extension cannot choose the
    content type /media/ serves it with. Returns a ContentFile whose .name is the new file name.
    """
    if upload.size > MAX_PHOTO_BYTES:
        raise BadImage('too large')
    try:
        from PIL import Image, ImageOps
        with Image.open(upload) as im:
            if (im.format or '').upper() not in ('JPEG', 'PNG', 'GIF', 'WEBP'):
                raise BadImage('format')
            im = ImageOps.exif_transpose(im)
            im.thumbnail((max_side, max_side))
            out = BytesIO()
            if im.mode in ('RGBA', 'LA', 'P'):
                im.convert('RGBA').save(out, 'PNG')
                ext = 'png'
            else:
                im.convert('RGB').save(out, 'JPEG', quality=88)
                ext = 'jpg'
    except BadImage:
        raise
    except Exception as exc:
        raise BadImage('unreadable') from exc
    return ContentFile(out.getvalue(), name=f'{uuid.uuid4().hex}.{ext}')
