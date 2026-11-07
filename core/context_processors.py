from work_modules.models import WorkModule
from core.models import SiteConfiguration

def hex_to_rgb(hex_str, default="16, 185, 129"):
    """Convert a hex color code (#ffffff or #fff) to an RGB comma-separated string (e.g. '255, 255, 255')."""
    if not hex_str:
        return default
    s = hex_str.strip().lstrip('#')
    if len(s) == 3:
        s = ''.join([c * 2 for c in s])
    if len(s) != 6:
        return default
    try:
        r = int(s[0:2], 16)
        g = int(s[2:4], 16)
        b = int(s[4:6], 16)
        return f"{r}, {g}, {b}"
    except Exception:
        return default

# Theme preset color mappings (server-side mirror of theme_presets.js)
THEME_PRESET_COLORS = {
    # Default theme: the ROWD brand system (Rowd Blue / Signal Blue / Cyan Pulse / Charcoal).
    'rowd': {
        'primary': '#0033a0', 'secondary': '#131925', 'accent': '#19bedc',
        'bg_start': '#0033a0', 'bg_end': '#001f66',
        'glass_bg': '#ffffff', 'glass_border': '#dce2ec', 'glow': '#2d6bff',
        'sidebar_bg': '#0033a0', 'sidebar_text': '#ffffff', 'sidebar_muted': '#b9c8ec', 'sidebar_primary': '#ffffff',
        'portal_bg': '#0033a0', 'portal_primary': '#0033a0', 'portal_primary_hover': '#00287f',
        'portal_glow_rgba': 'rgba(45, 107, 255, 0.3)', 'portal_particle': '#19bedc',
    },
    'crimson': {
        'primary': '#dc2626', 'secondary': '#1e1e1e', 'accent': '#f87171',
        'bg_start': '#1a0000', 'bg_end': '#2d0a0a',
        'glass_bg': '#1a0000', 'glass_border': '#ffffff', 'glow': '#dc2626',
        'sidebar_bg': '#0a0a0a', 'sidebar_text': '#ffffff', 'sidebar_muted': '#9ca3af', 'sidebar_primary': '#f87171',
        'portal_bg': '#0a0000', 'portal_primary': '#dc2626', 'portal_primary_hover': '#b91c1c',
        'portal_glow_rgba': 'rgba(220, 38, 38, 0.3)', 'portal_particle': '#dc2626',
    },
    'emerald': {
        'primary': '#10b981', 'secondary': '#064e3b', 'accent': '#34d399',
        'bg_start': '#022c22', 'bg_end': '#064e3b',
        'glass_bg': '#022c22', 'glass_border': '#ffffff', 'glow': '#10b981',
        'sidebar_bg': '#0a1c17', 'sidebar_text': '#f0fdf4', 'sidebar_muted': '#86efac', 'sidebar_primary': '#34d399',
        'portal_bg': '#021a13', 'portal_primary': '#10b981', 'portal_primary_hover': '#059669',
        'portal_glow_rgba': 'rgba(16, 185, 129, 0.3)', 'portal_particle': '#10b981',
    },
    'ocean': {
        'primary': '#2563eb', 'secondary': '#0f172a', 'accent': '#38bdf8',
        'bg_start': '#0c1929', 'bg_end': '#1e3a5f',
        'glass_bg': '#0c1929', 'glass_border': '#ffffff', 'glow': '#2563eb',
        'sidebar_bg': '#070f23', 'sidebar_text': '#eff6ff', 'sidebar_muted': '#93c5fd', 'sidebar_primary': '#38bdf8',
        'portal_bg': '#050c1e', 'portal_primary': '#2563eb', 'portal_primary_hover': '#1d4ed8',
        'portal_glow_rgba': 'rgba(37, 99, 235, 0.3)', 'portal_particle': '#38bdf8',
    },
    'amber': {
        'primary': '#d97706', 'secondary': '#451a03', 'accent': '#fbbf24',
        'bg_start': '#1c1003', 'bg_end': '#451a03',
        'glass_bg': '#1c1003', 'glass_border': '#ffffff', 'glow': '#d97706',
        'sidebar_bg': '#180e03', 'sidebar_text': '#fffbeb', 'sidebar_muted': '#fde68a', 'sidebar_primary': '#fbbf24',
        'portal_bg': '#120902', 'portal_primary': '#d97706', 'portal_primary_hover': '#b45309',
        'portal_glow_rgba': 'rgba(217, 119, 6, 0.3)', 'portal_particle': '#fbbf24',
    },
    'violet': {
        'primary': '#7c3aed', 'secondary': '#2e1065', 'accent': '#c084fc',
        'bg_start': '#1a0533', 'bg_end': '#3b0764',
        'glass_bg': '#1a0533', 'glass_border': '#ffffff', 'glow': '#7c3aed',
        'sidebar_bg': '#130324', 'sidebar_text': '#faf5ff', 'sidebar_muted': '#d8b4fe', 'sidebar_primary': '#c084fc',
        'portal_bg': '#0d0219', 'portal_primary': '#7c3aed', 'portal_primary_hover': '#6d28d9',
        'portal_glow_rgba': 'rgba(124, 58, 237, 0.3)', 'portal_particle': '#c084fc',
    },
    'slate': {
        'primary': '#475569', 'secondary': '#0f172a', 'accent': '#94a3b8',
        'bg_start': '#0f172a', 'bg_end': '#1e293b',
        'glass_bg': '#0f172a', 'glass_border': '#ffffff', 'glow': '#475569',
        'sidebar_bg': '#0b111c', 'sidebar_text': '#f8fafc', 'sidebar_muted': '#94a3b8', 'sidebar_primary': '#cbd5e1',
        'portal_bg': '#090e17', 'portal_primary': '#475569', 'portal_primary_hover': '#334155',
        'portal_glow_rgba': 'rgba(71, 85, 105, 0.3)', 'portal_particle': '#94a3b8',
    },
    'rose': {
        'primary': '#e11d48', 'secondary': '#4c0519', 'accent': '#fda4af',
        'bg_start': '#1c0511', 'bg_end': '#4c0519',
        'glass_bg': '#1c0511', 'glass_border': '#ffffff', 'glow': '#e11d48',
        'sidebar_bg': '#16030c', 'sidebar_text': '#fff1f2', 'sidebar_muted': '#fecdd3', 'sidebar_primary': '#fda4af',
        'portal_bg': '#0f0208', 'portal_primary': '#e11d48', 'portal_primary_hover': '#be123c',
        'portal_glow_rgba': 'rgba(225, 29, 72, 0.3)', 'portal_particle': '#fda4af',
    },
    'teal': {
        'primary': '#0d9488', 'secondary': '#042f2e', 'accent': '#2dd4bf',
        'bg_start': '#042f2e', 'bg_end': '#0f766e',
        'glass_bg': '#042f2e', 'glass_border': '#ffffff', 'glow': '#0d9488',
        'sidebar_bg': '#031a19', 'sidebar_text': '#f0fdfa', 'sidebar_muted': '#5eead4', 'sidebar_primary': '#2dd4bf',
        'portal_bg': '#011716', 'portal_primary': '#0d9488', 'portal_primary_hover': '#0f766e',
        'portal_glow_rgba': 'rgba(13, 148, 136, 0.3)', 'portal_particle': '#2dd4bf',
    },
    'sapphire': {
        'primary': '#4f46e5', 'secondary': '#1e1b4b', 'accent': '#818cf8',
        'bg_start': '#0f0c33', 'bg_end': '#1e1b4b',
        'glass_bg': '#0f0c33', 'glass_border': '#ffffff', 'glow': '#4f46e5',
        'sidebar_bg': '#0b092b', 'sidebar_text': '#eef2ff', 'sidebar_muted': '#a5b4fc', 'sidebar_primary': '#818cf8',
        'portal_bg': '#080720', 'portal_primary': '#4f46e5', 'portal_primary_hover': '#4338ca',
        'portal_glow_rgba': 'rgba(79, 70, 229, 0.3)', 'portal_particle': '#818cf8',
    },
    'monochrome': {
        'primary': '#27272a', 'secondary': '#09090b', 'accent': '#e4e4e7',
        'bg_start': '#09090b', 'bg_end': '#18181b',
        'glass_bg': '#09090b', 'glass_border': '#ffffff', 'glow': '#71717a',
        'sidebar_bg': '#09090b', 'sidebar_text': '#f4f4f5', 'sidebar_muted': '#a1a1aa', 'sidebar_primary': '#e4e4e7',
        'portal_bg': '#000000', 'portal_primary': '#27272a', 'portal_primary_hover': '#18181b',
        'portal_glow_rgba': 'rgba(161, 161, 170, 0.25)', 'portal_particle': '#e4e4e7',
    },
}

# Quick-start colour pairs for Site Settings (brand, accent). Picking one fills
# the custom colour inputs; the theme itself only ever reads those inputs.
WT_SWATCHES = [
    ('rowd', 'ROWD', 'رود', '#0033a0', '#19bedc'),
    ('crimson', 'Crimson', 'قرمزي', '#b91c1c', '#f59e9e'),
    ('emerald', 'Emerald', 'زمردي', '#047857', '#34d399'),
    ('ocean', 'Ocean', 'محيطي', '#1d4ed8', '#38bdf8'),
    ('violet', 'Violet', 'بنفسجي', '#6d28d9', '#c4b5fd'),
    ('teal', 'Teal', 'فيروزي', '#0f766e', '#5eead4'),
    ('slate', 'Slate', 'رمادي', '#334155', '#94a3b8'),
]

# Attach primary_rgb to every preset
for k, v in THEME_PRESET_COLORS.items():
    v['primary_rgb'] = hex_to_rgb(v.get('primary', '#10b981'))


def sidebar_modules(request):
    """Make WorkModules available globally for the sidebar."""
    if request.user.is_authenticated:
        visible_modules = list(WorkModule.get_visible_modules(request.user))
        page_size = 5
        module_pages = [visible_modules[i:i + page_size] for i in range(0, len(visible_modules), page_size)]
        return {
            'all_modules_list': visible_modules,
            'module_pages': module_pages,
        }
    return {'all_modules_list': [], 'module_pages': []}

from users.models import SiteSettings, SidebarVisibilityRule, SystemProfile

def site_config(request):
    """Make SiteConfiguration available globally with theme preset colors and sidebar visibility rules."""
    config = SiteConfiguration.objects.first()
    if not config:
        # Create a default configuration if none exists
        config = SiteConfiguration.objects.create()
    
    # Get theme preset colors (fallback to emerald/configured preset)
    preset_key = getattr(config, 'theme_preset', 'rowd') or 'rowd'
    theme_colors = dict(THEME_PRESET_COLORS.get(preset_key, THEME_PRESET_COLORS['rowd']))
    
    # If custom primary color is saved on site_config, compute its RGB dynamically
    effective_primary = getattr(config, 'primary_color', None) or theme_colors.get('primary', '#10b981')
    primary_rgb_val = hex_to_rgb(effective_primary)
    theme_colors['primary_rgb'] = primary_rgb_val
    config.primary_rgb = primary_rgb_val

    # Sidebar rules evaluation
    sb_rules = {}
    try:
        user_role = request.user.role if (request.user.is_authenticated and hasattr(request.user, 'role')) else 'worker'
        rules = SidebarVisibilityRule.objects.all().order_by('order')
        if not rules.exists():
            SidebarVisibilityRule.initialize_defaults()
            rules = SidebarVisibilityRule.objects.all().order_by('order')
        for r in rules:
            visible = r.is_allowed
            if visible:
                if user_role == 'super_admin':
                    visible = r.visible_admin
                elif user_role == 'manager':
                    visible = r.visible_manager
                else:
                    visible = r.visible_worker
            sb_rules[r.feature_key] = visible
    except Exception:
        pass
    
    return {
        'site_config': config,
        'site_settings': SiteSettings.get_settings(),
        'theme_preset_key': preset_key,
        'theme_colors': theme_colors,
        'wt_theme': _wt_theme(config, preset_key, theme_colors),
        'wt_lang': _wt_lang(request),
        'sb_rules': sb_rules,
    }


def _clean_hex(value, fallback):
    s = (value or '').strip()
    if len(s) in (4, 7) and s.startswith('#') and all(c in '0123456789abcdefABCDEF' for c in s[1:]):
        return s
    return fallback


def _wt_theme(config, preset_key, theme_colors):
    """The two brand inputs the WorkTrack design reads. Everything else is derived in CSS.

    A preset supplies them; the 'custom' preset takes them from the admin's colour fields.
    """
    if preset_key == 'custom':
        brand = _clean_hex(getattr(config, 'primary_color', ''), '#0033a0')
        accent = _clean_hex(getattr(config, 'accent_color', ''), '#19bedc')
    else:
        brand = _clean_hex(theme_colors.get('primary'), '#0033a0')
        accent = _clean_hex(theme_colors.get('accent'), '#19bedc')
    on_brand = _clean_hex(getattr(config, 'on_brand_color', ''), '#ffffff') if preset_key == 'custom' else '#ffffff'
    return {'brand': brand, 'accent': accent, 'on_brand': on_brand, 'brand_rgb': hex_to_rgb(brand, '0, 51, 160'),
            'logo_tone': _logo_tone(config)}


_LOGO_TONE_CACHE = {}


def _logo_tone(config):
    """'light' when the uploaded logo is mostly light ink (needs a dark backdrop), else 'dark'.

    Measured once per file version so any customer logo sits on a backdrop it can be read on.
    """
    logo = getattr(config, 'logo', None)
    if not logo:
        return 'none'
    try:
        import os
        path = logo.path
        key = (path, os.path.getmtime(path))
        if key in _LOGO_TONE_CACHE:
            return _LOGO_TONE_CACHE[key]
        from PIL import Image
        im = Image.open(path).convert('RGBA')
        im.thumbnail((96, 96))
        total = weight = 0.0
        for r, g, b, a in im.getdata():
            if a < 40:
                continue
            w = a / 255.0
            total += w * (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
            weight += w
        tone = 'light' if weight and (total / weight) > 0.72 else 'dark'
        _LOGO_TONE_CACHE[key] = tone
        return tone
    except Exception:
        return 'dark'




def _wt_lang(request):
    """Language for the first server render, so RTL pages never flash LTR before i18n.js runs."""
    lang = request.COOKIES.get('worktrack_lang') or request.COOKIES.get('django_language')
    if lang not in ('ar', 'en'):
        try:
            lang = SiteSettings.get_settings().default_language or 'ar'
        except Exception:
            lang = 'ar'
    return 'ar' if lang == 'ar' else 'en'
