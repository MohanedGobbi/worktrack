from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from users.models import CustomUser

class AttendanceConfiguration(models.Model):
    """Singleton model for global attendance settings."""
    office_start_time = models.TimeField(default='09:00', help_text="Standard office start time for Late evaluations.")
    office_end_time = models.TimeField(default='17:00', help_text="Standard office end time.")
    
    class Meta:
        verbose_name = "Attendance Configuration"
        verbose_name_plural = "Attendance Configuration"
        
    def save(self, *args, **kwargs):
        if not self.pk and AttendanceConfiguration.objects.exists():
            raise ValidationError('There can be only one AttendanceConfiguration instance')
        return super(AttendanceConfiguration, self).save(*args, **kwargs)

    def __str__(self):
        return "Attendance Policy Settings"

class AttendanceRecord(models.Model):
    """Tracks daily attendance for users."""
    
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('late', 'Late'),
        ('absent', 'Absent'),
        ('excused', 'Excused'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.now)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Total hours worked")
    notes = models.TextField(blank=True, default='')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-check_in']
        unique_together = ('user', 'date')
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['status']),
        ]
        
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.date} ({self.get_status_display()})"
    
    def calculate_hours(self):
        """Calculate total hours between check-in and check-out."""
        if self.check_in and self.check_out:
            # Create full datetimes for the same day to calculate difference
            dummy_date = self.date
            in_dt = timezone.datetime.combine(dummy_date, self.check_in)
            out_dt = timezone.datetime.combine(dummy_date, self.check_out)
            
            # If check-out is technically before check-in (e.g. overnight shift), handle it
            if out_dt < in_dt:
                out_dt += timezone.timedelta(days=1)
                
            delta = out_dt - in_dt
            self.total_hours = round(delta.total_seconds() / 3600.0, 2)
        else:
            self.total_hours = 0.00
        return self.total_hours
