"""
Management command to create test data for Smart City application.
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from dashboard.models import Sensor, SensorReading, Anomaly, Incident, WaterConsumption
from reports.models import Report

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test data for Smart City application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Delete existing data before creating new',
        )

    def handle(self, *args, **options):
        if options['clean']:
            self.stdout.write('Cleaning existing data...')
            SensorReading.objects.all().delete()
            Anomaly.objects.all().delete()
            Incident.objects.all().delete()
            WaterConsumption.objects.all().delete()
            Report.objects.all().delete()
            Sensor.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleaned.'))

        self.create_users()
        self.create_sensors()
        self.create_sensor_readings()
        self.create_anomalies()
        self.create_incidents()
        self.create_consumption_data()
        self.create_reports()

        self.stdout.write(self.style.SUCCESS('Test data created successfully!'))

    def create_users(self):
        """Create test users with different roles."""
        self.stdout.write('Creating users...')

        users_data = [
            {'email': 'citizen@example.com', 'password': 'testpass123', 'first_name': 'Иван', 'last_name': 'Петров', 'role': 'citizen'},
            {'email': 'operator@example.com', 'password': 'testpass123', 'first_name': 'Мария', 'last_name': 'Иванова', 'role': 'operator'},
            {'email': 'technician@example.com', 'password': 'testpass123', 'first_name': 'Георги', 'last_name': 'Димитров', 'role': 'technician'},
            {'email': 'admin@example.com', 'password': 'testpass123', 'first_name': 'Админ', 'last_name': 'Потребител', 'role': 'admin'},
        ]

        for user_data in users_data:
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'role': user_data['role'],
                    'is_active': True,
                }
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(f'  Created user: {user.email} ({user.get_role_display()})')

    def create_sensors(self):
        """Create test sensors."""
        self.stdout.write('Creating sensors...')

        sensors_data = [
            # Flow sensors
            {'name': 'Разходомер - Център 1', 'sensor_type': 'flow', 'latitude': 42.6977, 'longitude': 23.3219, 'district': 'Център', 'address': 'ул. Витоша 1'},
            {'name': 'Разходомер - Лозенец', 'sensor_type': 'flow', 'latitude': 42.6850, 'longitude': 23.3200, 'district': 'Лозенец', 'address': 'ул. Джеймс Баучер 52'},
            {'name': 'Разходомер - Младост 1', 'sensor_type': 'flow', 'latitude': 42.6500, 'longitude': 23.3800, 'district': 'Младост', 'address': 'бл. 1, Младост 1'},
            {'name': 'Разходомер - Люлин 1', 'sensor_type': 'flow', 'latitude': 42.7100, 'longitude': 23.2500, 'district': 'Люлин', 'address': 'бл. 1, Люлин 1'},
            
            # Pressure sensors
            {'name': 'Налягане - Център', 'sensor_type': 'pressure', 'latitude': 42.6950, 'longitude': 23.3250, 'district': 'Център', 'address': 'пл. Независимост'},
            {'name': 'Налягане - Младост', 'sensor_type': 'pressure', 'latitude': 42.6550, 'longitude': 23.3750, 'district': 'Младост', 'address': 'бл. 100, Младост 2'},
            {'name': 'Налягане - Люлин', 'sensor_type': 'pressure', 'latitude': 42.7150, 'longitude': 23.2450, 'district': 'Люлин', 'address': 'бл. 50, Люлин 3'},
            
            # Quality sensors
            {'name': 'Качество - Център', 'sensor_type': 'quality', 'latitude': 42.6980, 'longitude': 23.3180, 'district': 'Център', 'address': 'ул. Граф Игнатиев 10'},
            {'name': 'Качество - Младост', 'sensor_type': 'quality', 'latitude': 42.6520, 'longitude': 23.3780, 'district': 'Младост', 'address': 'бл. 200, Младост 4'},
            
            # Leak detectors
            {'name': 'Детектор - Център', 'sensor_type': 'leak', 'latitude': 42.6960, 'longitude': 23.3220, 'district': 'Център', 'address': 'ул. Сердика 5'},
            {'name': 'Детектор - Лозенец', 'sensor_type': 'leak', 'latitude': 42.6870, 'longitude': 23.3180, 'district': 'Лозенец', 'address': 'ул. Свети Климент Охридски 15'},
        ]

        for sensor_data in sensors_data:
            sensor, created = Sensor.objects.get_or_create(
                name=sensor_data['name'],
                defaults={
                    'sensor_type': sensor_data['sensor_type'],
                    'latitude': sensor_data['latitude'],
                    'longitude': sensor_data['longitude'],
                    'district': sensor_data['district'],
                    'address': sensor_data['address'],
                    'status': 'active',
                    'min_value': 0,
                    'max_value': 1000,
                    'threshold_warning': 800,
                    'threshold_critical': 950,
                }
            )
            if created:
                self.stdout.write(f'  Created sensor: {sensor.name}')

    def create_sensor_readings(self):
        """Create test sensor readings."""
        self.stdout.write('Creating sensor readings...')

        sensors = Sensor.objects.all()
        now = timezone.now()

        for sensor in sensors:
            readings_count = 0
            for hours_ago in range(168):  # Last 7 days
                timestamp = now - timedelta(hours=hours_ago)
                
                # Generate realistic values based on sensor type
                if sensor.sensor_type == 'flow':
                    base_value = 500
                    variation = random.gauss(0, 50)
                    value = max(0, base_value + variation)
                    unit = 'L/h'
                elif sensor.sensor_type == 'pressure':
                    base_value = 4
                    variation = random.gauss(0, 0.3)
                    value = max(0, base_value + variation)
                    unit = 'bar'
                elif sensor.sensor_type == 'quality':
                    base_value = 95
                    variation = random.gauss(0, 3)
                    value = min(100, max(0, base_value + variation))
                    unit = '%'
                elif sensor.sensor_type == 'leak':
                    value = random.choice([0, 0, 0, 0, 1])  # Mostly no leak
                    unit = 'binary'
                else:
                    value = random.uniform(10, 100)
                    unit = 'units'

                SensorReading.objects.create(
                    sensor=sensor,
                    value=round(value, 2),
                    unit=unit,
                    timestamp=timestamp,
                    is_anomaly=value > sensor.threshold_warning if sensor.threshold_warning else False
                )
                readings_count += 1

            self.stdout.write(f'  Created {readings_count} readings for {sensor.name}')

    def create_anomalies(self):
        """Create test anomalies."""
        self.stdout.write('Creating anomalies...')

        sensors = Sensor.objects.all()
        now = timezone.now()

        anomaly_types = ['leak', 'pressure_drop', 'high_consumption', 'quality_issue']
        severities = ['low', 'medium', 'high', 'critical']
        statuses = ['detected', 'investigating', 'confirmed', 'resolved']

        for i in range(15):
            sensor = random.choice(sensors)
            anomaly_type = random.choice(anomaly_types)
            severity = random.choice(severities)
            status = random.choice(statuses)

            detected_at = now - timedelta(hours=random.randint(1, 72))

            Anomaly.objects.create(
                title=f'Аномалия {i+1} - {sensor.district}',
                description=f'Открита е аномалия от тип {anomaly_type} в район {sensor.district}.',
                anomaly_type=anomaly_type,
                severity=severity,
                status=status,
                sensor=sensor,
                latitude=sensor.latitude,
                longitude=sensor.longitude,
                detected_at=detected_at,
                confidence=random.uniform(60, 99),
                estimated_affected_users=random.randint(10, 500),
            )

        self.stdout.write(f'  Created 15 anomalies')

    def create_incidents(self):
        """Create test incidents."""
        self.stdout.write('Creating incidents...')

        incident_types = ['burst_pipe', 'major_leak', 'pump_failure', 'maintenance']
        districts = ['Център', 'Лозенец', 'Младост', 'Люлин', 'Овча купел', 'Витоша']
        
        now = timezone.now()

        incidents_data = [
            {
                'title': 'Спукана тръба - ул. Витоша',
                'description': 'Голяма спукана тръба на главната магистрала. Екипът е на място.',
                'incident_type': 'burst_pipe',
                'district': 'Център',
                'latitude': 42.6977,
                'longitude': 23.3219,
                'affected_users': 500,
                'is_featured': True,
            },
            {
                'title': 'Теч в Младост 1',
                'description': 'Заявен теч от жители на квартала. Проверява се.',
                'incident_type': 'major_leak',
                'district': 'Младост',
                'latitude': 42.6500,
                'longitude': 23.3800,
                'affected_users': 150,
                'is_featured': True,
            },
            {
                'title': 'Планирана поддръжка - Люлин',
                'description': 'Планирана поддръжка на водопроводната мрежа.',
                'incident_type': 'maintenance',
                'district': 'Люлин',
                'latitude': 42.7100,
                'longitude': 23.2500,
                'affected_users': 200,
                'is_featured': False,
            },
            {
                'title': 'Неизправност на помпа',
                'description': 'Помпена станция временно извън строя.',
                'incident_type': 'pump_failure',
                'district': 'Лозенец',
                'latitude': 42.6850,
                'longitude': 23.3200,
                'affected_users': 80,
                'is_featured': False,
            },
        ]

        for incident_data in incidents_data:
            incident, created = Incident.objects.get_or_create(
                title=incident_data['title'],
                defaults={
                    'description': incident_data['description'],
                    'incident_type': incident_data['incident_type'],
                    'district': incident_data['district'],
                    'latitude': incident_data['latitude'],
                    'longitude': incident_data['longitude'],
                    'address': incident_data['district'],
                    'affected_users': incident_data['affected_users'],
                    'is_public': True,
                    'is_featured': incident_data['is_featured'],
                    'status': random.choice(['reported', 'investigating', 'in_progress']),
                    'estimated_resolution': now + timedelta(hours=random.randint(2, 24)),
                }
            )
            if created:
                self.stdout.write(f'  Created incident: {incident.title}')

    def create_consumption_data(self):
        """Create test water consumption data."""
        self.stdout.write('Creating consumption data...')

        districts = ['Център', 'Лозенец', 'Младост', 'Люлин', 'Овча купел']
        now = timezone.now()

        for district in districts:
            for days_ago in range(30):  # Last 30 days
                date = (now - timedelta(days=days_ago)).date()
                
                for hour in range(24):
                    # Generate realistic consumption pattern
                    base_consumption = 10000
                    
                    # Higher consumption during day hours
                    if 6 <= hour <= 22:
                        multiplier = 1.5
                    else:
                        multiplier = 0.6
                    
                    # Weekend variation
                    if date.weekday() >= 5:
                        multiplier *= 0.8
                    
                    consumption = base_consumption * multiplier * random.uniform(0.9, 1.1)

                    WaterConsumption.objects.get_or_create(
                        district=district,
                        date=date,
                        hour=hour,
                        defaults={
                            'consumption_liters': round(consumption, 2),
                            'avg_pressure': round(random.uniform(3.5, 4.5), 2),
                            'avg_quality_score': round(random.uniform(90, 99), 1),
                        }
                    )

        self.stdout.write(f'  Created consumption data for {len(districts)} districts')

    def create_reports(self):
        """Create test reports."""
        self.stdout.write('Creating reports...')

        categories = ['leak', 'burst_pipe', 'pressure_low', 'water_quality', 'no_water']
        districts = ['Център', 'Лозенец', 'Младост', 'Люлин']
        
        users = User.objects.filter(role='citizen')

        for i in range(20):
            category = random.choice(categories)
            district = random.choice(districts)
            user = random.choice(users) if users and random.random() > 0.3 else None

            Report.objects.create(
                user=user,
                reporter_name='' if user else f'Гражданин {i+1}',
                reporter_email='' if user else f'citizen{i}@example.com',
                title=f'Сигнал {i+1} - {district}',
                description=f'Докладван проблем с водата в район {district}.',
                category=category,
                status=random.choice(['pending', 'investigating', 'in_progress', 'resolved']),
                priority=random.choice(['low', 'medium', 'high', 'urgent']),
                address=f'ул. Примерна {i+1}, {district}',
                district=district,
                is_public=True,
            )

        self.stdout.write(f'  Created 20 reports')
