from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg, Sum

from users.models import User, Notification
from dashboard.models import Sensor, SensorReading, Anomaly, Incident, WaterConsumption
from reports.models import Report

from .serializers import (
    UserSerializer, UserProfileSerializer, NotificationSerializer,
    SensorSerializer, SensorReadingSerializer, AnomalySerializer,
    IncidentSerializer, WaterConsumptionSerializer,
    ReportSerializer, ReportDetailSerializer,
    DashboardStatsSerializer
)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for users."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class NotificationViewSet(viewsets.ModelViewSet):
    """API endpoint for notifications."""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return self.request.user.notifications.all()
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'marked as read'})


class SensorViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for sensors."""
    queryset = Sensor.objects.all()
    serializer_class = SensorSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def readings(self, request, pk=None):
        """Get recent readings for a sensor."""
        sensor = self.get_object()
        hours = int(request.query_params.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours)
        
        readings = sensor.readings.filter(timestamp__gte=since).order_by('-timestamp')
        serializer = SensorReadingSerializer(readings, many=True)
        return Response(serializer.data)


class AnomalyViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for anomalies."""
    queryset = Anomaly.objects.all()
    serializer_class = AnomalySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Anomaly.objects.all()
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        return queryset


class IncidentViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for incidents."""
    queryset = Incident.objects.filter(is_public=True)
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated]


class ReportViewSet(viewsets.ModelViewSet):
    """API endpoint for reports."""
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Report.objects.filter(is_public=True)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by district
        district = self.request.query_params.get('district')
        if district:
            queryset = queryset.filter(district__icontains=district)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ReportDetailSerializer
        return ReportSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics."""
    
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    
    stats = {
        'total_sensors': Sensor.objects.count(),
        'active_sensors': Sensor.objects.filter(status='active').count(),
        'active_anomalies': Anomaly.objects.filter(
            status__in=['detected', 'investigating', 'confirmed']
        ).count(),
        'critical_anomalies': Anomaly.objects.filter(
            status__in=['detected', 'investigating', 'confirmed'],
            severity='critical'
        ).count(),
        'ongoing_incidents': Incident.objects.filter(
            status__in=['reported', 'investigating', 'in_progress']
        ).count(),
        'pending_reports': Report.objects.filter(status='pending').count(),
        'predictions_24h': Prediction.objects.filter(
            prediction_made_at__gte=last_24h
        ).count(),
        'high_confidence_predictions': Prediction.objects.filter(
            confidence__gte=70
        ).count(),
    }
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def consumption_data(request):
    """Get consumption data for charts."""
    
    days = int(request.query_params.get('days', 7))
    since = timezone.now().date() - timedelta(days=days)
    
    data = WaterConsumption.objects.filter(
        date__gte=since
    ).values('date').annotate(
        total_consumption=Sum('consumption_liters')
    ).order_by('date')
    
    return Response(list(data))


@api_view(['GET'])
def map_data(request):
    """Get all data for map display."""
    
    sensors = Sensor.objects.filter(status='active')
    incidents = Incident.objects.filter(
        is_public=True,
        status__in=['reported', 'investigating', 'in_progress']
    )
    anomalies = Anomaly.objects.filter(
        status__in=['detected', 'investigating', 'confirmed']
    )
    
    data = {
        'sensors': SensorSerializer(sensors, many=True).data,
        'incidents': IncidentSerializer(incidents, many=True).data,
        'anomalies': AnomalySerializer(anomalies, many=True).data,
    }
    
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    """Mark all notifications as read."""
    
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return Response({'status': 'success'})
