"""
Celery tasks for ML model training and prediction.
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import os

from .models import PredictionModel, ModelTrainingLog, Prediction, AlertRule
from dashboard.models import Sensor, SensorReading, Anomaly
from .ml_models import (
    AnomalyDetector, 
    LeakDetector, 
    ConsumptionForecaster,
    get_model_path
)


@shared_task
def train_model_task(model_id):
    """
    Train an ML model in the background.
    
    Args:
        model_id: ID of the PredictionModel to train
    """
    model = PredictionModel.objects.get(id=model_id)
    
    # Create training log
    log = ModelTrainingLog.objects.create(
        model=model,
        status='running',
        parameters={'model_type': model.model_type}
    )
    
    try:
        if model.model_type == 'anomaly_detection':
            train_anomaly_detection_model(model)
        elif model.model_type == 'leak_detection':
            train_leak_detection_model(model)
        elif model.model_type == 'consumption_forecast':
            train_consumption_forecast_model(model)
        
        # Update log
        log.status = 'completed'
        log.completed_at = timezone.now()
        log.save()
        
        # Update model
        model.training_date = timezone.now()
        model.save()
        
    except Exception as e:
        log.status = 'failed'
        log.error_message = str(e)
        log.completed_at = timezone.now()
        log.save()
        raise


def train_anomaly_detection_model(model):
    """Train anomaly detection model."""
    
    # Get training data from all sensors
    now = timezone.now()
    training_period = now - timedelta(days=30)
    
    sensors = Sensor.objects.filter(status='active')
    all_readings = []
    
    for sensor in sensors:
        readings = list(sensor.readings.filter(
            timestamp__gte=training_period,
            is_anomaly=False  # Only use normal readings for training
        ).order_by('timestamp'))
        all_readings.extend(readings)
    
    if len(all_readings) < 100:
        raise ValueError("Insufficient training data (minimum 100 readings required)")
    
    # Train model
    detector = AnomalyDetector()
    detector.train(all_readings)
    
    # Save model
    filepath = get_model_path(f'anomaly_detection_{model.id}')
    detector.save(filepath)
    
    # Update model file reference
    model.model_file.name = f'ml_models/anomaly_detection_{model.id}.joblib'
    model.save()


def train_leak_detection_model(model):
    """Train leak detection model."""
    
    # Get flow and pressure sensors
    flow_sensors = Sensor.objects.filter(sensor_type='flow', status='active')
    pressure_sensors = Sensor.objects.filter(sensor_type='pressure', status='active')
    
    # Get historical data with known leak incidents
    from dashboard.models import Incident
    
    leak_incidents = Incident.objects.filter(
        incident_type='major_leak',
        created_at__gte=timezone.now() - timedelta(days=90)
    )
    
    # Prepare training data
    flow_readings_list = []
    pressure_readings_list = []
    labels = []
    
    for incident in leak_incidents:
        # Get readings before incident (no leak)
        before_time = incident.reported_at - timedelta(hours=2)
        for fs in flow_sensors:
            readings = list(fs.readings.filter(
                timestamp__gte=before_time - timedelta(hours=1),
                timestamp__lt=before_time
            ).order_by('timestamp'))
            if readings:
                flow_readings_list.append(readings)
                # Find corresponding pressure sensor
                ps = pressure_sensors.filter(district=fs.district).first()
                if ps:
                    p_readings = list(ps.readings.filter(
                        timestamp__gte=before_time - timedelta(hours=1),
                        timestamp__lt=before_time
                    ).order_by('timestamp'))
                    pressure_readings_list.append(p_readings)
                    labels.append(0)  # No leak
        
        # Get readings during incident (leak)
        for fs in flow_sensors.filter(district=incident.district):
            readings = list(fs.readings.filter(
                timestamp__gte=incident.reported_at,
                timestamp__lt=incident.reported_at + timedelta(hours=1)
            ).order_by('timestamp'))
            if readings:
                flow_readings_list.append(readings)
                ps = pressure_sensors.filter(district=fs.district).first()
                if ps:
                    p_readings = list(ps.readings.filter(
                        timestamp__gte=incident.reported_at,
                        timestamp__lt=incident.reported_at + timedelta(hours=1)
                    ).order_by('timestamp'))
                    pressure_readings_list.append(p_readings)
                    labels.append(1)  # Leak
    
    if len(labels) < 20:
        raise ValueError("Insufficient training data (minimum 20 samples required)")
    
    # Train model
    detector = LeakDetector()
    metrics = detector.train(flow_readings_list, pressure_readings_list, labels)
    
    # Save model
    filepath = get_model_path(f'leak_detection_{model.id}')
    detector.save(filepath)
    
    # Update model metrics
    model.accuracy = metrics.get('accuracy', 0) * 100
    model.precision = metrics.get('precision', 0) * 100
    model.recall = metrics.get('recall', 0) * 100
    model.f1_score = metrics.get('f1_score', 0) * 100
    model.model_file.name = f'ml_models/leak_detection_{model.id}.joblib'
    model.save()


def train_consumption_forecast_model(model):
    """Train consumption forecasting model."""
    
    from dashboard.models import WaterConsumption
    import pandas as pd
    
    # Get consumption data
    now = timezone.now()
    training_period = now - timedelta(days=90)
    
    consumption_data = WaterConsumption.objects.filter(
        date__gte=training_period.date()
    ).order_by('date', 'hour')
    
    if not consumption_data.exists():
        raise ValueError("No consumption data available for training")
    
    # Convert to DataFrame
    df = pd.DataFrame([
        {
            'timestamp': f"{c.date} {c.hour}:00:00",
            'consumption': c.consumption_liters,
            'district': c.district
        }
        for c in consumption_data
    ])
    
    # Train model for each district
    forecaster = ConsumptionForecaster()
    
    for district in df['district'].unique():
        district_data = df[df['district'] == district].copy()
        if len(district_data) >= 168:  # At least 1 week of data
            forecaster.train(district, district_data)
    
    # Save model
    filepath = get_model_path(f'consumption_forecast_{model.id}')
    forecaster.save(filepath)
    
    model.model_file.name = f'ml_models/consumption_forecast_{model.id}.joblib'
    model.save()


@shared_task
def run_periodic_anomaly_detection():
    """Run anomaly detection periodically."""
    
    now = timezone.now()
    last_hour = now - timedelta(hours=1)
    
    sensors = Sensor.objects.filter(status='active')
    
    for sensor in sensors:
        readings = list(sensor.readings.filter(
            timestamp__gte=last_hour
        ).order_by('timestamp'))
        
        if len(readings) < 5:
            continue
        
        # Load or train model
        model_path = get_model_path(f'anomaly_detection_sensor_{sensor.id}')
        
        if not os.path.exists(model_path):
            # Train new model
            training_readings = list(sensor.readings.filter(
                timestamp__gte=now - timedelta(days=7)
            ).order_by('timestamp'))
            
            if len(training_readings) < 50:
                continue
            
            detector = AnomalyDetector()
            detector.train(training_readings)
            detector.save(model_path)
        else:
            detector = AnomalyDetector()
            detector.load(model_path)
        
        # Detect anomalies
        results = detector.predict(readings)
        
        for reading, (is_anomaly, score) in zip(readings, results):
            if is_anomaly and not reading.is_anomaly:
                reading.is_anomaly = True
                reading.anomaly_score = score
                reading.save()
                
                # Create or update anomaly
                Anomaly.objects.get_or_create(
                    sensor=sensor,
                    detected_at=reading.timestamp,
                    defaults={
                        'title': f'Аномалия в {sensor.name}',
                        'description': f'Открита аномалия с резултат {score:.2f}',
                        'anomaly_type': self._determine_anomaly_type(sensor, reading),
                        'severity': 'medium' if score < 0.7 else 'high',
                        'confidence': score * 100,
                        'latitude': sensor.latitude,
                        'longitude': sensor.longitude,
                    }
                )


def _determine_anomaly_type(sensor, reading):
    """Determine the type of anomaly based on sensor type and reading."""
    
    if sensor.sensor_type == 'flow':
        if reading.value > sensor.max_value * 1.5:
            return 'high_consumption'
        elif reading.value < sensor.min_value * 0.5:
            return 'low_consumption'
    elif sensor.sensor_type == 'pressure':
        if reading.value < sensor.threshold_warning:
            return 'pressure_drop'
        elif sensor.threshold_critical and reading.value > sensor.threshold_critical:
            return 'pressure_spike'
    elif sensor.sensor_type == 'quality':
        return 'quality_issue'
    
    return 'other'


@shared_task
def generate_consumption_forecasts():
    """Generate consumption forecasts for all districts."""
    
    from dashboard.models import WaterConsumption
    import pandas as pd
    
    # Get default forecasting model
    model = PredictionModel.objects.filter(
        model_type='consumption_forecast',
        is_default=True,
        is_active=True
    ).first()
    
    if not model:
        return
    
    # Load model
    forecaster = ConsumptionForecaster()
    model_path = get_model_path(f'consumption_forecast_{model.id}')
    
    if not os.path.exists(model_path):
        return
    
    forecaster.load(model_path)
    
    # Get recent data
    now = timezone.now()
    recent_data = WaterConsumption.objects.filter(
        date__gte=(now - timedelta(days=7)).date()
    ).order_by('date', 'hour')
    
    # Generate forecasts for each district
    for district in recent_data.values_list('district', flat=True).distinct():
        district_data = recent_data.filter(district=district)
        
        df = pd.DataFrame([
            {
                'timestamp': f"{c.date} {c.hour}:00:00",
                'consumption': c.consumption_liters,
            }
            for c in district_data
        ])
        
        if len(df) < 24:
            continue
        
        # Generate forecast
        forecasts = forecaster.predict(district, df, hours_ahead=24)
        
        # Save predictions
        for i, forecast in enumerate(forecasts):
            prediction_time = now + timedelta(hours=i+1)
            
            Prediction.objects.create(
                title=f'Прогноза за консумация - {district}',
                description=f'Прогнозирана консумация за {prediction_time}',
                prediction_type='consumption',
                model=model,
                predicted_value=forecast,
                confidence=75.0,  # Default confidence
                probability=None,
                prediction_made_at=now,
                prediction_for_time=prediction_time,
                district=district,
            )


@shared_task
def check_alert_rules():
    """Check alert rules and send notifications."""
    
    active_rules = AlertRule.objects.filter(is_active=True)
    
    for rule in active_rules:
        # Get recent predictions matching the rule
        recent_predictions = Prediction.objects.filter(
            prediction_type=rule.prediction_type,
            status='pending',
            confidence__gte=rule.min_confidence,
            prediction_made_at__gte=timezone.now() - timedelta(hours=1)
        )
        
        if rule.min_probability:
            recent_predictions = recent_predictions.filter(
                probability__gte=rule.min_probability
            )
        
        for prediction in recent_predictions:
            # Send notifications
            if rule.notify_users and prediction.sensor:
                # Notify users in the affected area
                pass  # Implementation depends on user location data
            
            if rule.notify_operators:
                # Notify operators
                from users.models import Notification
                operators = User.objects.filter(role__in=['operator', 'admin'])
                
                for operator in operators:
                    Notification.objects.create(
                        user=operator,
                        title=rule.alert_title_template or f'Аларма: {prediction.title}',
                        message=rule.alert_message_template or prediction.description,
                        notification_type='alert',
                        link=f'/predictions/{prediction.id}/'
                    )
            
            if rule.create_incident:
                # Create incident
                from dashboard.models import Incident
                Incident.objects.get_or_create(
                    title=prediction.title,
                    defaults={
                        'description': prediction.description,
                        'incident_type': 'other',
                        'latitude': prediction.sensor.latitude if prediction.sensor else None,
                        'longitude': prediction.sensor.longitude if prediction.sensor else None,
                        'district': prediction.district,
                    }
                )
