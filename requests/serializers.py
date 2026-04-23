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

#شهد
from rest_framework import serializers
from .models import ServiceRequest
from organizations.models import OrganizationService, Service
from django.utils.timezone import now
from django.utils import timezone
from datetime import timedelta
from accounts.models import RefugeeProfile
#عرض خدمات
class ServiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Service
        fields = ['id', 'name','icon']

#لانشاء طلب مساعدة
class CreateRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = ServiceRequest
        fields = [
            "service",
            "family_members",
            "urgency_level",
            "description",
            "location",
        ]
    def validate_urgency_level(self, value):
        return value.lower()    

    def validate(self, attrs):
        service = attrs.get("service")
        organization = self.context.get("organization")

        if not OrganizationService.objects.filter(
            organization=organization,
            service=service
        ).exists():
            raise serializers.ValidationError(
                "Service not available for this organization"
            )

        return attrs
# لعرض طلباتي
class RefugeeMiniSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = RefugeeProfile
        fields = ["full_name", "profile_image"]

    def get_profile_image(self, obj):
        request = self.context.get("request")
        if obj.profile_image:
            return request.build_absolute_uri(obj.profile_image.url)
        return None    

class ApprovedRequestSerializer (serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name")
    sector = serializers.CharField(source="refugee.sector_name")
    ref = serializers.SerializerMethodField()
    approved_at = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = ['ref', 'service_name',"status", 'sector', 'approved_at','id']

    def get_ref(self, obj):
        return f"REF: {obj.refugee.id}"

    

    def get_approved_at(self, obj):
       diff = now() - obj.approved_at

       if diff.days == 0:
           return "Today"
       elif diff.days == 1:
           return "Yesterday"
       else:
           return f"{diff.days} days ago"

class RejectedRequestSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name")
    ref = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = [ 
            'id',
            "ref",
            "service_name",
            "rejection_reason",
            "status",
        ]
    def get_ref(self, obj):
         return f"REF: {obj.refugee.id}"
    

#  تفاصيل الطلب
class ServiceRequestDetailSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name")
    organization_logo = serializers.SerializerMethodField()
    service_name = serializers.CharField(source="service.name")
    service_type = serializers.CharField(source="service.service_type")
    ref = serializers.SerializerMethodField()
    sector = serializers.CharField(source="refugee.sector_name")
    received_at =serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()


    class Meta:
        model = ServiceRequest
        fields = [
            "ref",
            "organization_name",
            "organization_logo",
            "service_name",
            "status",
            "service_type",
            "family_members",
            "created_at",        # وقت تقديم الطلب للمنظمة
            "received_at",    
            "sector",
        ]  
    def get_ref(self, obj):
        return f"#REF- {obj.refugee.id}"

    def get_organization_logo(self, obj):
        request = self.context.get("request")
        if obj.organization.logo:
            return request.build_absolute_uri(obj.organization.logo.url)
        return None

    def get_received_at(self, obj):
        if not obj.received_at:
           return None

        return obj.received_at.strftime("%I:%M %p")
 
    def get_created_at(self, obj):
        
        if not obj.created_at:
           return None

        now = timezone.now()
        diff = now.date() - obj.created_at.date()

        # الجزء الأول (Today / Yesterday / Xd ago)
        if diff.days == 0:
            day_text = "Today"
        elif diff.days == 1:
            day_text = "Yesterday"
        else:
            day_text = f"{diff.days}d ago"

        # التاريخ
        day = obj.created_at.day

        # suffix (th / st / nd / rd)
        if 10 <= day <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

        date_text = obj.created_at.strftime(f"%B {day}{suffix}, %Y")

        return f"{day_text}, {date_text}"

#مسح الرمز 
class ConfirmDeliverySerializer(serializers.Serializer):
    refugee_id = serializers.IntegerField(read_only=True)
      

#لعرض واجهة الطلبات والفلترة حسب الحالة

class ApprovedSerializer(serializers.ModelSerializer):
    ref = serializers.SerializerMethodField()
    service_name = serializers.CharField(source="service.name")
    sector = serializers.CharField(source="refugee.sector_name")
    approved_at = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = [
            "status",
            "ref",
            "service_name",
            "id",
            "sector",
            "approved_at",  # وقت قبول المنظمة
        ]  
    def get_ref(self, obj):
        return f"REF: {obj.refugee.id}"


    def get_approved_at(self, obj):
        diff = now() - obj.approved_at

        if diff.days == 0:
            return "Today"
        elif diff.days == 1:
            return "Yesterday"
        else:
            return f"{diff.days} days ago"    

class CompletedSerializer(serializers.ModelSerializer):
    ref = serializers.SerializerMethodField()
    service_name = serializers.CharField(source="service.name")
    received_at = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = [
            "id",
            "status",
            "ref",
            "service_name",
            "received_at"  # وقت استلام النازح
        ] 
    def get_ref(self, obj):
        return f"REF: {obj.refugee.id}"

    def get_received_at(self, obj):
            if not obj.received_at:
                return None

            now = timezone.now()
            diff = now.date() - obj.received_at.date()

            if diff.days == 0:
                day_text = "Today"
            elif diff.days == 1:
                day_text = "1d ago"
            else:
                day_text = f"{diff.days}d ago"

            time_text = obj.received_at.strftime("%I %p")

            return f"Pickup {day_text}, {time_text}"


class RejectedSerializer(serializers.ModelSerializer):
    ref = serializers.SerializerMethodField()
    service_name = serializers.CharField(source="service.name")

    class Meta:
        model = ServiceRequest
        fields = [
            "id",
            "status",
            "ref",
            "service_name",
            "rejection_reason"  # سبب الرفض
        ] 
    def get_ref(self, obj):
        return f"REF: {obj.refugee.id}"
                  

class PendingSerializer(serializers.ModelSerializer):
    ref = serializers.SerializerMethodField()
    service_name = serializers.CharField(source="service.name")
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = [
            "id",
            "status",
            "ref",
            "service_name",
            "created_at"  # وقت إرسال الطلب
        ]       
    def get_ref(self, obj):
        return f"REF: {obj.refugee.id}"



    def get_created_at(self, obj):
        diff = now() - obj.created_at

        if diff.days == 0:
            return "Submitted Today"

        else:
            return f"Submitted {diff.days}d ago"


#واجهة الطلبات ضمن تطبيق المنظمة
class OrgPendingSerializer(serializers.ModelSerializer):
    refugee_name = serializers.CharField(source="refugee.full_name")
    request_id = serializers.SerializerMethodField()
    service_name = serializers.CharField(source="service.name")
    request_date = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = [
            "id",
            "status",
            "refugee_name",
            "request_id",
            "service_name",
            "location",
            "request_date"
        ]

    def get_request_id(self, obj):
        return f"R-{obj.id}"

    def get_request_date(self, obj):
        return obj.created_at.strftime("%d/%m/%Y")

class OrgRejectedSerializer(serializers.ModelSerializer):
    refugee_name = serializers.CharField(source="refugee.full_name")
    request_id = serializers.SerializerMethodField()
    service_name = serializers.CharField(source="service.name")
    request_date = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = [
            "id",
            "status",
            "refugee_name",
            "request_id",
            "service_name",
            "location",
            "request_date",
            "rejection_reason"
        ]

    def get_request_id(self, obj):
        return f"R-{obj.id}"

    def get_request_date(self, obj):
        return obj.created_at.strftime("%d/%m/%Y")      

class OrgApprovedSerializer(serializers.ModelSerializer):
    refugee_name = serializers.CharField(source="refugee.full_name")
    request_id = serializers.SerializerMethodField()
    service_name = serializers.CharField(source="service.name")
    request_date = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = [
            "id",
            "status",
            "refugee_name",
            "request_id",
            "service_name",
            "location",
            "request_date"
        ]

    def get_request_id(self, obj):
        return f"R-{obj.id}"

    def get_request_date(self, obj):
        return obj.created_at.strftime("%d/%m/%Y")

class OrgCompletedSerializer(serializers.ModelSerializer):
    refugee_name = serializers.CharField(source="refugee.full_name")
    request_id = serializers.SerializerMethodField()
    service_name = serializers.CharField(source="service.name")
    received_date = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = [
            "id",
            "status",
            "refugee_name",
            "request_id",
            "service_name",
            "location",
            "received_date"
        ]

    def get_request_id(self, obj):
        return f"R-{obj.id}"

    def get_received_date(self, obj):
        return obj.received_at.strftime("%d/%m/%Y") if obj.received_at else None
    
#لعرض تفاصيل الطلب ضمن  حساب المنظمة
class RequestDetailsSerializer(serializers.ModelSerializer):
    request_id = serializers.SerializerMethodField()
    refugee_name = serializers.CharField(source='refugee.full_name')
    phone_number = serializers.SerializerMethodField()

    organization_name = serializers.CharField(source='organization.name')
    organization_logo = serializers.SerializerMethodField()

    service_name = serializers.CharField(source='service.name')
    service_icon = serializers.CharField(source='service.icon')

    family_members_count = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = [
            "request_id",
            "status",
            "organization_name",
            "organization_logo",
            "refugee_name",
            "phone_number",
            "service_name",
            "service_icon",
            "location",
            'urgency_level',
            "family_members_count",
            "description",
        ]


    def get_request_id(self, obj):
        return f"R-{obj.id}"

    def get_organization_logo(self, obj):
        request = self.context.get("request")
        if obj.organization.logo:
            return request.build_absolute_uri(obj.organization.logo.url)
        return None

    def get_phone_number(self, obj):
        phone = obj.refugee.phone_number
        return f"+963 {phone}"


    def get_family_members_count(self, obj):
        return sum(member.count for member in obj.refugee.family_members.all())    

#كرمال زر قبول الطلب
class ApproveButtonSerializer(serializers.Serializer):
    message = serializers.CharField()

#كرمال زر رفض الطلب
class RejectButtonSerializer(serializers.Serializer):
    rejection_reason = serializers.CharField(required=True)         