from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model with email as the primary identifier."""
    
    ROLE_CHOICES = [
        ('citizen', _('Гражданин')),
        ('operator', _('Оператор')),
        ('technician', _('Техник')),
        ('admin', _('Администратор')),
    ]
    
    email = models.EmailField(
        _('имейл адрес'),
        unique=True,
        help_text=_('Задължително. Валиден имейл адрес.')
    )
    first_name = models.CharField(_('име'), max_length=150, blank=True)
    last_name = models.CharField(_('фамилия'), max_length=150, blank=True)
    phone = models.CharField(_('телефон'), max_length=20, blank=True)
    
    role = models.CharField(
        _('роля'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='citizen'
    )
    
    is_staff = models.BooleanField(
        _('staff статус'),
        default=False,
        help_text=_('Определя дали потребителят може да влиза в админ панела.')
    )
    is_active = models.BooleanField(
        _('активен'),
        default=True,
        help_text=_('Определя дали потребителят е активен.')
    )
    date_joined = models.DateTimeField(_('дата на регистрация'), default=timezone.now)
    last_login = models.DateTimeField(_('последно влизане'), blank=True, null=True)
    
    # Notification preferences
    email_notifications = models.BooleanField(
        _('имейл известия'),
        default=True,
        help_text=_('Получаване на известия по имейл')
    )
    sms_notifications = models.BooleanField(
        _('SMS известия'),
        default=False,
        help_text=_('Получаване на SMS известия')
    )
    push_notifications = models.BooleanField(
        _('push известия'),
        default=True,
        help_text=_('Получаване на push известия')
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = _('потребител')
        verbose_name_plural = _('потребители')
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the full name of the user."""
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip() or self.email
    
    def get_short_name(self):
        """Return the short name of the user."""
        return self.first_name or self.email
    
    def get_role_display_name(self):
        """Return the display name of the user's role."""
        return dict(self.ROLE_CHOICES).get(self.role, self.role)
    
    def is_citizen(self):
        return self.role == 'citizen'
    
    def is_operator(self):
        return self.role == 'operator'
    
    def is_technician(self):
        return self.role == 'technician'
    
    def is_admin_role(self):
        return self.role == 'admin'


class UserProfile(models.Model):
    """Extended user profile with additional information."""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('потребител')
    )
    address = models.CharField(_('адрес'), max_length=255, blank=True)
    city = models.CharField(_('град'), max_length=100, blank=True)
    postal_code = models.CharField(_('пощенски код'), max_length=10, blank=True)
    avatar = models.FileField(
        _('аватар'),
        upload_to='avatars/',
        blank=True,
        null=True
    )
    bio = models.TextField(_('биография'), blank=True)
    
    # Location for map display
    latitude = models.DecimalField(
        _('географска ширина'),
        max_digits=10,
        decimal_places=8,
        blank=True,
        null=True
    )
    longitude = models.DecimalField(
        _('географска дължина'),
        max_digits=11,
        decimal_places=8,
        blank=True,
        null=True
    )
    
    created_at = models.DateTimeField(_('създаден на'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновен на'), auto_now=True)
    
    class Meta:
        verbose_name = _('потребителски профил')
        verbose_name_plural = _('потребителски профили')
    
    def __str__(self):
        return f'Профил на {self.user.email}'


class Notification(models.Model):
    """User notifications for alerts and updates."""
    
    NOTIFICATION_TYPES = [
        ('info', _('Информация')),
        ('warning', _('Предупреждение')),
        ('alert', _('Тревога')),
        ('success', _('Успех')),
        ('error', _('Грешка')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('потребител')
    )
    title = models.CharField(_('заглавие'), max_length=200)
    message = models.TextField(_('съобщение'))
    notification_type = models.CharField(
        _('тип известие'),
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='info'
    )
    is_read = models.BooleanField(_('прочетено'), default=False)
    link = models.URLField(_('връзка'), blank=True)
    created_at = models.DateTimeField(_('създадено на'), auto_now_add=True)
    read_at = models.DateTimeField(_('прочетено на'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('известие')
        verbose_name_plural = _('известия')
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.title} - {self.user.email}'
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
