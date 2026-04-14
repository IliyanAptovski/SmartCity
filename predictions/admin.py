from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Prediction, PredictionModel, AlertRule, ModelTrainingLog


class PredictionInline(admin.TabularInline):
    """Inline admin for predictions."""
    model = Prediction
    extra = 0
    readonly_fields = ['prediction_made_at', 'confidence']
    can_delete = False
    max_num = 5


class TrainingLogInline(admin.TabularInline):
    """Inline admin for training logs."""
    model = ModelTrainingLog
    extra = 0
    readonly_fields = ['started_at', 'completed_at', 'status']
    can_delete = False
    max_num = 5


@admin.register(PredictionModel)
class PredictionModelAdmin(admin.ModelAdmin):
    """Admin configuration for PredictionModel."""
    
    list_display = [
        'name', 'model_type', 'accuracy', 'is_active', 
        'is_default', 'training_date', 'created_at'
    ]
    list_filter = ['model_type', 'is_active', 'is_default', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'is_default']
    inlines = [PredictionInline, TrainingLogInline]
    
    fieldsets = (
        (_('Основна информация'), {
            'fields': ('name', 'model_type', 'description', 'model_file')
        }),
        (_('Метрики'), {
            'fields': ('accuracy', 'precision', 'recall', 'f1_score')
        }),
        (_('Обучение'), {
            'fields': ('training_date', 'training_data_size')
        }),
        (_('Статус'), {
            'fields': ('is_active', 'is_default')
        }),
    )


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    """Admin configuration for Prediction."""
    
    list_display = [
        'title', 'prediction_type', 'confidence', 'probability',
        'status', 'prediction_made_at', 'prediction_for_time'
    ]
    list_filter = ['prediction_type', 'status', 'prediction_made_at']
    search_fields = ['title', 'description', 'district']
    list_editable = ['status']
    date_hierarchy = 'prediction_made_at'
    
    fieldsets = (
        (_('Основна информация'), {
            'fields': ('title', 'description', 'prediction_type', 'model')
        }),
        (_('Прогноза'), {
            'fields': ('predicted_value', 'confidence', 'probability')
        }),
        (_('Време'), {
            'fields': ('prediction_made_at', 'prediction_for_time')
        }),
        (_('Локация'), {
            'fields': ('sensor', 'district')
        }),
        (_('Валидация'), {
            'fields': ('status', 'actual_value', 'validated_at', 'validation_notes')
        }),
        (_('Обяснимост'), {
            'fields': ('feature_importance',)
        }),
    )


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    """Admin configuration for AlertRule."""
    
    list_display = [
        'name', 'prediction_type', 'min_confidence', 
        'notify_users', 'notify_operators', 'is_active'
    ]
    list_filter = ['prediction_type', 'is_active']
    list_editable = ['is_active']


@admin.register(ModelTrainingLog)
class ModelTrainingLogAdmin(admin.ModelAdmin):
    """Admin configuration for ModelTrainingLog."""
    
    list_display = ['model', 'started_at', 'status', 'duration_display']
    list_filter = ['status', 'started_at']
    readonly_fields = ['started_at', 'completed_at']
    
    def duration_display(self, obj):
        duration = obj.duration()
        if duration:
            minutes = int(duration.total_seconds() / 60)
            return f'{minutes} мин'
        return '-'
    duration_display.short_description = _('Продължителност')
