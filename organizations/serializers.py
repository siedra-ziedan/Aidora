from rest_framework import serializers
from .models import OrganizationService



          
class OrganizationServiceSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name')

    class Meta:
        model = OrganizationService
        fields = [
            'id',
            'service_name'
        ]

from accounts.models import VolunteerApplication
class OrganizationVolunteerApplicationSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    service_name = serializers.SerializerMethodField()
    service_icon = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    current_city = serializers.SerializerMethodField()
    class Meta:
        model = VolunteerApplication
        fields = [
            'id',
            'full_name',
            'service_name',
            'service_icon',
            'created_at',
            'current_city',
            'status',
        ]

    # 🔹 اسم المتطوع
    def get_full_name(self, obj):
        return obj.user.volunteer_profile.full_name

    # 🔹 أول خدمة مختارة
    def get_service_name(self, obj):
        first_service = obj.selected_services.first()
        if first_service:
            return first_service.service.name
        return None

    # 🔹 أيقونة الخدمة
    def get_service_icon(self, obj):
        first_service = obj.selected_services.first()
        if first_service and first_service.service.icon:
            request = self.context.get('request')
            return request.build_absolute_uri(first_service.service.icon.url)
        return None

    # 🔹 التاريخ بصيغة Oct 24, 2023
    def get_created_at(self, obj):
        return obj.created_at.strftime("%b %d, %Y")

    # 🔹 المدينة
    def get_current_city(self, obj):
        return obj.user.volunteer_profile.current_city


from rest_framework import serializers
from django.utils.timezone import now
from accounts.models import VolunteerApplication, VolunteerProfile

class ApplicationMetaSerializer(serializers.ModelSerializer):
    service_name = serializers.SerializerMethodField()
    service_icon = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    status = serializers.CharField()

    class Meta:
        model = VolunteerApplication
        fields = [
            'service_name',
            'service_icon',
            'created_at',
            'status',
        ]

    # 🔹 كل الخدمات (list)
    def get_service_name(self, obj):
        return [s.service.name for s in obj.selected_services.all()]
    def get_service_icon(self, obj):
      request = self.context.get('request')

      icons = []
      for s in obj.selected_services.all():
        if s.service.icon:
            icons.append(request.build_absolute_uri(s.service.icon.url))

      return icons

    # 🔹 date format
    def get_created_at(self, obj):
        return obj.created_at.strftime("%b %d, %Y")
    
class VolunteerProfileSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()

    class Meta:
        model = VolunteerProfile
        fields = [
            'profile_image',
            'age',
            'nationality',
            'current_city',
            'availability_shift',
            'available_days',
            'start_date',
            'expected_duration',
            'languages',
            'education_level',
            'previous_experience',
            'phone_number'

        ]

    def get_age(self, obj):
        if obj.date_of_birth:
            today = now().date()
            age = today.year - obj.date_of_birth.year - (
                (today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day)
            )
            return f"{age} years"
        return None
    
class VolunteerApplicationDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.volunteer_profile.full_name')
    email = serializers.EmailField(source='user.email')
    Emergency= serializers.CharField(source='phone_number')
    profile = VolunteerProfileSerializer(source='user.volunteer_profile')
    meta = ApplicationMetaSerializer(source='*')

    class Meta:
        model = VolunteerApplication
        fields = [
            'id',
            'full_name',
            'email',
            'Emergency',
            'why_volunteer',

            # nested
            'profile',
            'meta',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # 🔹 flatten profile
        profile = data.pop('profile', {})
        data.update(profile)

        # 🔹 flatten meta
        meta = data.pop('meta', {})
        data.update(meta)

        # 🔹 ID format
        data['id'] = f"ID {str(instance.id).zfill(4)}"

        return data


from requests.models import ServiceRequest,Task
class OrganizationRequestSerializer(serializers.ModelSerializer):
    refugee_id = serializers.SerializerMethodField()
    service_type = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = [
            'id'
            'refugee_id',
            'location',
            'service_type',
            'created_at',
        ]

    def get_refugee_id(self, obj):
        return f"R-{str(obj.id).zfill(4)}"

    def get_service_type(self, obj):
        return obj.service.service_type

    def get_created_at(self, obj):
        return obj.created_at.strftime("%d/%b/%Y")
    
from django.utils.timezone import now

class OrganizationTaskSerializer(serializers.ModelSerializer):
    volunteer_id = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    current_city = serializers.SerializerMethodField()
    time_since_completed = serializers.SerializerMethodField()
    report_reviewed=serializers.BooleanField()
    class Meta:
        model = Task
        fields = [
            'id'
            'title',
            'volunteer_id',
            'full_name',
            'current_city',
            'time_since_completed',
            'report_reviewed',
        ]

    def get_volunteer_id(self, obj):
        if obj.volunteer_id:
            return f"#{obj.volunteer_id.id}"
        return None

    def get_full_name(self, obj):
        if obj.volunteer_id:
            return obj.volunteer_id.full_name
        return None

    def get_current_city(self, obj):
        if obj.volunteer_id:
            return obj.volunteer_id.current_city
        return None

    def get_time_since_completed(self, obj):
        diff = now() - obj.updated_at
        seconds = int(diff.total_seconds())

        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        elif seconds < 86400:
            return f"{seconds // 3600}h ago"
        else:
            return f"{seconds // 86400}d ago"



class TaskReportSerializer(serializers.ModelSerializer):
    location = serializers.CharField(source='service_request_id.location')
    full_name = serializers.CharField(source='volunteer_id.full_name')
    points = serializers.IntegerField(source='volunteer_id.points')
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'title',
            'instructions',
            'location',
            'full_name',
            'points',
            'created_at',
        ]

    def get_created_at(self, obj):
        return obj.created_at.strftime("%A, %b %d•%I:%M %p")
    


class AssignTaskGetSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name')
    service_icon = serializers.SerializerMethodField()
    sector = serializers.CharField(source='refugee.sector')
    volunteers = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = [
            'id',
            'service_name',
            'service_icon',
            'sector',
            'volunteers'
        ]

    def get_service_icon(self, obj):
        request = self.context.get('request')
        if obj.service.icon:
            return request.build_absolute_uri(obj.service.icon.url)
        return None

    def get_volunteers(self, obj):
        request = self.context.get('request')
        search = request.query_params.get('search', '')

        volunteers = VolunteerProfile.objects.filter(
            organization=request.user.organization
        )

        if search:
            volunteers = volunteers.filter(
                full_name__istartswith=search
            )

        return [
            {
                "id": v.id,
                "full_name": v.full_name
            }
            for v in volunteers
        ]
class AssignTaskResponseSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='volunteer_id.full_name')
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'full_name',
            'title',
            'created_at'
        ]

    def get_created_at(self, obj):
        return obj.created_at.strftime("%b %d,%Y• %I:%M %p")    
    

class TaskSerializer(serializers.ModelSerializer):
    volunteer_full_name = serializers.CharField(source='volunteer_id.full_name')
    volunteer_profile_image = serializers.CharField(source='volunteer_id.profile_image')
    location = serializers.CharField(source='service_request_id.location')
    service_request_status = serializers.CharField(source='service_request_id.status')
    rejection_reason = serializers.CharField(source='rejection_reason', allow_null=True, required=False)

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'volunteer_full_name',
            'volunteer_profile_image',
            'location',
            'service_request_status',
            'rejection_reason',
        ]
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        # إذا rejection_reason = null، إمسح الحقل
        if data.get('rejection_reason') is None:
            del data['rejection_reason']
        
        return data


#قسم شهد
from rest_framework import serializers
from .models import Service
from .models import Organization, Service, TargetGroup, OrganizationService
from .models import OrganizationTargetGroup


# Serializer للخدمات
class ServiceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['service_type','icon']  


#لعرض المنظمات
class OrganizationCardSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organization
        fields = [ 'name', "logo","id"]

#لعرض معلومات المنظمة
class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["name", "description" ,"icon"]  # هنا الاسم والوصف فقط


class TargetGroupSerializer(serializers.ModelSerializer):
    
    name = serializers.CharField(source="target_group.name")

    class Meta:
        model = OrganizationTargetGroup
        fields = ["name"]

class OrganizationDetailSerializer(serializers.ModelSerializer):
    services = serializers.SerializerMethodField()
    target_groups = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "name",
            "title",
            "logo",
            "about",
            "official_website",
            "contact_email",
            "impact_image1",
            "impact_image2",
            "services",
            "target_groups",
        ]

    def get_services(self, obj):
        org_services = OrganizationService.objects.filter(organization=obj)
        return ServiceSerializer([os.service for os in org_services], many=True).data

    def get_target_groups(self, obj):
        org_targets = OrganizationTargetGroup.objects.filter(organization=obj)
        return [ot.target_group.name for ot in org_targets]


#للفلترة حسب الخدمة
class OrganizationSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["name", "logo","id"]  # بس الاسم واللوغو        

