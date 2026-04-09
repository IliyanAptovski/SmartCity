import os
import django
import random
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.settings")
django.setup()

from apps.sensors.models import Location, Sensor, Measurement


def create_locations():
    locations = [
        ("City Center", "Main St 1"),
        ("Industrial Zone", "Factory Rd 12"),
        ("Residential Area", "Green St 45"),
        ("University Campus", "Campus Ave 3"),
    ]

    objs = []
    for name, address in locations:
        obj, _ = Location.objects.get_or_create(name=name, address=address)
        objs.append(obj)

    return objs


def create_sensors(locations):
    sensors = []

    for loc in locations:
        for i in range(3):  # 3 sensors per location
            sensor = Sensor.objects.create(
                name=f"{loc.name}-Sensor-{i+1}",
                location=loc,
                active=True
            )
            sensors.append(sensor)

    return sensors


def generate_measurements(sensors):
    now = timezone.now()

    for sensor in sensors:
        for i in range(50):  # 50 readings per sensor
            timestamp = now - timedelta(minutes=i * 5)

            # NORMAL VALUES
            # Flow rate
            # Household / small building: 5 – 25 L
            # Apartment building / small network: 20 – 100 L

            # Pressure
            # Residential systems: 2.0 – 4.5 bar
            # Urban water supply: 3.0 – 6.0 bar

            # ANOMALIES
            # Flow rate
            # Too LOW possible blockage / leak: 0 – 2 L
            # Too HIGH possible leak / burst: > 150 L

            # Pressure
            # Too LOW weak flow, possible leak, pump failure: < 1.5 bar
            # Too HIGH dangerous, risk of pipe damage: > 6.5 – 7 bar

            flow = random.uniform(5, 100) # in liters
            pressure = random.uniform(2, 6) # in bars

            # INJECT ANOMALY (~15% chance)
            if random.random() < 0.15:
                
                anomaly_type = random.choice([
                    "leak",
                    "blockage",
                    "pump_failure",
                    "overpressure"
                ])

                if anomaly_type == "leak":
                    # High flow, low pressure
                    flow = random.uniform(120, 200)
                    pressure = random.uniform(0.5, 2.0)

                elif anomaly_type == "blockage":
                    # Very low flow, high pressure buildup
                    flow = random.uniform(0.0, 2.0)
                    pressure = random.uniform(6.5, 8.0)

                elif anomaly_type == "pump_failure":
                    # Low pressure + unstable/low flow
                    flow = random.uniform(0, 2.0)
                    pressure = random.uniform(0.5, 1.5)

                elif anomaly_type == "overpressure":
                    # Dangerous pressure spike
                    flow = random.uniform(80, 100)
                    pressure = random.uniform(7.0, 10.0)

            Measurement.objects.create(
                sensor=sensor,
                flow_rate=flow,
                pressure=pressure,
                timestamp=timestamp
            )


def run():
    print("Seeding data...")

    locations = create_locations()
    sensors = create_sensors(locations)
    generate_measurements(sensors)

    print("Done!")


if __name__ == "__main__":
    run()