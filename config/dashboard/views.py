from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Sum, Max, Min
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import Sensor, SensorReading, Anomaly, WaterConsumption, Incident
from reports.models import Report


def index(request):
    """Main dashboard view with overview statistics."""
    
    # Get current time
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    
    # Statistics
    context = {
        # Sensor statistics
        'total_sensors': Sensor.objects.count(),
        'active_sensors': Sensor.objects.filter(status='active').count(),
        'sensors_in_maintenance': Sensor.objects.filter(status='maintenance').count(),
        'sensors_with_errors': Sensor.objects.filter(status='error').count(),
        
        # Anomaly statistics
        'total_anomalies': Anomaly.objects.count(),
        'active_anomalies': Anomaly.objects.filter(status__in=['detected', 'investigating', 'confirmed']).count(),
        'critical_anomalies': Anomaly.objects.filter(
            status__in=['detected', 'investigating', 'confirmed'],
            severity='critical'
        ).count(),
        'anomalies_last_24h': Anomaly.objects.filter(detected_at__gte=last_24h).count(),
        
        # Recent anomalies
        'recent_anomalies': Anomaly.objects.filter(
            status__in=['detected', 'investigating', 'confirmed']
        ).select_related('sensor')[:5],
        
        # Featured incidents
        'featured_incidents': Incident.objects.filter(
            is_public=True,
            is_featured=True,
            status__in=['reported', 'investigating', 'in_progress']
        )[:3],
        
        # Recent public incidents
        'recent_incidents': Incident.objects.filter(
            is_public=True,
            status__in=['reported', 'investigating', 'in_progress']
        ).order_by('-reported_at')[:5],
        
        # Total reports
        'total_reports': Report.objects.filter(status__in=['pending', 'investigating']).count(),
        
        # Sensors for map
        'sensors': Sensor.objects.filter(status='active'),
        
        # Incidents for map
        'incidents_for_map': Incident.objects.filter(
            is_public=True,
            status__in=['reported', 'investigating', 'in_progress']
        ),
    }
    
    # Consumption data for charts
    consumption_data = WaterConsumption.objects.filter(
        date__gte=now.date() - timedelta(days=7)
    ).order_by('date', 'hour')
    
    # Prepare chart data
    chart_labels = []
    chart_values = []
    
    for item in consumption_data[:24]:
        chart_labels.append(f"{item.hour}:00")
        chart_values.append(round(item.consumption_liters, 2))
    
    context['chart_labels'] = chart_labels
    context['chart_values'] = chart_values
    
    # District statistics
    context['districts'] = WaterConsumption.objects.values('district').annotate(
        total_consumption=Sum('consumption_liters')
    ).order_by('-total_consumption')[:5]
    
    return render(request, 'dashboard/index.html', context)


def sensor_list(request):
    """List all sensors with filtering."""
    
    sensors = Sensor.objects.all()
    
    # Filter by type
    sensor_type = request.GET.get('type')
    if sensor_type:
        sensors = sensors.filter(sensor_type=sensor_type)
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        sensors = sensors.filter(status=status)
    
    # Filter by district
    district = request.GET.get('district')
    if district:
        sensors = sensors.filter(district__icontains=district)
    
    # Search
    search = request.GET.get('search')
    if search:
        sensors = sensors.filter(name__icontains=search)
    
    context = {
        'sensors': sensors,
        'sensor_types': Sensor.SENSOR_TYPES,
        'status_choices': Sensor.STATUS_CHOICES,
        'selected_type': sensor_type,
        'selected_status': status,
        'selected_district': district,
        'search_query': search,
    }
    
    return render(request, 'dashboard/sensor_list.html', context)


def sensor_detail(request, pk):
    """Detailed view for a single sensor."""
    
    sensor = get_object_or_404(Sensor, pk=pk)
    
    # Get recent readings
    readings = sensor.readings.all()[:100]
    
    # Get recent anomalies
    anomalies = sensor.anomalies.all()[:10]
    
    # Prepare chart data
    chart_labels = []
    chart_values = []
    
    for reading in reversed(readings[:24]):
        chart_labels.append(reading.timestamp.strftime('%H:%M'))
        chart_values.append(round(reading.value, 2))
    
    context = {
        'sensor': sensor,
        'readings': readings[:50],
        'anomalies': anomalies,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
    }
    
    return render(request, 'dashboard/sensor_detail.html', context)


def anomaly_list(request):
    """List all anomalies with filtering."""
    
    anomalies = Anomaly.objects.all()
    
    # Filter by severity
    severity = request.GET.get('severity')
    if severity:
        anomalies = anomalies.filter(severity=severity)
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        anomalies = anomalies.filter(status=status)
    
    # Filter by type
    anomaly_type = request.GET.get('type')
    if anomaly_type:
        anomalies = anomalies.filter(anomaly_type=anomaly_type)
    
    context = {
        'anomalies': anomalies[:50],
        'severity_choices': Anomaly.SEVERITY_CHOICES,
        'status_choices': Anomaly.STATUS_CHOICES,
        'type_choices': Anomaly.ANOMALY_TYPES,
        'selected_severity': severity,
        'selected_status': status,
        'selected_type': anomaly_type,
    }
    
    return render(request, 'dashboard/anomaly_list.html', context)


def anomaly_detail(request, pk):
    """Detailed view for a single anomaly."""
    
    anomaly = get_object_or_404(Anomaly, pk=pk)
    
    context = {
        'anomaly': anomaly,
    }
    
    return render(request, 'dashboard/anomaly_detail.html', context)


def incident_list(request):
    """List all public incidents with filtering."""
    
    incidents = Incident.objects.filter(is_public=True)
    
    # Filter by type
    incident_type = request.GET.get('type')
    if incident_type:
        incidents = incidents.filter(incident_type=incident_type)
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        incidents = incidents.filter(status=status)
    
    # Filter by district
    district = request.GET.get('district')
    if district:
        incidents = incidents.filter(district__icontains=district)
    
    # Search
    search = request.GET.get('search')
    if search:
        incidents = incidents.filter(title__icontains=search)
    
    context = {
        'incidents': incidents.order_by('-reported_at')[:50],
        'type_choices': Incident.INCIDENT_TYPES,
        'status_choices': Incident.STATUS_CHOICES,
        'selected_type': incident_type,
        'selected_status': status,
        'selected_district': district,
        'search_query': search,
    }
    
    return render(request, 'dashboard/incident_list.html', context)


def incident_detail(request, pk):
    """Detailed view for a single incident."""
    
    incident = get_object_or_404(Incident, pk=pk, is_public=True)
    
    context = {
        'incident': incident,
    }
    
    return render(request, 'dashboard/incident_detail.html', context)


def map_view(request):
    """Interactive map view with all sensors and incidents."""
    
    context = {
        'sensors': Sensor.objects.filter(status='active'),
        'incidents': Incident.objects.filter(
            is_public=True,
            status__in=['reported', 'investigating', 'in_progress']
        ),
        'anomalies': Anomaly.objects.filter(
            status__in=['detected', 'investigating', 'confirmed']
        ),
    }
    
    return render(request, 'dashboard/map.html', context)


def statistics(request):
    """Detailed statistics page."""
    
    now = timezone.now()
    last_30d = now - timedelta(days=30)
    
    # Consumption statistics
    consumption_stats = WaterConsumption.objects.filter(
        date__gte=last_30d.date()
    ).aggregate(
        total=Sum('consumption_liters'),
        avg=Avg('consumption_liters'),
        max=Max('consumption_liters'),
        min=Min('consumption_liters')
    )
    
    # Daily consumption for last 30 days
    daily_consumption = WaterConsumption.objects.filter(
        date__gte=last_30d.date()
    ).values('date').annotate(
        total=Sum('consumption_liters')
    ).order_by('date')
    
    # Anomaly statistics by type
    anomaly_by_type = Anomaly.objects.values('anomaly_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Incident statistics
    incident_stats = {
        'total': Incident.objects.count(),
        'ongoing': Incident.objects.filter(status__in=['reported', 'investigating', 'in_progress']).count(),
        'resolved': Incident.objects.filter(status='resolved').count(),
        'by_type': Incident.objects.values('incident_type').annotate(count=Count('id')),
    }
    
    context = {
        'consumption_stats': consumption_stats,
        'daily_consumption': daily_consumption,
        'anomaly_by_type': anomaly_by_type,
        'incident_stats': incident_stats,
    }
    
    return render(request, 'dashboard/statistics.html', context)


# API endpoints for AJAX requests
@require_http_methods(['GET'])
def api_sensor_data(request, sensor_id):
    """API endpoint to get sensor data for charts."""
    
    sensor = get_object_or_404(Sensor, pk=sensor_id)
    hours = int(request.GET.get('hours', 24))
    
    since = timezone.now() - timedelta(hours=hours)
    readings = sensor.readings.filter(timestamp__gte=since).order_by('timestamp')
    
    data = {
        'labels': [r.timestamp.strftime('%H:%M') for r in readings],
        'values': [r.value for r in readings],
        'unit': readings.first().unit if readings.exists() else '',
    }
    
    return JsonResponse(data)


@require_http_methods(['GET'])
def api_dashboard_stats(request):
    """API endpoint to get current dashboard statistics."""
    
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    
    data = {
        'active_sensors': Sensor.objects.filter(status='active').count(),
        'active_anomalies': Anomaly.objects.filter(
            status__in=['detected', 'investigating', 'confirmed']
        ).count(),
        'ongoing_incidents': Incident.objects.filter(
            status__in=['reported', 'investigating', 'in_progress']
        ).count(),
        'pending_reports': Report.objects.filter(status='pending').count(),
        'anomalies_last_24h': Anomaly.objects.filter(detected_at__gte=last_24h).count(),
    }
    
    return JsonResponse(data)


@require_http_methods(['GET'])
def api_map_data(request):
    """API endpoint to get all map data."""
    
    sensors = Sensor.objects.filter(status='active')
    incidents = Incident.objects.filter(
        is_public=True,
        status__in=['reported', 'investigating', 'in_progress']
    )
    anomalies = Anomaly.objects.filter(
        status__in=['detected', 'investigating', 'confirmed']
    )
    
    data = {
        'sensors': [
            {
                'id': s.id,
                'name': s.name,
                'type': s.get_sensor_type_display(),
                'lat': float(s.latitude),
                'lng': float(s.longitude),
                'status': s.status,
            }
            for s in sensors
        ],
        'incidents': [
            {
                'id': i.id,
                'title': i.title,
                'type': i.get_incident_type_display(),
                'lat': float(i.latitude),
                'lng': float(i.longitude),
                'status': i.status,
                'affected_radius': i.affected_area_radius,
            }
            for i in incidents
        ],
        'anomalies': [
            {
                'id': a.id,
                'title': a.title,
                'type': a.get_anomaly_type_display(),
                'lat': float(a.latitude) if a.latitude else None,
                'lng': float(a.longitude) if a.longitude else None,
                'severity': a.severity,
            }
            for a in anomalies
        ],
    }
    
    return JsonResponse(data)
