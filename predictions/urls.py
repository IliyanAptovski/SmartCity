from django.urls import path
from . import views

app_name = 'predictions'

urlpatterns = [
    # Public views
    path('', views.predictions_list, name='list'),
    path('<int:pk>/', views.prediction_detail, name='detail'),
    path('dashboard/', views.dashboard_predictions, name='dashboard'),
    
    # Staff views
    path('models/', views.model_list, name='model_list'),
    path('models/<int:pk>/', views.model_detail, name='model_detail'),
    path('train/', views.train_models, name='train'),
    
    # API endpoints
    path('api/predictions/', views.api_predictions, name='api_predictions'),
    path('api/predictions/<int:pk>/validate/', views.api_validate_prediction, name='api_validate'),
    path('api/run-anomaly-detection/', views.run_anomaly_detection, name='api_run_anomaly'),
]
