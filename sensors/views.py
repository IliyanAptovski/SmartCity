from django.shortcuts import render
from django.db.models import Sum, Avg, Count, F
from .models import Location, Measurement, Sensor

# Create your views here.

# Analytics for home page.
def index(request):
    measurements = Measurement.objects.all()
    return render(request, 'index.html', {"measurements":measurements})