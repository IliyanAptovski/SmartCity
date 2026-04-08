from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile, Notification


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = _('Профил')
    fk_name = 'user'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for User model."""
    
    inlines = [UserProfileInline]
    
    list_display = [
        'email', 'first_name', 'last_name', 'role', 
        'is_active', 'is_staff', 'date_joined', 'last_login'
    ]
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Лична информация'), {'fields': ('first_name', 'last_name', 'phone')}),
        (_('Права'), {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Важни дати'), {'fields': ('last_login', 'date_joined')}),
        (_('Известия'), {'fields': ('email_notifications', 'sms_notifications', 'push_notifications')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'role'),
        }),
    )
    
    readonly_fields = ['last_login', 'date_joined']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for UserProfile model."""
    
    list_display = ['user', 'city', 'created_at', 'updated_at']
    list_filter = ['city', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'city']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin configuration for Notification model."""
    
    list_display = ['title', 'user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__email']
    readonly_fields = ['created_at', 'read_at']
    date_hierarchy = 'created_at'
