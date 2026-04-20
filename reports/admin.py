from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Report, ReportComment, ReportStatusHistory


class ReportCommentInline(admin.TabularInline):
    """Inline admin for report comments."""
    model = ReportComment
    extra = 0
    readonly_fields = ['created_at']


class ReportStatusHistoryInline(admin.TabularInline):
    """Inline admin for report status history."""
    model = ReportStatusHistory
    extra = 0
    readonly_fields = ['created_at']
    can_delete = False


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Admin configuration for Report model."""
    
    list_display = [
        'title', 'category', 'status', 'priority', 
        'district', 'created_at', 'get_reporter_display'
    ]
    list_filter = ['category', 'status', 'priority', 'district', 'created_at', 'is_public']
    search_fields = ['title', 'description', 'address', 'reporter_email', 'user__email']
    list_editable = ['status', 'priority']
    date_hierarchy = 'created_at'
    inlines = [ReportCommentInline, ReportStatusHistoryInline]
    
    fieldsets = (
        (_('Подател'), {
            'fields': ('user', 'reporter_name', 'reporter_email', 'reporter_phone')
        }),
        (_('Детайли'), {
            'fields': ('title', 'category', 'description', 'status', 'priority')
        }),
        (_('Локация'), {
            'fields': ('address', 'district', 'latitude', 'longitude')
        }),
        (_('Вътрешно'), {
            'fields': ('notes', 'assigned_to', 'estimated_start', 'estimated_end')
        }),
        (_('Медия'), {
            'fields': ('image',)
        }),
        (_('Видимост'), {
            'fields': ('is_public',)
        }),
    )


@admin.register(ReportComment)
class ReportCommentAdmin(admin.ModelAdmin):
    """Admin configuration for ReportComment model."""
    
    list_display = ['report', 'author', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['report__title', 'author__email', 'content']


@admin.register(ReportStatusHistory)
class ReportStatusHistoryAdmin(admin.ModelAdmin):
    """Admin configuration for ReportStatusHistory model."""
    
    list_display = ['report', 'old_status', 'new_status', 'changed_by', 'created_at']
    list_filter = ['old_status', 'new_status', 'created_at']
    search_fields = ['report__title', 'changed_by__email']
    readonly_fields = ['created_at']
