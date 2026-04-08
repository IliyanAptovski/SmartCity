from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Main dashboard
    path('', views.index, name='index'),
    
    # Sensors
    path('sensors/', views.sensor_list, name='sensor_list'),
    path('sensors/<int:pk>/', views.sensor_detail, name='sensor_detail'),
    
    # Anomalies
    path('anomalies/', views.anomaly_list, name='anomaly_list'),
    path('anomalies/<int:pk>/', views.anomaly_detail, name='anomaly_detail'),
    
    # Incidents
    path('incidents/', views.incident_list, name='incident_list'),
    path('incidents/<int:pk>/', views.incident_detail, name='incident_detail'),
    
    # Map
    path('map/', views.map_view, name='map'),
    
    # Statistics
    path('statistics/', views.statistics, name='statistics'),
    
    # API endpoints
    path('api/sensor/<int:sensor_id>/data/', views.api_sensor_data, name='api_sensor_data'),
    path('api/dashboard-stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
    path('api/map-data/', views.api_map_data, name='api_map_data'),
]
