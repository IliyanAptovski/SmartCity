from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse


class Report(models.Model):
    """User-submitted reports for water infrastructure issues."""
    
    CATEGORY_CHOICES = [
        ('leak', _('Теч')),
        ('burst_pipe', _('Спукана тръба')),
        ('pressure_low', _('Ниско налягане')),
        ('pressure_high', _('Високо налягане')),
        ('water_quality', _('Качество на водата')),
        ('no_water', _('Няма вода')),
        ('sewage', _('Канализационен проблем')),
        ('hydrant', _('Пожарен хидрант')),
        ('meter', _('Водомер')),
        ('other', _('Друго')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Чакащ')),
        ('investigating', _('В проверка')),
        ('confirmed', _('Потвърден')),
        ('in_progress', _('В процес')),
        ('resolved', _('Разрешен')),
        ('rejected', _('Отхвърлен')),
    ]
    
    PRIORITY_CHOICES = [
        ('low', _('Нисък')),
        ('medium', _('Среден')),
        ('high', _('Висок')),
        ('urgent', _('Спешен')),
    ]
    
    # Reporter info
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_('потребител'),
        null=True,
        blank=True
    )
    
    # For anonymous reports
    reporter_name = models.CharField(_('име на подател'), max_length=150, blank=True)
    reporter_email = models.EmailField(_('имейл на подател'), blank=True)
    reporter_phone = models.CharField(_('телефон на подател'), max_length=20, blank=True)
    
    # Report details
    title = models.CharField(_('заглавие'), max_length=200)
    description = models.TextField(_('описание'))
    category = models.CharField(_('категория'), max_length=20, choices=CATEGORY_CHOICES)
    status = models.CharField(_('статус'), max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(_('приоритет'), max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Location
    address = models.CharField(_('адрес'), max_length=255)
    district = models.CharField(_('район'), max_length=100, blank=True)
    latitude = models.DecimalField(
        _('географска ширина'),
        max_digits=10,
        decimal_places=8,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        _('географска дължина'),
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True
    )
    
    # Media
    image = models.FileField(_('снимка'), upload_to='reports/', blank=True, null=True)
    
    # Internal fields
    notes = models.TextField(_('вътрешни бележки'), blank=True)
    assigned_to = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_reports',
        verbose_name=_('възложен на')
    )
    
    # Estimated resolution time
    estimated_start = models.DateTimeField(_('прогнозно начало'), null=True, blank=True)
    estimated_end = models.DateTimeField(_('прогнозен край'), null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('създаден на'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновен на'), auto_now=True)
    resolved_at = models.DateTimeField(_('разрешен на'), null=True, blank=True)
    
    # Visibility
    is_public = models.BooleanField(_('публичен'), default=True)
    
    class Meta:
        verbose_name = _('сигнал')
        verbose_name_plural = _('сигнали')
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.title} ({self.get_category_display()})'
    
    def get_absolute_url(self):
        return reverse('reports:detail', kwargs={'pk': self.pk})
    
    def get_status_color(self):
        """Get Bootstrap color class based on status."""
        colors = {
            'pending': 'warning',
            'investigating': 'info',
            'confirmed': 'primary',
            'in_progress': 'primary',
            'resolved': 'success',
            'rejected': 'secondary',
        }
        return colors.get(self.status, 'secondary')
    
    def get_priority_color(self):
        """Get Bootstrap color class based on priority."""
        colors = {
            'low': 'success',
            'medium': 'info',
            'high': 'warning',
            'urgent': 'danger',
        }
        return colors.get(self.priority, 'secondary')
    
    def is_resolved(self):
        return self.status == 'resolved'
    
    def is_rejected(self):
        return self.status == 'rejected'
    
    def can_be_edited(self):
        return self.status in ['pending', 'investigating']
    
    def get_reporter_display(self):
        """Get display name of the reporter."""
        if self.user:
            return self.user.get_full_name() or self.user.email
        return self.reporter_name or _('Анонимен')
    
    def save(self, *args, **kwargs):
        # Auto-set resolved_at when status changes to resolved
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)


class ReportComment(models.Model):
    """Comments on reports for internal communication."""
    
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('сигнал')
    )
    author = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='report_comments',
        verbose_name=_('автор')
    )
    content = models.TextField(_('съдържание'))
    is_internal = models.BooleanField(
        _('вътрешен коментар'),
        default=True,
        help_text=_('Вътрешните коментари не се показват на подателя на сигнала')
    )
    created_at = models.DateTimeField(_('създаден на'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновен на'), auto_now=True)
    
    class Meta:
        verbose_name = _('коментар')
        verbose_name_plural = _('коментари')
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Коментар на {self.author.email} за {self.report.title}'


class ReportStatusHistory(models.Model):
    """History of status changes for reports."""
    
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name=_('сигнал')
    )
    old_status = models.CharField(_('стар статус'), max_length=20, choices=Report.STATUS_CHOICES)
    new_status = models.CharField(_('нов статус'), max_length=20, choices=Report.STATUS_CHOICES)
    changed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('променен от')
    )
    comment = models.TextField(_('коментар'), blank=True)
    created_at = models.DateTimeField(_('създаден на'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('история на статус')
        verbose_name_plural = _('история на статуси')
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.report.title}: {self.get_old_status_display()} -> {self.get_new_status_display()}'
