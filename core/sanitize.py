"""Server-side cleaning of user-written text.

Templates auto-escape, but several pages and scripts build HTML from stored
values (innerHTML, emails, JSON islands), so stored text is cleaned on save
as a second line of defence.

- ``clean_text``: plain text. Removes anything that looks like an HTML tag or
  comment and keeps the words. Use for comments, notes, todo text, titles.
- ``clean_rich``: the small allowlist the messenger renders
  (b, strong, i, em, br and http(s)/relative/mailto links). Mirrors
  ``safeHtml`` in templates/messaging/messenger_page.html.
- ``script_json``: JSON that is safe to place inside a <script> block.
"""
import json
import re

from bs4 import BeautifulSoup, Comment
from django.utils.safestring import mark_safe

# A '<' that starts a tag, closing tag, comment, doctype or processing
# instruction, up to the next '>' or the end of the text. An unclosed tag is
# removed too, because a later concatenation could close it.
_TAG_RE = re.compile(r'<(?=[A-Za-z!/?])[^>]*(?:>|$)')

RICH_TAGS = {'b', 'strong', 'i', 'em', 'br', 'a'}
_DROP_WITH_CONTENT = {'script', 'style', 'iframe', 'object', 'embed', 'noscript', 'template', 'svg', 'math'}
_SAFE_HREF = re.compile(r'^(https?://|mailto:|/(?!/)|#|\?)', re.I)


def clean_text(value):
    """Return ``value`` with HTML tags and comments removed (None stays None)."""
    if value is None or not isinstance(value, str) or '<' not in value:
        return value
    previous = None
    # Repeat so that nested tricks like '<<b>script>' cannot reassemble.
    while previous != value:
        previous = value
        value = _TAG_RE.sub('', value)
    return value


def clean_rich(value):
    """Keep only the messenger's formatting tags; escape everything else."""
    if value is None or not isinstance(value, str) or '<' not in value:
        return value
    soup = BeautifulSoup(value, 'html.parser')
    for node in soup.find_all(string=lambda s: isinstance(s, Comment)):
        node.extract()
    for tag in soup.find_all(True):
        name = (tag.name or '').lower()
        if name in _DROP_WITH_CONTENT:
            tag.decompose()
            continue
        if name not in RICH_TAGS:
            tag.unwrap()
            continue
        href = tag.get('href') if name == 'a' else None
        tag.attrs = {}
        if name == 'a':
            href = (href or '').strip()
            if href and _SAFE_HREF.match(href):
                tag['href'] = href
                if href.lower().startswith(('http://', 'https://')):
                    tag['target'] = '_blank'
                    tag['rel'] = 'noopener noreferrer'
            else:
                tag.unwrap()
    return str(soup)


def script_json(data):
    """``json.dumps`` that cannot close a surrounding <script> element."""
    text = json.dumps(data, default=str)
    text = text.replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    text = text.replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    return mark_safe(text)


def clean_fields(instance, plain=(), rich=()):
    """Clean the named attributes of a model instance in place."""
    for name in plain:
        setattr(instance, name, clean_text(getattr(instance, name, None)))
    for name in rich:
        setattr(instance, name, clean_rich(getattr(instance, name, None)))
