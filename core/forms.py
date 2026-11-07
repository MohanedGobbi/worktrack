from django import forms
from .models import SiteConfiguration

class SiteConfigurationForm(forms.ModelForm):
    class Meta:
        model = SiteConfiguration
        fields = [
            'app_name', 'app_name_ar', 'theme_mode',
            'logo', 'theme_preset', 'primary_color', 'secondary_color',
            'banner_image', 'gateway_image', 'background_image', 'font_main', 'accent_color', 'bg_color_start',
            'bg_color_end', 'glass_bg_color', 'glass_border_color', 'glass_blur',
            'glow_color', 'border_radius', 'widget_color', 'banner_text_color', 'banner_text_style',
            'button_color', 'button_hover_color', 'button_text_color',
            'sidebar_bg_color', 'sidebar_text_color', 'sidebar_muted_color', 'sidebar_primary_color', 'sidebar_button_color', 'sidebar_width',
            'portal_bg_color',
            'card_bg_color', 'text_main_color', 'text_muted_color', 'border_color',
            'success_color', 'danger_color', 'warning_color', 'info_color'
        ]
        widgets = {
            'app_name': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'e.g. Worktrack Pro'}),
            'app_name_ar': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'مثال: وورك تراك برو', 'dir': 'rtl'}),
            'theme_mode': forms.HiddenInput(attrs={'id': 'id_theme_mode'}),
            'theme_preset': forms.Select(attrs={'class': 'form-select', 'id': 'id_theme_preset'}),
            'primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Primary Color'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Secondary Color'}),
            'accent_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Accent Color'}),
            'portal_bg_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Portal Background'}),
            'bg_color_start': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Background Gradient Start'}),
            'bg_color_end': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Background Gradient End'}),
            'button_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Button Color'}),
            'button_hover_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Button Hover Color'}),
            'button_text_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Button Text Color'}),
            'logo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'banner_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'gateway_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'background_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'font_main': forms.Select(attrs={'class': 'form-select'}, choices=[
                ("'Inter', sans-serif", "Inter (Clean & Professional)"),
                ("'Roboto', sans-serif", "Roboto (Standard Corporate)"),
                ("'Plus Jakarta Sans', sans-serif", "Plus Jakarta Sans (Modern)"),
                ("'Space Grotesk', sans-serif", "Space Grotesk (Tech/Cyber)"),
                ("system-ui, -apple-system, sans-serif", "System Default (Native)")
            ]),
            'glass_bg_color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'rgba(2, 44, 34, 0.65) or #022c22'}),
            'glass_border_color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'rgba(255, 255, 255, 0.2) or #ffffff'}),
            'glass_blur': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'glow_color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'rgba(16, 185, 129, 0.25) or #10b981'}),
            'border_radius': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '16px or 1rem'}),
            'widget_color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'rgba(2, 44, 34, 0.85) or #022c22'}),
            'banner_text_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Banner Text Color'}),
            'banner_text_style': forms.Select(attrs={'class': 'form-select'}),
            'sidebar_bg_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Sidebar Base Color'}),
            'sidebar_text_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Sidebar Primary Text'}),
            'sidebar_muted_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Sidebar Icon Color'}),
            'sidebar_primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Sidebar Hover/Active'}),
            'sidebar_button_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Sidebar Action Button'}),
            'sidebar_width': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 320px'}),
            'card_bg_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Card / Surface Background'}),
            'text_main_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Main Body Text Color'}),
            'text_muted_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Muted / Subtitle Text Color'}),
            'border_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Border / Divider Color'}),
            'success_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Success State Color'}),
            'danger_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Danger State Color'}),
            'warning_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Warning State Color'}),
            'info_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Info State Color'})
        }


import re as _re

_HEX = _re.compile(r'^#(?:[0-9a-fA-F]{3}){1,2}$')


class SiteThemeForm(forms.ModelForm):
    """Site Settings, built around the theme model: identity, three colours,
    contact and footer. The legacy colour columns stay in the database for old
    pages but are no longer edited here."""

    theme_preset = forms.ChoiceField(choices=[('rowd', 'ROWD default'), ('custom', 'Custom colours')])

    class Meta:
        model = SiteConfiguration
        fields = [
            'app_name', 'app_name_ar', 'logo', 'banner_image',
            'theme_preset', 'primary_color', 'accent_color', 'on_brand_color',
            'contact_email', 'contact_phone', 'website_url', 'address', 'address_ar',
            'footer_text', 'footer_text_ar',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['app_name'].required = True
        for name in ('logo', 'banner_image'):
            self.fields[name].required = False
        # A legacy preset (crimson, emerald, ...) is shown as custom colours.
        if self.instance and self.instance.theme_preset not in ('rowd', 'custom'):
            self.initial['theme_preset'] = 'custom'

    def _hex(self, name, fallback):
        value = (self.cleaned_data.get(name) or '').strip()
        if not value:
            return fallback
        if not _HEX.match(value):
            raise forms.ValidationError('Use a hex colour such as #0033a0.')
        if len(value) == 4:
            value = '#' + ''.join(c * 2 for c in value[1:])
        return value.lower()

    def clean_primary_color(self):
        return self._hex('primary_color', '#0033a0')

    def clean_accent_color(self):
        return self._hex('accent_color', '#19bedc')

    def clean_on_brand_color(self):
        return self._hex('on_brand_color', '#ffffff')

    def clean_app_name(self):
        return (self.cleaned_data.get('app_name') or '').strip()
