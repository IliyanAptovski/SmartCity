import os
import sys
import django
import random
from datetime import timedelta
from django.utils import timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.settings")
django.setup()

from apps.sensors.models import Location, Sensor, Measurement


def create_locations():
    locations = [
        ("Sofia Center", "Vitosha Blvd 1"),
        ("Plovdiv Old Town", "Saborna St 15"),
        ("Varna Seaside", "Knyaz Boris I Blvd 77"),
        ("Burgas Center", "Aleksandrovska St 21"),
        ("Ruse Downtown", "Tsar Osvoboditel Blvd 5"),
        ("Stara Zagora Center", "Tsar Simeon Veliki Blvd 88"),
        ("Pleven Center", "Vazrazhdane Sq 2"),
        ("Sliven Industrial Zone", "Industrialna St 10"),
        ("Dobrich Residential Area", "25-ti Septemvri Blvd 44"),
        ("Shumen Center", "Slavyanski Blvd 12"),
        ("Pernik Center", "Republika Blvd 3"),
        ("Haskovo Downtown", "San Stefano St 9"),
        ("Yambol Center", "Georgi Rakovski St 18"),
        ("Blagoevgrad Campus Area", "Ivan Mihaylov Blvd 66"),
        ("Veliko Tarnovo Old Town", "Gurko St 30"),
        ("Gabrovo Center", "Bryanska St 5"),
        ("Kardzhali Residential Area", "Bulgaria Blvd 14"),
    ]

    objs = []
    for name, address in locations:
        obj, _ = Location.objects.get_or_create(name=name, address=address)
        objs.append(obj)

    return objs


def create_sensors(locations):
    sensors = []

    for loc in locations:
        for i in range(17):  # 17 sensors per location
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

            flow = round(random.uniform(5, 100), 2) # in liters
            pressure = round(random.uniform(2, 6), 2) # in bars

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
                    flow = round(random.uniform(120, 200), 2)
                    pressure = round(random.uniform(0.5, 2.0), 2)

                elif anomaly_type == "blockage":
                    # Very low flow, high pressure buildup
                    flow = round(random.uniform(0.0, 2.0), 2)
                    pressure = round(random.uniform(6.5, 8.0), 2)

                elif anomaly_type == "pump_failure":
                    # Low pressure + unstable/low flow
                    flow = round(random.uniform(0, 2.0), 2)
                    pressure = round(random.uniform(0.5, 1.5), 2)

                elif anomaly_type == "overpressure":
                    # Dangerous pressure spike
                    flow = round(random.uniform(80, 100), 2)
                    pressure = round(random.uniform(7.0, 10.0), 2)

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