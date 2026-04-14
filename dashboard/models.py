from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import random


class Sensor(models.Model):
    """Water sensor model for monitoring infrastructure."""
    
    SENSOR_TYPES = [
        ('flow', _('Разходомер')),
        ('pressure', _('Налягане')),
        ('quality', _('Качество на водата')),
        ('level', _('Ниво на резервоар')),
        ('temperature', _('Температура')),
        ('leak', _('Детектор за теч')),
    ]
    
    STATUS_CHOICES = [
        ('active', _('Активен')),
        ('inactive', _('Неактивен')),
        ('maintenance', _('В поддръжка')),
        ('error', _('Грешка')),
    ]
    
    name = models.CharField(_('име'), max_length=100)
    sensor_type = models.CharField(_('тип'), max_length=20, choices=SENSOR_TYPES)
    status = models.CharField(_('статус'), max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Location
    latitude = models.DecimalField(_('географска ширина'), max_digits=10, decimal_places=8)
    longitude = models.DecimalField(_('географска дължина'), max_digits=11, decimal_places=8)
    address = models.CharField(_('адрес'), max_length=255, blank=True)
    district = models.CharField(_('район'), max_length=100, blank=True)
    
    # Configuration
    min_value = models.FloatField(_('минимална стойност'), default=0)
    max_value = models.FloatField(_('максимална стойност'), default=100)
    threshold_warning = models.FloatField(_('праг за предупреждение'), null=True, blank=True)
    threshold_critical = models.FloatField(_('критичен праг'), null=True, blank=True)
    
    # Metadata
    serial_number = models.CharField(_('сериен номер'), max_length=50, unique=True, blank=True)
    manufacturer = models.CharField(_('производител'), max_length=100, blank=True)
    installation_date = models.DateField(_('дата на инсталация'), null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('създаден на'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновен на'), auto_now=True)
    last_reading_at = models.DateTimeField(_('последно четене'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('сензор')
        verbose_name_plural = _('сензори')
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.name} ({self.get_sensor_type_display()})'
    
    def get_current_reading(self):
        """Get the most recent reading from this sensor."""
        return self.readings.first()
    
    def get_status_color(self):
        """Get Bootstrap color class based on status."""
        colors = {
            'active': 'success',
            'inactive': 'secondary',
            'maintenance': 'warning',
            'error': 'danger',
        }
        return colors.get(self.status, 'secondary')
    
    def is_in_warning_state(self):
        """Check if sensor is in warning state based on latest reading."""
        reading = self.get_current_reading()
        if reading and self.threshold_warning is not None:
            return reading.value >= self.threshold_warning
        return False
    
    def is_in_critical_state(self):
        """Check if sensor is in critical state based on latest reading."""
        reading = self.get_current_reading()
        if reading and self.threshold_critical is not None:
            return reading.value >= self.threshold_critical
        return False


class SensorReading(models.Model):
    """Individual sensor reading."""
    
    sensor = models.ForeignKey(
        Sensor,
        on_delete=models.CASCADE,
        related_name='readings',
        verbose_name=_('сензор')
    )
    value = models.FloatField(_('стойност'))
    unit = models.CharField(_('мерна единица'), max_length=20, blank=True)
    timestamp = models.DateTimeField(_('време'), default=timezone.now)
    
    # Quality indicators
    is_anomaly = models.BooleanField(_('аномалия'), default=False)
    anomaly_score = models.FloatField(_('аномален резултат'), null=True, blank=True)
    
    # Raw data for ML
    raw_data = models.JSONField(_('сурови данни'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('измерване')
        verbose_name_plural = _('измервания')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['sensor', '-timestamp']),
            models.Index(fields=['is_anomaly']),
        ]
    
    def __str__(self):
        return f'{self.sensor.name}: {self.value} {self.unit} at {self.timestamp}'


class Anomaly(models.Model):
    """Detected anomalies in the water infrastructure."""
    
    SEVERITY_CHOICES = [
        ('low', _('Ниска')),
        ('medium', _('Средна')),
        ('high', _('Висока')),
        ('critical', _('Критична')),
    ]
    
    STATUS_CHOICES = [
        ('detected', _('Открита')),
        ('investigating', _('В проверка')),
        ('confirmed', _('Потвърдена')),
        ('resolved', _('Разрешена')),
        ('false_positive', _('Фалшива тревога')),
    ]
    
    ANOMALY_TYPES = [
        ('leak', _('Теч')),
        ('pressure_drop', _('Спад на налягане')),
        ('pressure_spike', _('Скок на налягане')),
        ('quality_issue', _('Проблем с качеството')),
        ('high_consumption', _('Висока консумация')),
        ('low_consumption', _('Ниска консумация')),
        ('sensor_malfunction', _('Неизправност на сензор')),
        ('other', _('Друго')),
    ]
    
    title = models.CharField(_('заглавие'), max_length=200)
    description = models.TextField(_('описание'), blank=True)
    anomaly_type = models.CharField(_('тип аномалия'), max_length=30, choices=ANOMALY_TYPES)
    severity = models.CharField(_('тежест'), max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(_('статус'), max_length=20, choices=STATUS_CHOICES, default='detected')
    
    # Location
    sensor = models.ForeignKey(
        Sensor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='anomalies',
        verbose_name=_('сензор')
    )
    latitude = models.DecimalField(_('географска ширина'), max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(_('географска дължина'), max_digits=11, decimal_places=8, null=True, blank=True)
    affected_area = models.FloatField(_('засегната площ (кв.м)'), null=True, blank=True)
    
    # Detection info
    detected_at = models.DateTimeField(_('открита на'), default=timezone.now)
    confidence = models.FloatField(_('увереност (%)'), help_text=_('ML увереност в процента'))
    
    # Resolution info
    resolved_at = models.DateTimeField(_('разрешена на'), null=True, blank=True)
    resolved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_anomalies',
        verbose_name=_('разрешена от')
    )
    resolution_notes = models.TextField(_('бележки за разрешаване'), blank=True)
    
    # Estimated impact
    estimated_start = models.DateTimeField(_('прогнозно начало'), null=True, blank=True)
    estimated_end = models.DateTimeField(_('прогнозен край'), null=True, blank=True)
    estimated_affected_users = models.PositiveIntegerField(_('засегнати потребители'), default=0)
    
    created_at = models.DateTimeField(_('създадена на'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновена на'), auto_now=True)
    
    class Meta:
        verbose_name = _('аномалия')
        verbose_name_plural = _('аномалии')
        ordering = ['-detected_at']
    
    def __str__(self):
        return f'{self.title} ({self.get_severity_display()})'
    
    def get_severity_color(self):
        """Get Bootstrap color class based on severity."""
        colors = {
            'low': 'info',
            'medium': 'warning',
            'high': 'danger',
            'critical': 'dark',
        }
        return colors.get(self.severity, 'secondary')
    
    def get_status_color(self):
        """Get Bootstrap color class based on status."""
        colors = {
            'detected': 'danger',
            'investigating': 'warning',
            'confirmed': 'danger',
            'resolved': 'success',
            'false_positive': 'secondary',
        }
        return colors.get(self.status, 'secondary')
    
    def is_resolved(self):
        return self.status == 'resolved'
    
    def duration(self):
        """Calculate duration of the anomaly."""
        if self.resolved_at:
            return self.resolved_at - self.detected_at
        return timezone.now() - self.detected_at


class WaterConsumption(models.Model):
    """Aggregated water consumption data."""
    
    district = models.CharField(_('район'), max_length=100)
    date = models.DateField(_('дата'))
    hour = models.PositiveSmallIntegerField(_('час'), default=0)
    
    consumption_liters = models.FloatField(_('консумация (литри)'))
    avg_pressure = models.FloatField(_('средно налягане'), null=True, blank=True)
    avg_quality_score = models.FloatField(_('среден коефициент на качество'), null=True, blank=True)
    
    # Statistics
    min_consumption = models.FloatField(_('минимална консумация'), null=True, blank=True)
    max_consumption = models.FloatField(_('максимална консумация'), null=True, blank=True)
    std_deviation = models.FloatField(_('стандартно отклонение'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('създадено на'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('консумация на вода')
        verbose_name_plural = _('консумация на вода')
        ordering = ['-date', '-hour']
        unique_together = ['district', 'date', 'hour']
    
    def __str__(self):
        return f'{self.district} - {self.date} {self.hour}:00 - {self.consumption_liters}L'


class Incident(models.Model):
    """Major incidents and outages."""
    
    INCIDENT_TYPES = [
        ('burst_pipe', _('Спукана тръба')),
        ('major_leak', _('Голям теч')),
        ('pump_failure', _('Неизправност на помпа')),
        ('contamination', _('Замърсяване')),
        ('maintenance', _('Планирана поддръжка')),
        ('power_outage', _('Прекъсване на тока')),
        ('other', _('Друго')),
    ]
    
    STATUS_CHOICES = [
        ('reported', _('Докладван')),
        ('investigating', _('В проверка')),
        ('in_progress', _('В процес на отстраняване')),
        ('resolved', _('Разрешен')),
        ('cancelled', _('Отменен')),
    ]
    
    title = models.CharField(_('заглавие'), max_length=200)
    description = models.TextField(_('описание'))
    incident_type = models.CharField(_('тип инцидент'), max_length=20, choices=INCIDENT_TYPES)
    status = models.CharField(_('статус'), max_length=20, choices=STATUS_CHOICES, default='reported')
    
    # Location
    latitude = models.DecimalField(_('географска ширина'), max_digits=10, decimal_places=8)
    longitude = models.DecimalField(_('географска дължина'), max_digits=11, decimal_places=8)
    address = models.CharField(_('адрес'), max_length=255)
    district = models.CharField(_('район'), max_length=100)
    affected_area_radius = models.FloatField(_('радиус на засегнатата зона (м)'), default=500)
    
    # Timeline
    reported_at = models.DateTimeField(_('докладван на'), default=timezone.now)
    started_at = models.DateTimeField(_('започнал на'), null=True, blank=True)
    estimated_resolution = models.DateTimeField(_('прогнозно разрешаване'), null=True, blank=True)
    resolved_at = models.DateTimeField(_('разрешен на'), null=True, blank=True)
    
    # Impact
    affected_users = models.PositiveIntegerField(_('засегнати потребители'), default=0)
    estimated_cost = models.DecimalField(_('прогнозна стойност'), max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Reporter
    reported_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reported_incidents',
        verbose_name=_('докладван от')
    )
    
    # Assigned team
    assigned_to = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_incidents',
        verbose_name=_('възложен на')
    )
    
    # Media
    image = models.FileField(_('снимка'), upload_to='incidents/', blank=True, null=True)
    
    # Visibility
    is_public = models.BooleanField(_('публичен'), default=True)
    is_featured = models.BooleanField(_('избран'), default=False)
    
    created_at = models.DateTimeField(_('създаден на'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновен на'), auto_now=True)
    
    class Meta:
        verbose_name = _('инцидент')
        verbose_name_plural = _('инциденти')
        ordering = ['-reported_at']
    
    def __str__(self):
        return self.title
    
    def get_status_color(self):
        colors = {
            'reported': 'danger',
            'investigating': 'warning',
            'in_progress': 'primary',
            'resolved': 'success',
            'cancelled': 'secondary',
        }
        return colors.get(self.status, 'secondary')
    
    def is_ongoing(self):
        return self.status in ['reported', 'investigating', 'in_progress']
