from django import forms
from .models import AttendanceConfiguration

class AttendanceConfigurationForm(forms.ModelForm):
    class Meta:
        model = AttendanceConfiguration
        fields = ['office_start_time', 'office_end_time']
        widgets = {
            'office_start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-lg'}),
            'office_end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-lg'}),
        }
