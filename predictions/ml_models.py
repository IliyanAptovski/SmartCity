"""
Machine Learning models for Smart City Water Infrastructure Monitoring.

This module contains ML models for:
- Anomaly detection in water consumption
- Leak detection
- Consumption forecasting
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import os
from datetime import datetime, timedelta
from django.conf import settings


class AnomalyDetector:
    """Anomaly detection model for water sensor data."""
    
    def __init__(self, contamination=0.1):
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def prepare_features(self, readings):
        """
        Prepare features from sensor readings.
        
        Args:
            readings: List of SensorReading objects or DataFrame
            
        Returns:
            numpy array of features
        """
        if isinstance(readings, list):
            data = []
            for reading in readings:
                data.append({
                    'value': reading.value,
                    'hour': reading.timestamp.hour,
                    'day_of_week': reading.timestamp.weekday(),
                    'month': reading.timestamp.month,
                })
            df = pd.DataFrame(data)
        else:
            df = readings.copy()
        
        # Add statistical features
        df['value_diff'] = df['value'].diff().fillna(0)
        df['value_rolling_mean'] = df['value'].rolling(window=5, min_periods=1).mean()
        df['value_rolling_std'] = df['value'].rolling(window=5, min_periods=1).std().fillna(0)
        
        return df.values
    
    def train(self, readings):
        """
        Train the anomaly detection model.
        
        Args:
            readings: List of normal SensorReading objects
        """
        features = self.prepare_features(readings)
        features_scaled = self.scaler.fit_transform(features)
        
        self.model.fit(features_scaled)
        self.is_trained = True
    
    def predict(self, readings):
        """
        Predict anomalies in readings.
        
        Args:
            readings: List of SensorReading objects
            
        Returns:
            List of tuples (is_anomaly, anomaly_score)
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        features = self.prepare_features(readings)
        features_scaled = self.scaler.transform(features)
        
        # Predict: -1 for anomaly, 1 for normal
        predictions = self.model.predict(features_scaled)
        scores = self.model.decision_function(features_scaled)
        
        # Convert to boolean and normalize scores
        is_anomaly = predictions == -1
        anomaly_scores = 1 - (scores + 0.5)  # Normalize to 0-1 range
        
        return list(zip(is_anomaly, anomaly_scores))
    
    def save(self, filepath):
        """Save model to file."""
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'is_trained': self.is_trained
        }, filepath)
    
    def load(self, filepath):
        """Load model from file."""
        data = joblib.load(filepath)
        self.model = data['model']
        self.scaler = data['scaler']
        self.is_trained = data['is_trained']


class LeakDetector:
    """Leak detection model based on pressure and flow patterns."""
    
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            max_depth=10
        )
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def extract_features(self, flow_readings, pressure_readings):
        """
        Extract features from flow and pressure readings.
        
        Args:
            flow_readings: List of flow sensor readings
            pressure_readings: List of pressure sensor readings
            
        Returns:
            numpy array of features
        """
        features = []
        
        # Calculate statistics for flow
        flow_values = [r.value for r in flow_readings]
        flow_stats = {
            'flow_mean': np.mean(flow_values) if flow_values else 0,
            'flow_std': np.std(flow_values) if flow_values else 0,
            'flow_min': np.min(flow_values) if flow_values else 0,
            'flow_max': np.max(flow_values) if flow_values else 0,
            'flow_trend': self._calculate_trend(flow_values),
        }
        
        # Calculate statistics for pressure
        pressure_values = [r.value for r in pressure_readings]
        pressure_stats = {
            'pressure_mean': np.mean(pressure_values) if pressure_values else 0,
            'pressure_std': np.std(pressure_values) if pressure_values else 0,
            'pressure_min': np.min(pressure_values) if pressure_values else 0,
            'pressure_max': np.max(pressure_values) if pressure_values else 0,
            'pressure_trend': self._calculate_trend(pressure_values),
        }
        
        # Combine features
        feature_vector = [
            flow_stats['flow_mean'],
            flow_stats['flow_std'],
            flow_stats['flow_min'],
            flow_stats['flow_max'],
            flow_stats['flow_trend'],
            pressure_stats['pressure_mean'],
            pressure_stats['pressure_std'],
            pressure_stats['pressure_min'],
            pressure_stats['pressure_max'],
            pressure_stats['pressure_trend'],
            # Leak indicators
            flow_stats['flow_std'] / (flow_stats['flow_mean'] + 1e-6),  # Flow variation
            pressure_stats['pressure_std'] / (pressure_stats['pressure_mean'] + 1e-6),  # Pressure variation
        ]
        
        return np.array(feature_vector).reshape(1, -1)
    
    def _calculate_trend(self, values):
        """Calculate trend using linear regression."""
        if len(values) < 2:
            return 0
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        return slope
    
    def train(self, flow_readings_list, pressure_readings_list, labels):
        """
        Train the leak detection model.
        
        Args:
            flow_readings_list: List of flow reading lists
            pressure_readings_list: List of pressure reading lists
            labels: List of labels (0 = no leak, 1 = leak)
        """
        X = []
        for flow, pressure in zip(flow_readings_list, pressure_readings_list):
            features = self.extract_features(flow, pressure)
            X.append(features[0])
        
        X = np.array(X)
        y = np.array(labels)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        self.metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1_score': f1_score(y_test, y_pred, zero_division=0),
        }
        
        self.is_trained = True
        return self.metrics
    
    def predict(self, flow_readings, pressure_readings):
        """
        Predict if there's a leak.
        
        Args:
            flow_readings: List of flow sensor readings
            pressure_readings: List of pressure sensor readings
            
        Returns:
            Dictionary with prediction results
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        features = self.extract_features(flow_readings, pressure_readings)
        features_scaled = self.scaler.transform(features)
        
        prediction = self.model.predict(features_scaled)[0]
        probability = self.model.predict_proba(features_scaled)[0]
        
        return {
            'has_leak': bool(prediction == 1),
            'confidence': float(max(probability) * 100),
            'leak_probability': float(probability[1] * 100),
            'feature_importance': dict(zip(
                ['flow_mean', 'flow_std', 'flow_min', 'flow_max', 'flow_trend',
                 'pressure_mean', 'pressure_std', 'pressure_min', 'pressure_max', 'pressure_trend',
                 'flow_variation', 'pressure_variation'],
                self.model.feature_importances_
            ))
        }
    
    def save(self, filepath):
        """Save model to file."""
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'is_trained': self.is_trained,
            'metrics': getattr(self, 'metrics', {})
        }, filepath)
    
    def load(self, filepath):
        """Load model from file."""
        data = joblib.load(filepath)
        self.model = data['model']
        self.scaler = data['scaler']
        self.is_trained = data['is_trained']
        self.metrics = data.get('metrics', {})


class ConsumptionForecaster:
    """Time series forecasting model for water consumption."""
    
    def __init__(self):
        self.models = {}  # One model per district
        self.scalers = {}
    
    def prepare_time_series_features(self, consumption_data):
        """
        Prepare time series features for forecasting.
        
        Args:
            consumption_data: DataFrame with consumption data
            
        Returns:
            numpy array of features
        """
        df = consumption_data.copy()
        
        # Time-based features
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
        df['month'] = pd.to_datetime(df['timestamp']).dt.month
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Lag features
        df['consumption_lag_1'] = df['consumption'].shift(1)
        df['consumption_lag_24'] = df['consumption'].shift(24)
        df['consumption_lag_168'] = df['consumption'].shift(168)  # 1 week
        
        # Rolling statistics
        df['consumption_rolling_mean_24'] = df['consumption'].rolling(window=24, min_periods=1).mean()
        df['consumption_rolling_std_24'] = df['consumption'].rolling(window=24, min_periods=1).std().fillna(0)
        
        # Fill NaN values
        df = df.fillna(method='bfill').fillna(method='ffill').fillna(0)
        
        feature_columns = [
            'hour', 'day_of_week', 'month', 'is_weekend',
            'consumption_lag_1', 'consumption_lag_24', 'consumption_lag_168',
            'consumption_rolling_mean_24', 'consumption_rolling_std_24'
        ]
        
        return df[feature_columns].values, df['consumption'].values
    
    def train(self, district, consumption_data):
        """
        Train forecasting model for a district.
        
        Args:
            district: District name
            consumption_data: DataFrame with consumption data
        """
        from sklearn.ensemble import GradientBoostingRegressor
        
        X, y = self.prepare_time_series_features(consumption_data)
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train model
        model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        model.fit(X_scaled, y)
        
        self.models[district] = model
        self.scalers[district] = scaler
    
    def predict(self, district, historical_data, hours_ahead=24):
        """
        Forecast consumption for future hours.
        
        Args:
            district: District name
            historical_data: DataFrame with historical consumption data
            hours_ahead: Number of hours to forecast
            
        Returns:
            List of predicted consumption values
        """
        if district not in self.models:
            raise ValueError(f"No model trained for district: {district}")
        
        model = self.models[district]
        scaler = self.scalers[district]
        
        predictions = []
        current_data = historical_data.copy()
        
        for _ in range(hours_ahead):
            # Prepare features
            X, _ = self.prepare_time_series_features(current_data)
            X_scaled = scaler.transform(X[-1:])
            
            # Predict
            pred = model.predict(X_scaled)[0]
            predictions.append(max(0, pred))  # Consumption can't be negative
            
            # Add prediction to data for next iteration
            last_row = current_data.iloc[-1:].copy()
            last_row['consumption'] = pred
            last_row['timestamp'] = pd.to_datetime(last_row['timestamp']) + timedelta(hours=1)
            current_data = pd.concat([current_data, last_row], ignore_index=True)
        
        return predictions


def get_model_path(model_name):
    """Get the full path for saving/loading a model."""
    models_dir = os.path.join(settings.MEDIA_ROOT, 'ml_models')
    os.makedirs(models_dir, exist_ok=True)
    return os.path.join(models_dir, f'{model_name}.joblib')


def train_anomaly_model(sensor_readings, model_name='anomaly_detector'):
    """
    Train and save an anomaly detection model.
    
    Args:
        sensor_readings: List of SensorReading objects
        model_name: Name for the saved model
        
    Returns:
        Trained AnomalyDetector instance
    """
    detector = AnomalyDetector()
    detector.train(sensor_readings)
    
    filepath = get_model_path(model_name)
    detector.save(filepath)
    
    return detector


def detect_anomalies(sensor_readings, model_name='anomaly_detector'):
    """
    Detect anomalies in sensor readings.
    
    Args:
        sensor_readings: List of SensorReading objects
        model_name: Name of the saved model
        
    Returns:
        List of tuples (is_anomaly, anomaly_score)
    """
    filepath = get_model_path(model_name)
    
    if not os.path.exists(filepath):
        # Train new model if doesn't exist
        return None
    
    detector = AnomalyDetector()
    detector.load(filepath)
    
    return detector.predict(sensor_readings)
