from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import RefugeeProfile ,RefugeeFamilyMember,VolunteerProfile
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import VolunteerApplication
from organizations.models import Organization, OrganizationService
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import RefugeeProfile, VolunteerProfile

User = get_user_model()
class RegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    phone_number = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        user = User.objects.filter(email=value).first()
        if user:
            raise serializers.ValidationError("Account already exists with this email")
        return value

    def create(self, validated_data):
        role = self.context.get("role")
        email = validated_data["email"]

        # إنشاء المستخدم
        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data["password"],
            role=role
        )

        # إنشاء بروفايل فارغ حسب الدور
        if role == "refugee":
          profile = user.refugee_profile
          profile.full_name = validated_data["full_name"]
          profile.phone_number = validated_data["phone_number"]
          profile.profile_completed = False
          profile.save()

        elif role == "volunteer":
           profile = user.volunteer_profile  # جاي من الـ signal
           profile.full_name = validated_data["full_name"]
           profile.phone_number = validated_data["phone_number"]
           profile.profile_completed = False
           profile.save()
        return user

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # هنا ممكن تضيف حقول إضافية مثل role
        token['role'] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # إضافة role في response
        data['role'] = self.user.role
        # الآن data يحتوي على 'access', 'refresh', 'role'
        return data


class RefugeeProfileCompleteSerializer(serializers.Serializer):

    gender = serializers.CharField()
    date_of_birth = serializers.DateField()
    location = serializers.CharField()
    sector_name = serializers.CharField(required=False)
    consent_given = serializers.BooleanField()
    family_members = serializers.ListField(child=serializers.DictField())

    def update(self, instance, validated_data):

        instance.gender = validated_data["gender"]
        instance.date_of_birth = validated_data["date_of_birth"]
        instance.location = validated_data["location"]
        instance.sector_name = validated_data.get("sector_name")
        instance.consent_given = validated_data["consent_given"]
        instance.profile_completed = True
        instance.save()

        family_members = validated_data["family_members"]

        for member in family_members:

            RefugeeFamilyMember.objects.create(
                refugee=instance,
                family_category_id=member["category_id"],
                count=member["count"]
            )
        
        return instance

class VolunteerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = VolunteerProfile
        fields = [
            'gender',
            'date_of_birth',
            'nationality',
            'id_number',
            'current_city',
            'education_level',
            'languages',
            'previous_experience',
            'skills',
            'availability_shift',
            'available_days',
            'start_date',
            'expected_duration',
        ]
        extra_kwargs = {field: {'required': False} for field in fields}

    def to_internal_value(self, data):
        data = data.copy()

        for field in ['skills', 'languages']:
            value = data.get(field)
            if isinstance(value, str):
                data[field] = [item.strip() for item in value.split(',') if item.strip()]

        if 'gender' in data:
          gender = data.get('gender')

          if isinstance(gender, str):
             gender = gender.strip().lower()
             if gender in ['male', 'm']:
                data['gender'] = 'male'         
             elif gender in ['female', 'f', 'fmale']:
                data['gender'] = 'female'
             else:
                raise serializers.ValidationError({
                    "gender": "Invalid gender value"
                })
  
        return super().to_internal_value(data)

class VolunteerApplicationSerializer(serializers.ModelSerializer):
    selected_services = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )

    class Meta:
        model = VolunteerApplication
        fields = [
            'phone_number',
            'why_volunteer',
            'i_commit',
            'i_agree_terms',
            'selected_services'
        ]

    def validate_selected_services(self, value):
        if not value:
            raise serializers.ValidationError(
                "At least one service must be selected."
            )

        organization_id = self.context['organization_id']

        # التأكد أن الخدمات تابعة لنفس المنظمة
        services = OrganizationService.objects.filter(
            id__in=value,
            organization_id=organization_id
        )

        if services.count() != len(value):
            raise serializers.ValidationError(
                "Invalid services for this organization."
            )

        return value

    def create(self, validated_data):
        user = self.context['request'].user
        organization_id = self.context['organization_id']
        selected_services = validated_data.pop('selected_services')

        # منع إرسال طلبين لنفس المنظمة
        if VolunteerApplication.objects.filter(
            user=user,
            organization_id=organization_id
        ).exists():
            raise serializers.ValidationError(
                "You have already submitted an application for this organization."
            )

        # إنشاء الطلب
        application = VolunteerApplication.objects.create(
            user=user,
            organization_id=organization_id,
            **validated_data
        )

        # ربط الخدمات المختارة
        application.selected_services.set(selected_services)

        return application
    



class VolunteerApplicationReadOnlySerializer(serializers.ModelSerializer):
    selected_services = serializers.StringRelatedField(many=True)  # أسماء الخدمات بدل الـ IDs
    user_profile = serializers.SerializerMethodField()

    class Meta:
        model = VolunteerApplication
        fields = [
            'phone_number',
            'why_volunteer',
            'i_commit',
            'i_agree_terms',
            'selected_services',
            'status',
            'user_profile'
        ]
        read_only_fields = fields  # كل الحقول للقراءة فقط

    def get_user_profile(self, obj):
        profile = getattr(obj.user, "volunteer_profile", None)

        if profile:
            return {
            # الواجهة الأولى
             "full_name": profile.full_name,
             "gender": profile.gender,
             "date_of_birth": profile.date_of_birth,
             "nationality": profile.nationality,
             "id_number": profile.id_number,
             "current_city": profile.current_city,

             # واجهة skills
             "education_level": profile.education_level,
             "languages": profile.languages,
             "previous_experience": profile.previous_experience,
             "skills": profile.skills,

             # واجهة availability
             "availability_shift": profile.availability_shift,
             "available_days": profile.available_days,
             "start_date": profile.start_date,
             "expected_duration": profile.expected_duration,
         }

            return None

import qrcode
from io import BytesIO
import base64
class VolunteerQRSerializer(serializers.ModelSerializer):
    qr_image_base64 = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = VolunteerProfile
        fields = ['qr_code', 'profile_image', 'qr_image_base64', 'display_name']

    def get_display_name(self, obj):
        # الاسم الظاهر للـ QR
        name = obj.full_name if obj.full_name else obj.user.username
        return f"@{name.replace(' ', '')}"

    def get_qr_image_base64(self, obj):
        if not obj.qr_code:
            return None

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(obj.qr_code)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
# كرمال عرض بروفايل المتطوع اول ما يفوت
class VolunteerProfileViewSerializer(serializers.ModelSerializer):
    join_date = serializers.SerializerMethodField()
    tasks_count=serializers.IntegerField(read_only=True)
    class Meta:
        model = VolunteerProfile
        fields = [
            "full_name",
            "profile_image",
            "tasks_count",
            "points",
            "skills",
            "languages",
            "previous_experience",
            "join_date",
        ]


    def get_join_date(self, obj):
        return obj.created_at.strftime("%b %Y")


#شهد
from rest_framework import serializers
from .models import RefugeeProfile
from .models import Notification

class RefugeeProfileSerializer(serializers.ModelSerializer):
    refugee_id = serializers.SerializerMethodField()
    profile_image=serializers.SerializerMethodField()
    children_count = serializers.SerializerMethodField()
    elderly_count = serializers.SerializerMethodField()
    disabled_count = serializers.SerializerMethodField()
    women_count = serializers.SerializerMethodField()
    total_family_members = serializers.SerializerMethodField()

    class Meta:
        model = RefugeeProfile
        fields = [
            'refugee_id',
            'profile_image',
            'full_name', 
            'location',
            'sector_name',
            'children_count',
            'elderly_count',
            'disabled_count',
            'women_count',
            'total_family_members',
        ]

    def get_refugee_id(self, obj):
        return f"ID : #{obj.id}"    
     
    def get_profile_image(self, obj):
        request = self.context.get("request")
        if obj.profile_image:
            return request.build_absolute_uri(obj.profile_image.url)
        return None


    def get_family_count(self, obj, category_name):
        member = obj.family_members.filter(category__name__iexact=category_name).first()
        return member.count if member else 0

    def get_children_count(self, obj):
        return self.get_family_count(obj, 'Child')

    def get_elderly_count(self, obj):
        return self.get_family_count(obj, 'Elderly')

    def get_disabled_count(self, obj):
        return self.get_family_count(obj, 'Disabled')

    def get_women_count(self, obj):
        return self.get_family_count(obj, 'Women')

    def get_total_family_members(self, obj):
        return sum(member.count for member in obj.family_members.all())



class NotificationSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "message",
            "created_at",
            "notification_type",
        ]

    def get_created_at(self, obj):
        return obj.created_at.strftime("%b %d, %Y • %I:%M %p")                