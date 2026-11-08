import os
import time
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

TRANSLATION_CACHE_VERSION_KEY = 'translation_cache_version'
TRANSLATION_TIMESTAMP_FILE = '/tmp/translation_last_updated.txt'


def _touch_translation_timestamp():
    try:
        with open(TRANSLATION_TIMESTAMP_FILE, 'w', encoding='utf-8') as f:
            f.write(str(time.time()))
    except Exception:
        pass

class SiteConfiguration(models.Model):
    THEME_PRESET_CHOICES = [
        ('rowd', 'ROWD (Rowd Blue / Signal / Cyan, default)'),
        ('crimson', 'Royal Crimson (Red / Ruby / Black)'),
        ('emerald', 'Emerald Sovereign (Green / Malachite)'),
        ('ocean', 'Ocean Cobalt (Blue / Sky)'),
        ('amber', 'Imperial Amber (Gold / Bronze)'),
        ('violet', 'Royal Amethyst (Purple / Lilac)'),
        ('slate', 'Titanium Slate (Slate / Platinum)'),
        ('rose', 'Rose Bordeaux (Rose / Velvet)'),
        ('teal', 'Nordic Teal (Teal / Aquamarine)'),
        ('sapphire', 'Electric Sapphire (Indigo / Sapphire)'),
        ('monochrome', 'Obsidian Monochrome (Pure Carbon / Silver)'),
        ('custom', 'Custom (Manual Colors)'),
    ]
    
    app_name = models.CharField(max_length=150, default="WorkTrack Pro", help_text="System application name in English")
    app_name_ar = models.CharField(max_length=150, default="وورك تراك برو", blank=True, null=True, help_text="System application name in Arabic")
    logo = models.ImageField(upload_to='site/', blank=True, null=True, help_text="Upload your custom site logo here (max height 40px recommended).")
    
    @property
    def app_name_en(self):
        return self.app_name

    @property
    def primary_rgb(self):
        if hasattr(self, '_primary_rgb') and self._primary_rgb:
            return self._primary_rgb
        s = (self.primary_color or '#10b981').strip().lstrip('#')
        if len(s) == 3:
            s = ''.join([c * 2 for c in s])
        if len(s) == 6:
            try:
                return f"{int(s[0:2], 16)}, {int(s[2:4], 16)}, {int(s[4:6], 16)}"
            except Exception:
                pass
        return "16, 185, 129"

    @primary_rgb.setter
    def primary_rgb(self, value):
        self._primary_rgb = value

    theme_preset = models.CharField(max_length=20, choices=THEME_PRESET_CHOICES, default='rowd', help_text="Select a pre-built color theme for the entire application")
    primary_color = models.CharField(max_length=20, default="#10b981", help_text="Primary brand color (Hex format, e.g., #10b981)")
    secondary_color = models.CharField(max_length=20, default="#064e3b", help_text="Secondary brand color (Hex format, e.g., #064e3b)")
    
    
    THEME_MODE_CHOICES = [
        ('light', 'Clean Light (فاتح رصين - افتراضي للنظام)'),
        ('dark', 'Obsidian Dark (داكن أوبسيديان)'),
    ]
    theme_mode = models.CharField(max_length=20, choices=THEME_MODE_CHOICES, default='light', help_text="Theme appearance mode")
    portal_bg_color = models.CharField(max_length=20, default="#070d1f", help_text="Background color for Login & Home page")
    gateway_image = models.ImageField(upload_to='site/gateways/', blank=True, null=True, help_text="Background image for Login & Home page")
    background_image = models.ImageField(upload_to='site/backgrounds/', blank=True, null=True, help_text="Global background image (e.g., space nebula)")
    banner_image = models.ImageField(upload_to='site/banners/', blank=True, null=True, help_text="Banner background image")
    font_main = models.CharField(max_length=100, default="'Inter', sans-serif", help_text="Main font family")
    accent_color = models.CharField(max_length=20, default="#0ea5e9", help_text="Accent color for highlighting")
    bg_color_start = models.CharField(max_length=20, default="#020617", help_text="Background gradient start")
    bg_color_end = models.CharField(max_length=20, default="#0f172a", help_text="Background gradient end")
    glass_bg_color = models.CharField(max_length=50, default="rgba(15, 23, 42, 0.6)", help_text="RGBA base color for glass panels")
    glass_border_color = models.CharField(max_length=50, default="rgba(255, 255, 255, 0.08)", help_text="RGBA border color for glass panels")
    glass_blur = models.IntegerField(default=16, help_text="Backdrop blur in px")
    glow_color = models.CharField(max_length=50, default="rgba(16, 185, 129, 0.15)", help_text="RGBA glow for active components")
    border_radius = models.CharField(max_length=20, default="16px", help_text="Base border radius")
    
    # Widget & Banner Specific Settings
    widget_color = models.CharField(max_length=50, default="rgba(30, 41, 59, 0.8)", help_text="Color for widgets/cards")
    banner_text_color = models.CharField(max_length=50, default="#ffffff", help_text="Dedicated color for banner title")
    banner_text_style = models.CharField(max_length=50, choices=[('solid', 'Solid Color'), ('gradient', 'Gradient (Primary/Accent)')], default='gradient', help_text="Text style for banner title")
    
    # Custom Button & Accent Color Settings
    button_color = models.CharField(max_length=20, default="#dc2626", help_text="Primary button background color (e.g., Login button)")
    button_hover_color = models.CharField(max_length=20, default="#b91c1c", help_text="Primary button hover state color")
    button_text_color = models.CharField(max_length=20, default="#ffffff", help_text="Primary button text color")
    
    # Sidebar Architecture Fields
    sidebar_bg_color = models.CharField(max_length=50, default="#0f1412", help_text="Sidebar base color")
    sidebar_text_color = models.CharField(max_length=50, default="#f2fffd", help_text="Sidebar primary text color")
    sidebar_muted_color = models.CharField(max_length=50, default="#8a9e9a", help_text="Sidebar secondary/icon color")
    sidebar_primary_color = models.CharField(max_length=50, default="#dc2626", help_text="Sidebar hover/active accent")
    sidebar_button_color = models.CharField(max_length=20, default="#dc2626", help_text="Sidebar action button color")
    sidebar_width = models.CharField(max_length=20, default="320px", help_text="Sidebar width (e.g. 320px)")
    
    # System Semantic & Surface Roles
    card_bg_color = models.CharField(max_length=50, default="#0e1d16", blank=True, help_text="Card / Surface background color")
    text_main_color = models.CharField(max_length=50, default="#eaf5ee", blank=True, help_text="Main typography color")
    text_muted_color = models.CharField(max_length=50, default="#7f9487", blank=True, help_text="Muted / subtitle text color")
    border_color = models.CharField(max_length=50, default="#1f3329", blank=True, help_text="Global border / divider color")
    success_color = models.CharField(max_length=50, default="#10b981", blank=True, help_text="Success indicator color")
    danger_color = models.CharField(max_length=50, default="#ef4444", blank=True, help_text="Danger / error color")
    warning_color = models.CharField(max_length=50, default="#f59e0b", blank=True, help_text="Warning color")
    info_color = models.CharField(max_length=50, default="#0ea5e9", blank=True, help_text="Info indicator color")
    
    # ── Theme model (what the WorkTrack design reads) ───────────────────────
    # Brand = primary_color, accent = accent_color, plus the text colour on brand.
    on_brand_color = models.CharField(max_length=20, default="#ffffff", help_text="Text and icon colour on the brand colour")

    # ── Contact and footer (per install, both languages) ────────────────────
    contact_email = models.EmailField(blank=True, default="", help_text="Public contact email shown in the footer")
    contact_phone = models.CharField(max_length=40, blank=True, default="", help_text="Public contact phone shown in the footer")
    website_url = models.URLField(blank=True, default="", help_text="Institution website")
    address = models.CharField(max_length=255, blank=True, default="", help_text="Postal address (English)")
    address_ar = models.CharField(max_length=255, blank=True, default="", help_text="Postal address (Arabic)")
    footer_text = models.CharField(max_length=200, blank=True, default="", help_text="Footer line (English). Empty = product name")
    footer_text_ar = models.CharField(max_length=200, blank=True, default="", help_text="Footer line (Arabic). Empty = product name")

    # ── Partner (optional; shown next to the ROWD credit, never instead of it) ──
    partner_name = models.CharField(max_length=150, blank=True, default="", help_text="Partner organisation (English)")
    partner_name_ar = models.CharField(max_length=200, blank=True, default="", help_text="Partner organisation (Arabic)")
    partner_url = models.URLField(blank=True, default="", help_text="Partner website")
    partner_logo = models.ImageField(upload_to='site/partners/', blank=True, null=True, help_text="Partner logo")

    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"
        
    def save(self, *args, **kwargs):
        if not self.pk and SiteConfiguration.objects.exists():
            raise ValidationError('There can be only one SiteConfiguration instance')
        return super(SiteConfiguration, self).save(*args, **kwargs)

    def __str__(self):
        return "System Settings"


class AllowedHost(models.Model):
    """Dynamically manages allowed hostnames/IPs for the application."""
    hostname = models.CharField(max_length=255, unique=True, help_text="Domain name or IP Address (e.g., example.com, 192.168.1.5)")
    description = models.CharField(max_length=255, blank=True, null=True, help_text="Optional description of this host")
    is_active = models.BooleanField(default=True, help_text="Uncheck to temporarily disable this host")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['hostname']
        verbose_name = "Allowed Host"
        verbose_name_plural = "Allowed Hosts"
        
    def __str__(self):
        return self.hostname

@receiver(post_save, sender=AllowedHost)
@receiver(post_delete, sender=AllowedHost)
def clear_allowed_host_cache(sender, instance, **kwargs):
    cache_key = f"allowed_host_{instance.hostname}"
    cache.delete(cache_key)


class BlockedHostAttempt(models.Model):
    """Logs intrusion attempts by unrecognized hosts."""
    hostname = models.CharField(max_length=255, help_text="The Host header the client tried to access")
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="The IP address of the client making the request")
    attempt_count = models.PositiveIntegerField(default=1)
    last_attempt = models.DateTimeField(auto_now=True)
    first_attempt = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-last_attempt']
        verbose_name = "Blocked Host Attempt"
        verbose_name_plural = "Blocked Host Attempts"
        
    def __str__(self):
        return f"Blocked: {self.hostname} ({self.attempt_count} times)"

class TranslationItem(models.Model):
    """Dynamically stores translation strings for the application."""
    key = models.CharField(max_length=255, unique=True, db_index=True)
    english_text = models.TextField(blank=True, null=True, help_text="Default English text")
    arabic_text = models.TextField(blank=True, null=True, help_text="Translated Arabic text")
    context = models.CharField(max_length=255, blank=True, null=True, help_text="Context or page where this string is used")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['key']
        verbose_name = "Translation Item"
        verbose_name_plural = "Translation Items"

    def __str__(self):
        return self.key

@receiver(post_save, sender=TranslationItem)
@receiver(post_delete, sender=TranslationItem)
def clear_translation_cache(sender, instance, **kwargs):
    cache.delete('all_translations')
    try:
        version = cache.get(TRANSLATION_CACHE_VERSION_KEY, 0) or 0
        cache.set(TRANSLATION_CACHE_VERSION_KEY, version + 1, timeout=None)
    except Exception:
        pass
    _touch_translation_timestamp()
