"""Feature switches backed by SidebarVisibilityRule.

A feature that is switched off (Admin console > sidebar visibility, or `is_allowed=False`)
disappears from the sidebar and links (templates read `sb_rules.<key>`) and its pages
redirect home, so it cannot be reached by typing the URL. The code stays in place, so
turning the rule back on restores the feature.
"""
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def feature_enabled(key):
    from users.models import SidebarVisibilityRule
    rule = SidebarVisibilityRule.objects.filter(feature_key=key).values_list('is_allowed', flat=True).first()
    return rule is not False  # no rule row = enabled


def feature_required(key):
    """Wrap a view (usable in urls.py: feature_required('roadmap')(roadmap_gantt))."""
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not feature_enabled(key):
                if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.path.startswith('/api/'):
                    from django.http import JsonResponse
                    return JsonResponse({'status': 'error', 'message': 'This feature is switched off.'}, status=404)
                messages.info(request, 'This feature is not enabled for this install.')
                return redirect('dashboard')
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


# ── Uploaded files ─────────────────────────────────────────────────────────
# Users upload files that are served from /media/ on the app's own origin. A file such as an .html or .svg
# must never run script there, whatever its content: scripts are blocked by CSP, markup-like types are
# always downloaded, and the browser may not guess a different type.
_DOWNLOAD_ONLY = ('.html', '.htm', '.xhtml', '.xht', '.svg', '.svgz', '.xml', '.xsl', '.js', '.mjs', '.shtml', '.php')


def safe_media_serve(request, path, document_root=None):
    from django.views.static import serve
    response = serve(request, path, document_root=document_root)
    response['X-Content-Type-Options'] = 'nosniff'
    # object-src 'none' would stop the browser's built-in PDF viewer, so PDFs get the lighter policy.
    if path.lower().endswith('.pdf'):
        response['Content-Security-Policy'] = "script-src 'none'; base-uri 'none'; form-action 'none'"
    else:
        response['Content-Security-Policy'] = "script-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"
    if path.lower().endswith(_DOWNLOAD_ONLY):
        response['Content-Disposition'] = 'attachment'
        response['Content-Type'] = 'application/octet-stream'
    return response
