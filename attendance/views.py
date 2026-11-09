from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
import csv
from .models import AttendanceRecord
import datetime

@login_required
@require_http_methods(["GET"])
def attendance_dashboard(request):
    """View and manage attendance records based on user role."""
    today = timezone.now().date()
    
    # Get current user's record for today
    my_today_record = AttendanceRecord.objects.filter(user=request.user, date=today).first()
    
    # Base query
    if request.user.role in ['admin', 'super_admin']:
        # Admins see everyone
        records_query = AttendanceRecord.objects.select_related('user', 'user__department')
    elif request.user.role == 'manager':
        # Managers see their team and themselves
        team_members = [u.id for u in getattr(request.user, 'managed_users', []) if hasattr(request.user, 'managed_users')]
        # Also need to get users whose profile__manager=request.user
        from users.models import UserProfile
        team_ids = list(UserProfile.objects.filter(manager=request.user).values_list('user_id', flat=True))
        team_ids.append(request.user.id)
        records_query = AttendanceRecord.objects.filter(user_id__in=team_ids).select_related('user', 'user__department')
    else:
        # Workers see only themselves
        records_query = AttendanceRecord.objects.filter(user=request.user).select_related('user')
        
    # Filters
    # For legacy links that pass 'date', use it as both start and end
    legacy_date = request.GET.get('date')
    
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if legacy_date and not start_date_str and not end_date_str:
        start_date_str = legacy_date
        end_date_str = legacy_date
        
    try:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else today - datetime.timedelta(days=7)
    except ValueError:
        start_date = today - datetime.timedelta(days=7)
        
    try:
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else today
    except ValueError:
        end_date = today
        
    status_filter = request.GET.get('status', '')
    user_filter = request.GET.get('user_filter', 'all')
    
    target_user = None
    if request.user.role in ['admin', 'super_admin', 'manager']:
        if user_filter == 'me':
            records_query = records_query.filter(user=request.user)
            target_user = request.user
        elif user_filter != 'all' and user_filter.isdigit():
            user_id = int(user_filter)
            records_query = records_query.filter(user_id=user_id)
            from users.models import CustomUser
            target_user = CustomUser.objects.filter(id=user_id).first()
    
    filtered_records = records_query.filter(date__gte=start_date, date__lte=end_date)
    if status_filter:
        filtered_records = filtered_records.filter(status=status_filter)
        
    filtered_records = filtered_records.order_by('-date', '-check_in', 'user__first_name')
    
    # Pagination (10 per page)
    paginator = Paginator(filtered_records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Monthly stats for the logged-in user
    first_day_of_month = today.replace(day=1)
    my_monthly_records = AttendanceRecord.objects.filter(user=request.user, date__gte=first_day_of_month)
    my_stats = my_monthly_records.aggregate(
        present_count=Count('id', filter=Q(status='present')),
        late_count=Count('id', filter=Q(status='late')),
        absent_count=Count('id', filter=Q(status='absent')),
        total_hours=Sum('total_hours')
    )
    my_stats['total_hours'] = my_stats['total_hours'] or 0.0

    # Team stats if manager/admin
    team_stats = None
    if request.user.role in ['admin', 'super_admin', 'manager']:
        team_today = records_query.filter(date=today)
        team_stats = team_today.aggregate(
            present_count=Count('id', filter=Q(status='present')),
            late_count=Count('id', filter=Q(status='late')),
            absent_count=Count('id', filter=Q(status='absent'))
        )
        
    context = {
        'today': today,
        'start_date': start_date,
        'end_date': end_date,
        'my_today_record': my_today_record,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'user_filter': user_filter,
        'target_user': target_user,
        'my_stats': my_stats,
        'team_stats': team_stats,
        'is_manager_or_admin': request.user.role in ['admin', 'super_admin', 'manager'],
    }
    # Phase 1: Heatmap Calendar Data Generation (Restricted to Admins)
    if request.user.role in ['admin', 'super_admin']:
        # Get requested month or default to current month
        month_filter = request.GET.get('month', today.strftime('%Y-%m'))
        try:
            target_date = datetime.datetime.strptime(month_filter, '%Y-%m').date()
        except ValueError:
            target_date = today.replace(day=1)
            
        target_year = target_date.year
        target_month_num = target_date.month
        
        # Get all records for the requested month, not just the user's
        import calendar
        cal = calendar.monthcalendar(target_year, target_month_num)
        month_data = []
        
        # We need an aggregate view for admins. Let's show a heatmap of overall org attendance.
        # Get all records for the target month
        first_day_of_target = target_date.replace(day=1)
        last_day_of_target = target_date.replace(
            month=(target_month_num % 12) + 1, 
            day=1, 
            year=target_year + (target_month_num // 12)
        ) - datetime.timedelta(days=1)
        
        monthly_org_records = AttendanceRecord.objects.filter(
            date__gte=first_day_of_target, 
            date__lte=last_day_of_target
        )
        
        # Count present/late/absent per day for the whole org
        daily_stats = monthly_org_records.values('date').annotate(
            present=Count('id', filter=Q(status='present')),
            late=Count('id', filter=Q(status='late')),
            absent=Count('id', filter=Q(status='absent'))
        )
        
        stats_dict = {d['date']: d for d in daily_stats}
        
        for week in cal:
            week_data = []
            for day in week:
                if day == 0:
                    week_data.append({'day': 0, 'status': 'empty'})
                else:
                    date_obj = datetime.date(target_year, target_month_num, day)
                    stats = stats_dict.get(date_obj)
                    
                    if date_obj > today:
                        week_data.append({'day': day, 'status': 'future'})
                    elif date_obj.weekday() >= 5: # Weekend
                        week_data.append({'day': day, 'status': 'weekend'})
                    elif stats:
                        # Determine dominant status for the org on this day
                        # If more than 20% are absent/late, color it yellow, otherwise green
                        total_expected = stats['present'] + stats['late'] + stats['absent']
                        if total_expected == 0:
                            week_data.append({'day': day, 'status': 'empty'})
                        else:
                            late_absent_ratio = (stats['late'] + stats['absent']) / total_expected
                            if stats['absent'] > stats['present']:
                                status = 'absent'
                            elif late_absent_ratio > 0.2:
                                status = 'late'
                            else:
                                status = 'present'
                                
                            week_data.append({
                                'day': day, 
                                'status': status, 
                                'present_count': stats['present'],
                                'late_count': stats['late'],
                                'absent_count': stats['absent']
                            })
                    else:
                        week_data.append({'day': day, 'status': 'empty'})
            month_data.append(week_data)
            
        context['calendar_data'] = month_data
        context['heatmap_month_name'] = f'{target_date.month}/{target_date.year}'  # numeric: reads the same in Arabic and English
        context['heatmap_month_value'] = target_date.strftime('%Y-%m')
    
    # Phase 1: Department Benchmarking Data (Admins Only)
    import json
    if request.user.role in ['admin', 'super_admin']:
        dept_stats_raw = AttendanceRecord.objects.filter(
            date__gte=first_day_of_month
        ).values('user__department__name').annotate(
            present=Count('id', filter=Q(status='present')),
            late=Count('id', filter=Q(status='late')),
            absent=Count('id', filter=Q(status='absent'))
        )
        
        labels = []
        present_data = []
        late_data = []
        
        for d in dept_stats_raw:
            name = d['user__department__name'] or 'Unassigned'
            labels.append(name)
            present_data.append(d['present'])
            late_data.append(d['late'])
            
        context['chart_labels'] = labels
        context['chart_present'] = present_data
        context['chart_late'] = late_data
        
        # Phase 1: Chronic Late Algorithm
        # Find users who have been late 3 or more times in the current month
        chronic_late_users = AttendanceRecord.objects.filter(
            date__gte=first_day_of_month,
            status='late'
        ).values('user__first_name', 'user__last_name', 'user__department__name').annotate(
            late_count=Count('id')
        ).filter(late_count__gte=3).order_by('-late_count')
        
        context['chronic_late_users'] = chronic_late_users

    return render(request, 'attendance/dashboard.html', context)

@login_required
@require_http_methods(["POST"])
def check_in(request):
    """Record user check-in time."""
    today = timezone.now().date()
    now_time = timezone.localtime().time()
    
    record, created = AttendanceRecord.objects.get_or_create(
        user=request.user,
        date=today,
        defaults={'check_in': now_time}
    )
    
    if not created and record.check_in:
        messages.warning(request, 'You have already checked in today.')
    else:
        if not created:
            record.check_in = now_time
            
        # Determine Late Status from Site Configuration
        from .models import AttendanceConfiguration
        site_config = AttendanceConfiguration.objects.first()
        standard_start = site_config.office_start_time if site_config and site_config.office_start_time else datetime.time(9, 0)
        
        if now_time > standard_start:
            record.status = 'late'
            messages.warning(request, f'Checked in late at {now_time.strftime("%H:%M")}.')
        else:
            record.status = 'present'
            messages.success(request, f'Checked in successfully at {now_time.strftime("%H:%M")}!')
            
        record.save()
        
    return redirect('attendance-dashboard')

@login_required
@require_http_methods(["POST"])
def check_out(request):
    """Record user check-out time and calculate hours."""
    today = timezone.now().date()
    now_time = timezone.localtime().time()
    notes = request.POST.get('notes', '')
    
    record = AttendanceRecord.objects.filter(user=request.user, date=today).first()
    
    if not record or not record.check_in:
        messages.error(request, 'You must check in before you can check out.')
        return redirect('attendance-dashboard')
        
    if record.check_out:
        messages.warning(request, 'You have already checked out today.')
        return redirect('attendance-dashboard')
        
    record.check_out = now_time
    if notes:
        record.notes = notes
    
    # Calculate total hours
    record.calculate_hours()
    record.save()
    
    messages.success(request, f'Checked out successfully at {now_time.strftime("%H:%M")}. Total hours: {record.total_hours}')
    return redirect('attendance-dashboard')

from .forms import AttendanceConfigurationForm

def is_super_admin(user):
    return user.is_authenticated and hasattr(user, 'role') and user.role == 'super_admin'

@login_required
@user_passes_test(is_super_admin)
def attendance_settings_view(request):
    """View for updating attendance times."""
    from .models import AttendanceConfiguration
    config = AttendanceConfiguration.objects.first()
    if not config:
        config = AttendanceConfiguration.objects.create()

    if request.method == 'POST':
        form = AttendanceConfigurationForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Attendance policy updated successfully!")
            return redirect('attendance-settings')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AttendanceConfigurationForm(instance=config)

    return render(request, 'attendance/settings.html', {
        'form': form,
    })

@login_required
@require_http_methods(["GET"])
def export_attendance_xls(request):
    """Export currently filtered attendance records to CSV (can be opened in Excel)."""
    today = timezone.now().date()
    
    # Mirror the filtering logic exactly
    if request.user.role in ['admin', 'super_admin']:
        records_query = AttendanceRecord.objects.select_related('user', 'user__department')
    elif request.user.role == 'manager':
        from users.models import UserProfile
        team_ids = list(UserProfile.objects.filter(manager=request.user).values_list('user_id', flat=True))
        team_ids.append(request.user.id)
        records_query = AttendanceRecord.objects.filter(user_id__in=team_ids).select_related('user', 'user__department')
    else:
        records_query = AttendanceRecord.objects.filter(user=request.user).select_related('user')
        
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    try:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else today - datetime.timedelta(days=7)
    except ValueError:
        start_date = today - datetime.timedelta(days=7)
        
    try:
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else today
    except ValueError:
        end_date = today
        
    status_filter = request.GET.get('status', '')
    user_filter = request.GET.get('user_filter', 'all')
    
    if request.user.role in ['admin', 'super_admin', 'manager']:
        if user_filter == 'me':
            records_query = records_query.filter(user=request.user)
        elif user_filter != 'all' and user_filter.isdigit():
            records_query = records_query.filter(user_id=int(user_filter))
    
    filtered_records = records_query.filter(date__gte=start_date, date__lte=end_date)
    if status_filter:
        filtered_records = filtered_records.filter(status=status_filter)
        
    filtered_records = filtered_records.order_by('-date', '-check_in', 'user__first_name')
    
    # Generate CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_export_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['User ID', 'First Name', 'Last Name', 'Department', 'Date', 'Check In', 'Check Out', 'Status', 'Total Hours', 'Notes'])
    
    for record in filtered_records:
        writer.writerow([
            record.user.id,
            record.user.first_name,
            record.user.last_name,
            record.user.department.name if getattr(record.user, 'department', None) else 'Unassigned',
            record.date.strftime('%Y-%m-%d'),
            record.check_in.strftime('%H:%M') if record.check_in else '',
            record.check_out.strftime('%H:%M') if record.check_out else '',
            record.get_status_display(),
            record.total_hours,
            record.notes or ''
        ])
        
    return response
