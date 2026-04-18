from rest_framework import serializers
from .models import ServiceRequest

class ServiceRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequest
        fields = ['family_members', 'urgency_level', 'description', 'location']


from django.utils.timezone import now
from datetime import timedelta
from .models import Task

class TaskHomeSerializer(serializers.ModelSerializer):
    location = serializers.CharField(source='service_request_id.location')
    created_display = serializers.SerializerMethodField()
    icon = serializers.ImageField(source='service_request_id.service.icon')

    class Meta:
        model = Task
        fields = ['id', 'title', 'location', 'created_display', 'icon']

    def get_created_display(self, obj):
        diff = now() - obj.created_at

        if diff < timedelta(hours=24):
            return obj.created_at.strftime("%I:%M %p")
        elif diff < timedelta(days=2):
            return "Yesterday"
        else:
            return f"{diff.days} days ago"

    # 🔥 تحويل الرابط لـ absolute URL
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')

        if data.get('icon') and request:
            data['icon'] = request.build_absolute_uri(data['icon'])

        return data
from rest_framework import serializers
from django.utils.timesince import timesince
from django.utils.timezone import now

class TaskListSerializer(serializers.ModelSerializer):
    location = serializers.CharField(source='service_request_id.location')
    created_at_display = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    organization_name = serializers.CharField(source='volunteer_id.organization.name', read_only=True)
    task_description = serializers.CharField(source='service_request_id.description', read_only=True)
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'status',
            'location',
            'created_at_display',
            'time_ago',
            'task_description',
            'organization_name',
            'rejection_reason',
        ]

    def get_created_at_display(self, obj):
        return obj.created_at.strftime("%b %d, %I:%M %p")

    def get_time_ago(self, obj):
        return f"{timesince(obj.created_at, now())} ago"

    def to_representation(self, instance):
       data = super().to_representation(instance)

       if instance.status == 'completed':
         data.pop('time_ago', None)
         data.pop('rejection_reason', None)

       elif instance.status == 'failed':
          data.pop('time_ago', None)
          data.pop('organization_name', None)
          data.pop('task_description', None)
       else:  # pending
        data.pop('rejection_reason', None)
       return data 

class TaskUpdateSerializer(serializers.ModelSerializer):
    request_id_display = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ['id', 'title', 'status', 'service_request_id', 'request_id_display']

    def get_request_id_display(self, obj):
        return f"Request#{str(obj.service_request_id.id).zfill(4)}"    
    


class ServiceRequestCreateSecondSerializer(serializers.ModelSerializer):
    service_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ServiceRequest
        fields = [
            'service_id',
            'urgency_level',
            'description',
            'location',
            'family_members'
        ]    