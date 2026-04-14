from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import Report, ReportComment, ReportStatusHistory
from .forms import ReportForm, ReportUpdateForm, ReportCommentForm, ReportSearchForm


def report_list(request):
    """List all public reports with filtering."""
    
    reports = Report.objects.filter(is_public=True)
    
    # Apply filters
    form = ReportSearchForm(request.GET)
    if form.is_valid():
        search = form.cleaned_data.get('search')
        category = form.cleaned_data.get('category')
        status = form.cleaned_data.get('status')
        district = form.cleaned_data.get('district')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if search:
            reports = reports.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(address__icontains=search)
            )
        
        if category:
            reports = reports.filter(category=category)
        
        if status:
            reports = reports.filter(status=status)
        
        if district:
            reports = reports.filter(district__icontains=district)
        
        if date_from:
            reports = reports.filter(created_at__date__gte=date_from)
        
        if date_to:
            reports = reports.filter(created_at__date__lte=date_to)
    
    # Order by date
    reports = reports.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(reports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_reports': reports.count(),
    }
    
    return render(request, 'reports/report_list.html', context)


def report_detail(request, pk):
    """Detailed view for a single report."""
    
    report = get_object_or_404(Report, pk=pk, is_public=True)
    comments = report.comments.filter(is_internal=False)
    status_history = report.status_history.all()
    
    context = {
        'report': report,
        'comments': comments,
        'status_history': status_history,
    }
    
    return render(request, 'reports/report_detail.html', context)


def report_create(request):
    """Create a new report."""
    
    if request.method == 'POST':
        form = ReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            
            # Set user if authenticated
            if request.user.is_authenticated:
                report.user = request.user
                # Clear anonymous fields
                report.reporter_name = ''
                report.reporter_email = ''
                report.reporter_phone = ''
            
            report.save()
            
            # Create status history entry
            ReportStatusHistory.objects.create(
                report=report,
                old_status='pending',
                new_status='pending',
                comment=_('Сигналът е създаден')
            )
            
            # Send notification to user if authenticated
            if request.user.is_authenticated:
                from users.models import Notification
                Notification.objects.create(
                    user=request.user,
                    title=_('Сигналът е изпратен успешно'),
                    message=_(f'Вашият сигнал "{report.title}" е получен и ще бъде разгледан.'),
                    notification_type='success',
                    link=f'/reports/{report.pk}/'
                )
            
            messages.success(request, _('Сигналът е изпратен успешно! Благодарим ви!'))
            return redirect('reports:detail', pk=report.pk)
    else:
        form = ReportForm()
    
    context = {
        'form': form,
        'categories': Report.CATEGORY_CHOICES,
    }
    
    return render(request, 'reports/report_form.html', context)


@login_required
def my_reports(request):
    """List reports submitted by the current user."""
    
    reports = Report.objects.filter(user=request.user).order_by('-created_at')
    
    # Statistics
    stats = {
        'total': reports.count(),
        'pending': reports.filter(status='pending').count(),
        'in_progress': reports.filter(status__in=['investigating', 'confirmed', 'in_progress']).count(),
        'resolved': reports.filter(status='resolved').count(),
    }
    
    context = {
        'reports': reports,
        'stats': stats,
    }
    
    return render(request, 'reports/my_reports.html', context)


@login_required
def report_edit(request, pk):
    """Edit an existing report (only for the owner and only if not resolved)."""
    
    report = get_object_or_404(Report, pk=pk)
    
    # Check permissions
    if report.user != request.user and not request.user.is_staff:
        messages.error(request, _('Нямате права да редактирате този сигнал.'))
        return redirect('reports:detail', pk=pk)
    
    # Check if can be edited
    if not report.can_be_edited():
        messages.error(request, _('Този сигнал вече не може да бъде редактиран.'))
        return redirect('reports:detail', pk=pk)
    
    if request.method == 'POST':
        form = ReportForm(request.POST, request.FILES, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, _('Сигналът е обновен успешно!'))
            return redirect('reports:detail', pk=pk)
    else:
        form = ReportForm(instance=report)
    
    context = {
        'form': form,
        'report': report,
        'is_edit': True,
    }
    
    return render(request, 'reports/report_form.html', context)


# Staff views
@login_required
def staff_report_list(request):
    """List all reports for staff members."""
    
    # Check if user is staff
    if not (request.user.is_staff or request.user.is_operator() or request.user.is_admin_role()):
        messages.error(request, _('Нямате достъп до тази страница.'))
        return redirect('dashboard:index')
    
    reports = Report.objects.all()
    
    # Apply filters
    form = ReportSearchForm(request.GET)
    if form.is_valid():
        search = form.cleaned_data.get('search')
        category = form.cleaned_data.get('category')
        status = form.cleaned_data.get('status')
        district = form.cleaned_data.get('district')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if search:
            reports = reports.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(address__icontains=search)
            )
        
        if category:
            reports = reports.filter(category=category)
        
        if status:
            reports = reports.filter(status=status)
        
        if district:
            reports = reports.filter(district__icontains=district)
        
        if date_from:
            reports = reports.filter(created_at__date__gte=date_from)
        
        if date_to:
            reports = reports.filter(created_at__date__lte=date_to)
    
    # Order by priority and date
    reports = reports.order_by('priority', '-created_at')
    
    # Pagination
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total': Report.objects.count(),
        'pending': Report.objects.filter(status='pending').count(),
        'investigating': Report.objects.filter(status='investigating').count(),
        'in_progress': Report.objects.filter(status='in_progress').count(),
        'resolved_today': Report.objects.filter(
            status='resolved',
            resolved_at__date__gte=timezone.now().date()
        ).count(),
    }
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'stats': stats,
    }
    
    return render(request, 'reports/staff_report_list.html', context)


@login_required
def staff_report_detail(request, pk):
    """Detailed view for staff members with all comments."""
    
    # Check if user is staff
    if not (request.user.is_staff or request.user.is_operator() or request.user.is_admin_role()):
        messages.error(request, _('Нямате достъп до тази страница.'))
        return redirect('reports:detail', pk=pk)
    
    report = get_object_or_404(Report, pk=pk)
    comments = report.comments.all()
    status_history = report.status_history.all()
    
    if request.method == 'POST':
        comment_form = ReportCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.report = report
            comment.author = request.user
            comment.save()
            messages.success(request, _('Коментарът е добавен.'))
            return redirect('reports:staff_detail', pk=pk)
    else:
        comment_form = ReportCommentForm()
    
    context = {
        'report': report,
        'comments': comments,
        'status_history': status_history,
        'comment_form': comment_form,
        'update_form': ReportUpdateForm(instance=report),
    }
    
    return render(request, 'reports/staff_report_detail.html', context)


@login_required
def staff_report_update(request, pk):
    """Update report status and details (staff only)."""
    
    # Check if user is staff
    if not (request.user.is_staff or request.user.is_operator() or request.user.is_admin_role()):
        messages.error(request, _('Нямате достъп до тази страница.'))
        return redirect('reports:detail', pk=pk)
    
    report = get_object_or_404(Report, pk=pk)
    
    if request.method == 'POST':
        old_status = report.status
        form = ReportUpdateForm(request.POST, instance=report)
        if form.is_valid():
            report = form.save()
            
            # Create status history if status changed
            if old_status != report.status:
                ReportStatusHistory.objects.create(
                    report=report,
                    old_status=old_status,
                    new_status=report.status,
                    changed_by=request.user,
                    comment=form.cleaned_data.get('notes', '')
                )
                
                # Notify user if report has an associated user
                if report.user:
                    from users.models import Notification
                    status_display = dict(Report.STATUS_CHOICES).get(report.status)
                    Notification.objects.create(
                        user=report.user,
                        title=_(f'Статусът на сигнала е променен'),
                        message=_(f'Сигналът "{report.title}" вече е със статус: {status_display}'),
                        notification_type='info',
                        link=f'/reports/{report.pk}/'
                    )
            
            messages.success(request, _('Сигналът е обновен успешно!'))
            return redirect('reports:staff_detail', pk=pk)
    
    return redirect('reports:staff_detail', pk=pk)


# API endpoints
@require_http_methods(['GET'])
def api_report_stats(request):
    """API endpoint to get report statistics."""
    
    data = {
        'total': Report.objects.filter(is_public=True).count(),
        'pending': Report.objects.filter(status='pending').count(),
        'in_progress': Report.objects.filter(status__in=['investigating', 'in_progress']).count(),
        'resolved': Report.objects.filter(status='resolved').count(),
        'by_category': list(Report.objects.values('category').annotate(
            count=__import__('django.db.models').db.models.Count('id')
        )),
    }
    
    return JsonResponse(data)
