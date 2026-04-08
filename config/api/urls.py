from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'notifications', views.NotificationViewSet, basename='notifications')
router.register(r'sensors', views.SensorViewSet)
router.register(r'anomalies', views.AnomalyViewSet)
router.register(r'incidents', views.IncidentViewSet)
router.register(r'reports', views.ReportViewSet, basename='reports')

urlpatterns = [
    path('', include(router.urls)),
    path('stats/', views.dashboard_stats, name='stats'),
    path('consumption/', views.consumption_data, name='consumption'),
    path('map-data/', views.map_data, name='map_data'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_read'),
]
