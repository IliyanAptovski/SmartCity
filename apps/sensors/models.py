from django.db import models
from django.utils import timezone

# Create your models here.
class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.address}, {self.name} "


class Sensor(models.Model):
    name = models.CharField(max_length=100)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    installed_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def installed_at_gmt(self):
        local_time = timezone.localtime(self.installed_at)
        return local_time.strftime("%Y-%m-%d %H:%M:%S GMT%z")

    def __str__(self):
        return f"{self.name} ({self.location.name})"

class Measurement(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    flow_rate = models.FloatField()
    pressure = models.FloatField()

    def measured_at_gmt(self):
        local_time = timezone.localtime(self.timestamp)
        return local_time.strftime("%Y-%m-%d %H:%M:%S GMT%z")

    def __str__(self):
        return f"{self.sensor.name} - {self.measured_at_gmt()} - {self.sensor.location.name}"