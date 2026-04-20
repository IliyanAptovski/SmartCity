from django.contrib import admin
from .models import Location, Sensor, Measurement

# Register your models here.
admin.site.register(Location)
admin.site.register(Sensor)
admin.site.register(Measurement)