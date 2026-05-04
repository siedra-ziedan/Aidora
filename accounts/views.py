from django.shortcuts import render

# Create your views here.
from django.contrib.auth import authenticate, get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
import jwt
from django.conf import settings
from .serializers import RefugeeProfileCompleteSerializer
from .serializers import RegisterSerializer
from rest_framework.permissions import IsAuthenticated
from .models import RefugeeProfile
from rest_framework import generics, permissions
from .models import VolunteerProfile
from .serializers import ( VolunteerProfileSerializer ,VolunteerApplicationSerializer,
                         VolunteerProfileViewSerializer, VolunteerApplicationReadOnlySerializer)    
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.utils import get_or_create_pin
from django.utils import timezone
from .models import VolunteerApplication
from rest_framework.generics import RetrieveAPIView
from rest_framework.viewsets import ViewSet
from .permissions import IsRole
User = get_user_model()

@api_view(['POST'])
def login_api(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response(
            {"error": "Email and password are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"error": "Email does not exist"}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=user.username, password=password)
    if user is None:
        return Response({"error": "Incorrect password"}, status=status.HTTP_400_BAD_REQUEST)

    # Generate tokens using Simple JWT
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)           

    return Response({
        "access": access_token,
        "refresh": refresh_token,
        "role": user.role
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response({"message": "Logged out successfully"}, status=status.HTTP_205_RESET_CONTENT)

    except Exception:
        return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
@api_view(['POST'])
def register_refugee(request):
    serializer = RegisterSerializer(
        data=request.data,
        context={"role": "refugee"}
    )

    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Refugee account created"},
            status=201
        )

    return Response(serializer.errors, status=400)

@api_view(['POST'])
def register_volunteer(request):
    serializer = RegisterSerializer(
        data=request.data,
        context={"role": "volunteer"}
    )

    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Volunteer account created"},
            status=201
        )

    return Response(serializer.errors, status=400)

from rest_framework.views import APIView

class CompleteRefugeeProfileView(APIView):
    permission_classes = [IsAuthenticated, IsRole]
    allowed_roles = ["refugee"]

    def patch(self, request):
        try:
            profile = RefugeeProfile.objects.get(user=request.user)
        except RefugeeProfile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)

        serializer = RefugeeProfileCompleteSerializer(
            profile,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile completed"})

        return Response(serializer.errors, status=400)
class VolunteerProfileViewSet(ViewSet):
    permission_classes = [IsAuthenticated]
    permission_classes = [IsRole]
    allowed_roles = ["volunteer"]
    def get_profile(self, request):
        profile, _ = VolunteerProfile.objects.get_or_create(
            user=request.user
        )
        return profile


    # ✅ PATCH (الواجهة الأولى)
    def update_profile(self, request):
        profile = self.get_profile(request)

        serializer = VolunteerProfileSerializer(
            profile,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    # ✅ PATCH skills
    def update_skills(self, request):
        profile = self.get_profile(request)

        fields = ['education_level', 'languages', 'previous_experience', 'skills']
        data = {f: request.data.get(f) for f in fields if f in request.data}

        serializer = VolunteerProfileSerializer(profile, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    # ✅ PATCH availability
    def update_availability(self, request):
        profile = self.get_profile(request)
        data = request.data.copy() 
        DAY_MAP = {
        'S': 'sunday',
        'M': 'monday',
        'TU': 'tuesday',
        'W': 'wednesday',
        'TH': 'thursday',
        'F': 'friday',
        'SA': 'saturday',
        }
        if 'available_days' in data:
          data['available_days'] = [
          DAY_MAP.get(day.upper(), day).strip().lower()
          for day in data.get('available_days', [])
              ]      
        if 'availability_shift' in data:
            data['availability_shift'] = data.get('availability_shift').lower()        
        fields = ['availability_shift', 'available_days', 'start_date', 'expected_duration']
        data = {f: data.get(f) for f in fields if f in data}

        serializer = VolunteerProfileSerializer(profile, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_volunteer_application(request, id):

    serializer = VolunteerApplicationSerializer(
        data=request.data,
        context={
            'request': request,
            'organization_id': id
        }
    )

    if serializer.is_valid():
        serializer.save()
        return Response(
            {"detail": "Your request submitted successfully."},
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def auth_me(request):
    user = request.user
    profile_completed = False

    response_data = {
        "role": user.role,
        "profile_completed": False,
    }

    if user.role == "refugee":
        profile = getattr(user, "refugee_profile", None)
        if profile:
            response_data["profile_completed"] = profile.profile_completed

        # ❌ ما منضيف application_status

    elif user.role == "volunteer":
        profile = getattr(user, "volunteer_profile", None)
        if profile:
            response_data["profile_completed"] = profile.profile_completed

        application = VolunteerApplication.objects.filter(user=user).order_by('-id').first()
        response_data["application_status"] = application.status if application else None

    return Response(response_data)






@api_view(['POST'])
@permission_classes([IsAuthenticated])
@permission_classes([IsRole])
def resend_pin(request):
    user = request.user

    # تأكد أنه المستخدم عنده بروفايل متطوع
    profile = getattr(user, "volunteer_profile", None)
    if not profile:
        return Response(
            {"detail": "Volunteer profile not found."},
            status=status.HTTP_400_BAD_REQUEST
        )


    # توليد أو إعادة الـ PIN الحالي إذا صالح
    pin = get_or_create_pin(profile)

    # إرسال البريد
    from django.core.mail import send_mail
    from django.conf import settings
    send_mail(
    subject="Aidora Verification PIN",
    message=f"Your verification PIN is: {pin}",
    from_email=f"Aidora <{settings.EMAIL_HOST_USER}>",
    recipient_list=[user.email],
    )
    return Response({"detail": "Verification PIN resent successfully."}, status=status.HTTP_200_OK)
resend_pin.allowed_roles = ["volunteer"]
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@permission_classes([IsRole])
def verify_pin(request):
    user = request.user
    input_pin = request.data.get('pin')

    if not input_pin:
        return Response({"detail": "PIN is required."}, status=status.HTTP_400_BAD_REQUEST)

    profile = getattr(user, "volunteer_profile", None)
    if not profile:
        return Response({"detail": "Volunteer profile not found."}, status=status.HTTP_400_BAD_REQUEST)

    now = timezone.now()
    if profile.verification_pin != input_pin:
        return Response({"detail": "Invalid PIN."}, status=status.HTTP_400_BAD_REQUEST)
    if profile.pin_expires_at < now:
        return Response({"detail": "PIN has expired."}, status=status.HTTP_400_BAD_REQUEST)

    # ✅ تم التحقق بنجاح
    profile.is_verified = True
    profile.profile_completed = True

    # ✅ اسند organization_id من الطلب الموافق عليه
    from django.shortcuts import get_object_or_404
    from accounts.models import VolunteerApplication
    application = get_object_or_404(
    VolunteerApplication,
    user=user,
    status='approved'
    )
    profile.organization = application.organization
    profile.save()

    return Response({"detail": "PIN verified successfully and organisation assigned."}, status=200)
verify_pin.allowed_roles = ["volunteer"]


from rest_framework.exceptions import NotFound
class VolunteerApplicationDetailView(RetrieveAPIView):
    serializer_class = VolunteerApplicationReadOnlySerializer
    permission_classes = [IsAuthenticated]
    permission_classes = [IsRole]
    allowed_roles = ["volunteer"]

    def get_object(self):
        try:
            return VolunteerApplication.objects.get(
                user=self.request.user,
                organization_id=self.kwargs['id']
            )
        except VolunteerApplication.DoesNotExist:
            raise NotFound("No application found for this organization.")


from .serializers import VolunteerQRSerializer
import uuid
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@permission_classes([IsRole])
def volunteer_qr(request, volunteer_id):

    try:
        profile = VolunteerProfile.objects.get(id=volunteer_id)
    except VolunteerProfile.DoesNotExist:
        return Response({"error": "Volunteer not found"}, status=404)

    # ✅ بعد ما صار موجود فينا نستخدمه
    if not request.user.is_staff and profile.user.id != request.user.id:
        return Response({"error": "You are not allowed to view this QR."}, status=403)

    # توليد QR نصي إذا مش موجود
    if not profile.qr_code:
        # استخدم full_name أو username كاحتياط
        name = profile.full_name 
        profile.qr_code = f"@{name.replace(' ', '')}|{uuid.uuid4().hex[:8]}"
        profile.save()

    serializer = VolunteerQRSerializer(profile)
    return Response(serializer.data)
volunteer_qr.allowed_roles = ["volunteer"]


from django.db.models import Count
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@permission_classes([IsRole])
def volunteer_profile_view(request):
    profile = VolunteerProfile.objects.filter(
        user=request.user
    ).annotate(
        tasks_count=Count('tasks')  # ✅ هون الصح
    ).first()

    if not profile:
        return Response({"error": "Profile not found"}, status=404)

    serializer = VolunteerProfileViewSerializer(profile)
    return Response(serializer.data)
volunteer_profile_view.allowed_roles = ["volunteer"]


from rest_framework.views import APIView
class UploadProfileImageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        profile = request.user.volunteer_profile

        image = request.FILES.get('profile_image')

        if not image:
            return Response(
                {"error": "No image provided"},
                status=400
            )

        # 🔥 حذف الصورة القديمة (إذا موجودة)
        if profile.profile_image:
            profile.profile_image.delete(save=False)

        # 🔥 حفظ الصورة الجديدة
        profile.profile_image = image
        profile.save()

        return Response({
            "message": "Profile image updated successfully",
            "profile_image": request.build_absolute_uri(profile.profile_image.url)
        })


#شهد
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import RefugeeProfile
from .serializers import RefugeeProfileSerializer
from .models import Notification
from .serializers import NotificationSerializer

class RefugeeProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    permission_classes = [IsRole]
    allowed_roles = ["refugee"]
    def get(self, request):
        # مؤقت للاختبار
        #refugee = RefugeeProfile.objects.first()
        
        refugee = request.user.refugee_profile
        serializer = RefugeeProfileSerializer(refugee, context={"request": request})
        return Response(serializer.data)

from django.contrib.auth import get_user_model
#User = get_user_model()

class NotificationListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    permission_classes = [IsRole]
    allowed_roles = ["refugee"]

    def get(self, request):

        notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')

        # 🔥 خلي كل الإشعارات مقروءة
        notifications.update(is_read=True)

        serializer = NotificationSerializer(
            notifications,
            many=True
        )

        return Response({
            "notifications": serializer.data
        })