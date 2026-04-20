from django.shortcuts import render
from .models import Location, Measurement, Sensor

# Create your views here.
def index(request):
    measurements = Measurement.objects.all()
    return render(request, 'index.html', {"measurements":measurements})