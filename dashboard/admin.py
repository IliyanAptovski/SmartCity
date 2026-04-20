from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Sensor, SensorReading, Anomaly, WaterConsumption, Incident


class SensorReadingInline(admin.TabularInline):
    """Inline admin for sensor readings."""
    model = SensorReading
    extra = 0
    readonly_fields = ['timestamp', 'value', 'unit', 'is_anomaly']
    can_delete = False
    max_num = 10


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    """Admin configuration for Sensor model."""
    
    list_display = [
        'name', 'sensor_type', 'status', 'district', 
        'last_reading_at', 'created_at'
    ]
    list_filter = ['sensor_type', 'status', 'district', 'created_at']
    search_fields = ['name', 'address', 'district', 'serial_number']
    list_editable = ['status']
    inlines = [SensorReadingInline]
    
    fieldsets = (
        (_('Основна информация'), {
            'fields': ('name', 'sensor_type', 'status', 'serial_number', 'manufacturer')
        }),
        (_('Локация'), {
            'fields': ('latitude', 'longitude', 'address', 'district')
        }),
        (_('Конфигурация'), {
            'fields': ('min_value', 'max_value', 'threshold_warning', 'threshold_critical')
        }),
        (_('Дати'), {
            'fields': ('installation_date', 'last_reading_at')
        }),
    )


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    """Admin configuration for SensorReading model."""
    
    list_display = ['sensor', 'value', 'unit', 'timestamp', 'is_anomaly']
    list_filter = ['is_anomaly', 'timestamp', 'sensor__sensor_type']
    search_fields = ['sensor__name', 'sensor__address']
    date_hierarchy = 'timestamp'
    readonly_fields = ['timestamp']


@admin.register(Anomaly)
class AnomalyAdmin(admin.ModelAdmin):
    """Admin configuration for Anomaly model."""
    
    list_display = [
        'title', 'anomaly_type', 'severity', 'status', 
        'sensor', 'detected_at', 'confidence'
    ]
    list_filter = ['severity', 'status', 'anomaly_type', 'detected_at']
    search_fields = ['title', 'description', 'sensor__name']
    list_editable = ['status', 'severity']
    date_hierarchy = 'detected_at'
    
    fieldsets = (
        (_('Основна информация'), {
            'fields': ('title', 'description', 'anomaly_type', 'severity', 'status')
        }),
        (_('Локация'), {
            'fields': ('sensor', 'latitude', 'longitude', 'affected_area')
        }),
        (_('Откриване'), {
            'fields': ('detected_at', 'confidence')
        }),
        (_('Разрешаване'), {
            'fields': ('resolved_at', 'resolved_by', 'resolution_notes')
        }),
        (_('Прогнози'), {
            'fields': ('estimated_start', 'estimated_end', 'estimated_affected_users')
        }),
    )


@admin.register(WaterConsumption)
class WaterConsumptionAdmin(admin.ModelAdmin):
    """Admin configuration for WaterConsumption model."""
    
    list_display = [
        'district', 'date', 'hour', 'consumption_liters', 
        'avg_pressure', 'avg_quality_score'
    ]
    list_filter = ['district', 'date']
    search_fields = ['district']
    date_hierarchy = 'date'


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    """Admin configuration for Incident model."""
    
    list_display = [
        'title', 'incident_type', 'status', 'district',
        'reported_at', 'affected_users', 'is_public'
    ]
    list_filter = ['incident_type', 'status', 'district', 'reported_at', 'is_public']
    search_fields = ['title', 'description', 'address']
    list_editable = ['status', 'is_public']
    date_hierarchy = 'reported_at'
    
    fieldsets = (
        (_('Основна информация'), {
            'fields': ('title', 'description', 'incident_type', 'status', 'is_public', 'is_featured')
        }),
        (_('Локация'), {
            'fields': ('latitude', 'longitude', 'address', 'district', 'affected_area_radius')
        }),
        (_('Времева линия'), {
            'fields': ('reported_at', 'started_at', 'estimated_resolution', 'resolved_at')
        }),
        (_('Въздействие'), {
            'fields': ('affected_users', 'estimated_cost')
        }),
        (_('Отговорници'), {
            'fields': ('reported_by', 'assigned_to')
        }),
        (_('Медия'), {
            'fields': ('image',)
        }),
    )
