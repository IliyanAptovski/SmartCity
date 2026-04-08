from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Count
from django.contrib import messages

from .models import Prediction, PredictionModel, AlertRule, ModelTrainingLog
from dashboard.models import Sensor, SensorReading, Anomaly


def predictions_list(request):
    """List all predictions with filtering."""
    
    predictions = Prediction.objects.all()
    
    # Filter by type
    prediction_type = request.GET.get('type')
    if prediction_type:
        predictions = predictions.filter(prediction_type=prediction_type)
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        predictions = predictions.filter(status=status)
    
    # Filter by confidence
    min_confidence = request.GET.get('min_confidence')
    if min_confidence:
        predictions = predictions.filter(confidence__gte=float(min_confidence))
    
    # Show only high confidence predictions by default
    show_all = request.GET.get('show_all')
    if not show_all:
        predictions = predictions.filter(confidence__gte=50)
    
    context = {
        'predictions': predictions.order_by('-prediction_made_at')[:50],
        'prediction_types': Prediction.PREDICTION_TYPES,
        'status_choices': Prediction.STATUS_CHOICES,
        'selected_type': prediction_type,
        'selected_status': status,
        'high_confidence_count': predictions.filter(confidence__gte=70).count(),
        'pending_count': predictions.filter(status='pending').count(),
    }
    
    return render(request, 'predictions/predictions_list.html', context)


def prediction_detail(request, pk):
    """Detailed view for a single prediction."""
    
    prediction = get_object_or_404(Prediction, pk=pk)
    
    context = {
        'prediction': prediction,
    }
    
    return render(request, 'predictions/prediction_detail.html', context)


@staff_member_required
def model_list(request):
    """List all ML models."""
    
    models = PredictionModel.objects.all()
    
    context = {
        'models': models,
        'model_types': PredictionModel.MODEL_TYPES,
    }
    
    return render(request, 'predictions/model_list.html', context)


@staff_member_required
def model_detail(request, pk):
    """Detailed view for a model."""
    
    model = get_object_or_404(PredictionModel, pk=pk)
    training_logs = model.training_logs.all()[:10]
    recent_predictions = model.predictions.all()[:20]
    
    context = {
        'model': model,
        'training_logs': training_logs,
        'recent_predictions': recent_predictions,
    }
    
    return render(request, 'predictions/model_detail.html', context)


@login_required
def dashboard_predictions(request):
    """Dashboard view for predictions."""
    
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    
    # Statistics
    stats = {
        'total_predictions': Prediction.objects.count(),
        'predictions_24h': Prediction.objects.filter(prediction_made_at__gte=last_24h).count(),
        'high_confidence': Prediction.objects.filter(confidence__gte=70).count(),
        'confirmed': Prediction.objects.filter(status='confirmed').count(),
        'pending': Prediction.objects.filter(status='pending').count(),
    }
    
    # Recent high-confidence predictions
    recent_predictions = Prediction.objects.filter(
        confidence__gte=60
    ).order_by('-prediction_made_at')[:10]
    
    # Predictions by type
    predictions_by_type = Prediction.objects.values('prediction_type').annotate(
        count=Count('id'),
        avg_confidence=Avg('confidence')
    ).order_by('-count')
    
    context = {
        'stats': stats,
        'recent_predictions': recent_predictions,
        'predictions_by_type': predictions_by_type,
    }
    
    return render(request, 'predictions/dashboard.html', context)


# API endpoints
@require_http_methods(['GET'])
def api_predictions(request):
    """API endpoint to get predictions."""
    
    predictions = Prediction.objects.filter(status='pending')
    
    # Filter by minimum confidence
    min_confidence = request.GET.get('min_confidence', 50)
    predictions = predictions.filter(confidence__gte=float(min_confidence))
    
    data = {
        'predictions': [
            {
                'id': p.id,
                'title': p.title,
                'type': p.get_prediction_type_display(),
                'confidence': p.confidence,
                'probability': p.probability,
                'predicted_for': p.prediction_for_time.isoformat() if p.prediction_for_time else None,
                'district': p.district,
                'sensor_id': p.sensor_id,
            }
            for p in predictions
        ]
    }
    
    return JsonResponse(data)


@require_http_methods(['POST'])
def api_validate_prediction(request, pk):
    """API endpoint to validate a prediction."""
    
    prediction = get_object_or_404(Prediction, pk=pk)
    
    actual_value = request.POST.get('actual_value')
    notes = request.POST.get('notes', '')
    
    if actual_value is not None:
        prediction.validate(float(actual_value), notes)
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error', 'message': 'Actual value required'})


def run_anomaly_detection(request):
    """Run anomaly detection on recent sensor data."""
    
    from .ml_models import detect_anomalies, get_model_path, AnomalyDetector
    import os
    
    # Get recent readings
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    
    sensors = Sensor.objects.filter(status='active')
    new_anomalies = []
    
    for sensor in sensors:
        readings = list(sensor.readings.filter(timestamp__gte=last_24h).order_by('timestamp'))
        
        if len(readings) < 10:
            continue
        
        # Check if model exists
        model_path = get_model_path(f'anomaly_detector_{sensor.id}')
        
        if not os.path.exists(model_path):
            # Train new model for this sensor
            from .ml_models import train_anomaly_model
            # Use last 7 days for training
            training_readings = list(sensor.readings.filter(
                timestamp__gte=now - timedelta(days=7)
            ).order_by('timestamp'))
            
            if len(training_readings) >= 50:
                detector = train_anomaly_model(training_readings, f'anomaly_detector_{sensor.id}')
            else:
                continue
        else:
            # Load existing model
            detector = AnomalyDetector()
            detector.load(model_path)
        
        # Detect anomalies
        results = detector.predict(readings)
        
        for reading, (is_anomaly, score) in zip(readings, results):
            if is_anomaly and not reading.is_anomaly:
                # Mark reading as anomaly
                reading.is_anomaly = True
                reading.anomaly_score = score
                reading.save()
                
                # Create anomaly record
                anomaly, created = Anomaly.objects.get_or_create(
                    sensor=sensor,
                    detected_at=reading.timestamp,
                    defaults={
                        'title': f'Аномалия в {sensor.name}',
                        'description': f'Открита аномалия с резултат {score:.2f}',
                        'anomaly_type': 'other',
                        'severity': 'medium' if score < 0.7 else 'high',
                        'confidence': score * 100,
                        'latitude': sensor.latitude,
                        'longitude': sensor.longitude,
                    }
                )
                
                if created:
                    new_anomalies.append({
                        'sensor': sensor.name,
                        'score': score,
                        'time': reading.timestamp.isoformat()
                    })
    
    return JsonResponse({
        'status': 'success',
        'anomalies_detected': len(new_anomalies),
        'anomalies': new_anomalies
    })


@staff_member_required
def train_models(request):
    """View for training ML models."""
    
    if request.method == 'POST':
        model_type = request.POST.get('model_type')
        
        # Start training in background (simplified version)
        from .tasks import train_model_task
        
        # For now, just show message
        messages.info(request, f'Обучението на модел {model_type} е стартирано.')
        
        return redirect('predictions:model_list')
    
    context = {
        'model_types': PredictionModel.MODEL_TYPES,
    }
    
    return render(request, 'predictions/train_models.html', context)
