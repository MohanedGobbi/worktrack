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

# Only well-formed markup is removed: tags (<b>, </div>, <img src=x ...>), comments,
# doctypes and processing instructions. A stray '<' as in "x<y" or "a < b" is text and
# stays; output escaping (templates, wtEsc, textContent) is what makes it safe to show.
_MARKUP_RE = re.compile(
    r'<!--.*?(?:-->|$)'                       # comments (also an unclosed one at the end)
    r'|<![A-Za-z\[][^<>]*>'                   # <!DOCTYPE ...>, <![CDATA[...]>
    r'|<\?[^<>]*\?>'                           # <?xml ...?>
    r'|</?[A-Za-z][\w:-]*(?:\s[^<>]*)?/?>',     # opening / closing / self-closing tags
    re.S,
)

RICH_TAGS = {'b', 'strong', 'i', 'em', 'br', 'a'}
_DROP_WITH_CONTENT = {'script', 'style', 'iframe', 'object', 'embed', 'noscript', 'template', 'svg', 'math', 'textarea', 'title', 'xmp', 'noembed', 'noframes'}
_SAFE_HREF = re.compile(r'^(https?://|mailto:|/(?![/\\])|#|\?)', re.I)


def clean_text(value):
    """Return ``value`` with HTML markup removed (None stays None)."""
    if value is None or not isinstance(value, str) or '<' not in value:
        return value
    previous = None
    # Repeat so that nested tricks like '<<b>script>' cannot reassemble a tag.
    while previous != value:
        previous = value
        value = _MARKUP_RE.sub('', value)
    return value


def clean_rich(value):
    """Keep only the messenger's formatting tags; escape everything else.

    Plain text (no markup) is returned unchanged, so ordinary messages are not
    re-serialised ("a < b & c" stays as typed).
    """
    if value is None or not isinstance(value, str) or not _MARKUP_RE.search(value):
        return value
    soup = BeautifulSoup(value, 'html.parser')
    for node in soup.find_all(string=lambda s: isinstance(s, Comment)):
        node.extract()
    # Drop dangerous containers first, then walk what is left.
    for tag in soup.find_all(_DROP_WITH_CONTENT):
        if not tag.decomposed:
            tag.decompose()
    for tag in soup.find_all(True):
        if tag.decomposed or tag.parent is None:
            continue
        name = (tag.name or '').lower()
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
