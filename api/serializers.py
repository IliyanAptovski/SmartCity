from rest_framework import serializers
from users.models import User, UserProfile, Notification
from dashboard.models import Sensor, SensorReading, Anomaly, Incident, WaterConsumption
from reports.models import Report, ReportComment


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'role', 'date_joined']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'address', 'city', 'postal_code', 'avatar', 'bio', 'latitude', 'longitude']


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""
    
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'is_read', 'link', 'created_at']


class SensorSerializer(serializers.ModelSerializer):
    """Serializer for Sensor model."""
    
    sensor_type_display = serializers.CharField(source='get_sensor_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    status_color = serializers.CharField(read_only=True)
    
    class Meta:
        model = Sensor
        fields = [
            'id', 'name', 'sensor_type', 'sensor_type_display', 
            'status', 'status_display', 'status_color',
            'latitude', 'longitude', 'address', 'district',
            'min_value', 'max_value', 'threshold_warning', 'threshold_critical',
            'last_reading_at'
        ]


class SensorReadingSerializer(serializers.ModelSerializer):
    """Serializer for SensorReading model."""
    
    sensor_name = serializers.CharField(source='sensor.name', read_only=True)
    
    class Meta:
        model = SensorReading
        fields = ['id', 'sensor', 'sensor_name', 'value', 'unit', 'timestamp', 'is_anomaly', 'anomaly_score']


class AnomalySerializer(serializers.ModelSerializer):
    """Serializer for Anomaly model."""
    
    anomaly_type_display = serializers.CharField(source='get_anomaly_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    severity_color = serializers.CharField(read_only=True)
    sensor_name = serializers.CharField(source='sensor.name', read_only=True)
    
    class Meta:
        model = Anomaly
        fields = [
            'id', 'title', 'description', 'anomaly_type', 'anomaly_type_display',
            'severity', 'severity_display', 'severity_color',
            'status', 'status_display',
            'sensor', 'sensor_name', 'latitude', 'longitude',
            'detected_at', 'confidence', 'estimated_start', 'estimated_end',
            'estimated_affected_users'
        ]


class IncidentSerializer(serializers.ModelSerializer):
    """Serializer for Incident model."""
    
    incident_type_display = serializers.CharField(source='get_incident_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    status_color = serializers.CharField(read_only=True)
    
    class Meta:
        model = Incident
        fields = [
            'id', 'title', 'description', 'incident_type', 'incident_type_display',
            'status', 'status_display', 'status_color',
            'latitude', 'longitude', 'address', 'district',
            'affected_area_radius', 'reported_at', 'estimated_resolution',
            'affected_users', 'image'
        ]


class WaterConsumptionSerializer(serializers.ModelSerializer):
    """Serializer for WaterConsumption model."""
    
    class Meta:
        model = WaterConsumption
        fields = [
            'id', 'district', 'date', 'hour',
            'consumption_liters', 'avg_pressure', 'avg_quality_score'
        ]


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for Report model."""
    
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_color = serializers.CharField(read_only=True)
    reporter = serializers.CharField(source='get_reporter_display', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'title', 'description', 'category', 'category_display',
            'status', 'status_display', 'status_color',
            'priority', 'priority_display',
            'address', 'district', 'latitude', 'longitude',
            'image', 'created_at', 'reporter', 'estimated_start', 'estimated_end'
        ]


class ReportDetailSerializer(ReportSerializer):
    """Detailed serializer for Report model."""
    
    comments = serializers.SerializerMethodField()
    status_history = serializers.SerializerMethodField()
    
    class Meta(ReportSerializer.Meta):
        fields = ReportSerializer.Meta.fields + ['comments', 'status_history', 'notes']
    
    def get_comments(self, obj):
        comments = obj.comments.filter(is_internal=False)
        return [{'author': c.author.get_full_name(), 'content': c.content, 'created_at': c.created_at} for c in comments]
    
    def get_status_history(self, obj):
        history = obj.status_history.all()
        return [{'old_status': h.get_old_status_display(), 'new_status': h.get_new_status_display(), 'changed_by': h.changed_by.get_full_name() if h.changed_by else None, 'created_at': h.created_at} for h in history]


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics."""
    
    total_sensors = serializers.IntegerField()
    active_sensors = serializers.IntegerField()
    active_anomalies = serializers.IntegerField()
    critical_anomalies = serializers.IntegerField()
    ongoing_incidents = serializers.IntegerField()
    pending_reports = serializers.IntegerField()
