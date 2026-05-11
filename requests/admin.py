from django.contrib import admin
from .models import Task ,ServiceRequest

# Register your models here.
admin.site.register(Task)
admin.site.register(ServiceRequest)