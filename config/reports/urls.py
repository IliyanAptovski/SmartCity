from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Public views
    path('', views.report_list, name='list'),
    path('create/', views.report_create, name='create'),
    path('<int:pk>/', views.report_detail, name='detail'),
    
    # User views
    path('my-reports/', views.my_reports, name='my_reports'),
    path('<int:pk>/edit/', views.report_edit, name='edit'),
    
    # Staff views
    path('staff/', views.staff_report_list, name='staff_list'),
    path('staff/<int:pk>/', views.staff_report_detail, name='staff_detail'),
    path('staff/<int:pk>/update/', views.staff_report_update, name='staff_update'),
    
    # API
    path('api/stats/', views.api_report_stats, name='api_stats'),
]
