from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class PredictionModel(models.Model):
    """ML models used for predictions."""
    
    MODEL_TYPES = [
        ('anomaly_detection', _('Откриване на аномалии')),
        ('consumption_forecast', _('Прогноза за консумация')),
        ('leak_detection', _('Откриване на течове')),
        ('pressure_prediction', _('Прогноза за налягане')),
        ('quality_prediction', _('Прогноза за качество')),
    ]
    
    name = models.CharField(_('име'), max_length=100)
    model_type = models.CharField(_('тип'), max_length=30, choices=MODEL_TYPES)
    description = models.TextField(_('описание'), blank=True)
    
    # Model file
    model_file = models.FileField(_('модел файл'), upload_to='ml_models/')
    
    # Performance metrics
    accuracy = models.FloatField(_('точност'), null=True, blank=True)
    precision = models.FloatField(_('прецизност'), null=True, blank=True)
    recall = models.FloatField(_('recall'), null=True, blank=True)
    f1_score = models.FloatField(_('F1 score'), null=True, blank=True)
    
    # Training info
    training_date = models.DateTimeField(_('дата на обучение'), null=True, blank=True)
    training_data_size = models.PositiveIntegerField(_('размер на данните за обучение'), null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(_('активен'), default=True)
    is_default = models.BooleanField(_('по подразбиране'), default=False)
    
    created_at = models.DateTimeField(_('създаден на'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновен на'), auto_now=True)
    
    class Meta:
        verbose_name = _('предсказващ модел')
        verbose_name_plural = _('предсказващи модели')
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.name} ({self.get_model_type_display()})'


class Prediction(models.Model):
    """Individual predictions made by ML models."""
    
    PREDICTION_TYPES = [
        ('anomaly', _('Аномалия')),
        ('consumption', _('Консумация')),
        ('leak', _('Теч')),
        ('pressure', _('Налягане')),
        ('quality', _('Качество')),
        ('maintenance', _('Поддръжка')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Чакаща')),
        ('confirmed', _('Потвърдена')),
        ('rejected', _('Отхвърлена')),
        ('expired', _('Изтекла')),
    ]
    
    title = models.CharField(_('заглавие'), max_length=200)
    description = models.TextField(_('описание'), blank=True)
    prediction_type = models.CharField(_('тип прогноза'), max_length=20, choices=PREDICTION_TYPES)
    
    # Model used
    model = models.ForeignKey(
        PredictionModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='predictions',
        verbose_name=_('модел')
    )
    
    # Prediction details
    predicted_value = models.FloatField(_('предсказана стойност'), null=True, blank=True)
    confidence = models.FloatField(_('увереност (%)'), help_text=_('Увереност на модела в процента'))
    probability = models.FloatField(_('вероятност (%)'), null=True, blank=True)
    
    # Time range
    prediction_made_at = models.DateTimeField(_('направена на'), default=timezone.now)
    prediction_for_time = models.DateTimeField(_('за време'), null=True, blank=True)
    
    # Location (optional)
    sensor = models.ForeignKey(
        'dashboard.Sensor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='predictions',
        verbose_name=_('сензор')
    )
    district = models.CharField(_('район'), max_length=100, blank=True)
    
    # Status
    status = models.CharField(_('статус'), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Validation
    actual_value = models.FloatField(_('реална стойност'), null=True, blank=True)
    validated_at = models.DateTimeField(_('валидирана на'), null=True, blank=True)
    validation_notes = models.TextField(_('бележки за валидация'), blank=True)
    
    # Feature importance (for explainability)
    feature_importance = models.JSONField(_('важност на характеристиките'), blank=True, null=True)
    
    created_at = models.DateTimeField(_('създадена на'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновена на'), auto_now=True)
    
    class Meta:
        verbose_name = _('прогноза')
        verbose_name_plural = _('прогнози')
        ordering = ['-prediction_made_at']
    
    def __str__(self):
        return f'{self.title} ({self.confidence:.1f}% увереност)'
    
    def get_confidence_color(self):
        """Get Bootstrap color class based on confidence."""
        if self.confidence >= 80:
            return 'success'
        elif self.confidence >= 60:
            return 'info'
        elif self.confidence >= 40:
            return 'warning'
        else:
            return 'danger'
    
    def get_status_color(self):
        """Get Bootstrap color class based on status."""
        colors = {
            'pending': 'warning',
            'confirmed': 'success',
            'rejected': 'danger',
            'expired': 'secondary',
        }
        return colors.get(self.status, 'secondary')
    
    def is_high_confidence(self):
        return self.confidence >= 70
    
    def validate(self, actual_value, notes=''):
        """Validate the prediction with actual value."""
        self.actual_value = actual_value
        self.validated_at = timezone.now()
        self.validation_notes = notes
        self.save()


class AlertRule(models.Model):
    """Rules for generating alerts based on predictions."""
    
    name = models.CharField(_('име'), max_length=100)
    description = models.TextField(_('описание'), blank=True)
    
    # Conditions
    prediction_type = models.CharField(_('тип прогноза'), max_length=20, choices=Prediction.PREDICTION_TYPES)
    min_confidence = models.FloatField(_('минимална увереност (%)'), default=50)
    min_probability = models.FloatField(_('минимална вероятност (%)'), default=50)
    
    # Actions
    notify_users = models.BooleanField(_('извести потребители'), default=True)
    notify_operators = models.BooleanField(_('извести оператори'), default=True)
    create_incident = models.BooleanField(_('създай инцидент'), default=False)
    
    # Notification message
    alert_title_template = models.CharField(_('шаблон за заглавие'), max_length=200, blank=True)
    alert_message_template = models.TextField(_('шаблон за съобщение'), blank=True)
    
    # Status
    is_active = models.BooleanField(_('активно'), default=True)
    
    created_at = models.DateTimeField(_('създадено на'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновено на'), auto_now=True)
    
    class Meta:
        verbose_name = _('правило за аларма')
        verbose_name_plural = _('правила за аларми')
    
    def __str__(self):
        return self.name


class ModelTrainingLog(models.Model):
    """Log of model training sessions."""
    
    model = models.ForeignKey(
        PredictionModel,
        on_delete=models.CASCADE,
        related_name='training_logs',
        verbose_name=_('модел')
    )
    
    started_at = models.DateTimeField(_('започнато на'), auto_now_add=True)
    completed_at = models.DateTimeField(_('завършено на'), null=True, blank=True)
    
    status = models.CharField(_('статус'), max_length=20, default='running')
    
    # Training parameters
    parameters = models.JSONField(_('параметри'), blank=True, null=True)
    
    # Results
    metrics = models.JSONField(_('метрики'), blank=True, null=True)
    error_message = models.TextField(_('съобщение за грешка'), blank=True)
    
    class Meta:
        verbose_name = _('лог за обучение')
        verbose_name_plural = _('логове за обучение')
        ordering = ['-started_at']
    
    def __str__(self):
        return f'Обучение на {self.model.name} - {self.started_at}'
    
    def duration(self):
        """Calculate training duration."""
        if self.completed_at:
            return self.completed_at - self.started_at
        return timezone.now() - self.started_at
