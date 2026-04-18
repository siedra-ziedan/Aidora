from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from organizations.models import Service, Organization, OrganizationService
from .models import ServiceRequest
from .serializers import ServiceRequestCreateSerializer
from accounts.permissions import IsRole
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@permission_classes([IsRole])
def service_request_form(request, organization_id, service_id):
    """
    API لعرض الاستمارة وإرسال طلب خدمة.
    GET: يعرض اسم الخدمة ووصفها حسب المنظمة.
    POST: ينشئ طلب خدمة بعد التحقق أن الخدمة مرتبطة بالمنظمة.
    """

    try:
        organization = Organization.objects.get(id=organization_id)
    except Organization.DoesNotExist:
        return Response({"error": "Organization not found"}, status=404)

    # تحقق أن الخدمة تابعة للمنظمة
    if not OrganizationService.objects.filter(
        organization=organization,
        service_id=service_id
    ).exists():
        return Response(
            {"error": "This service does not belong to the organization."},
            status=status.HTTP_400_BAD_REQUEST
        )

    service = Service.objects.get(id=service_id)

    # GET: عرض بيانات الخدمة
    if request.method == "GET":
        return Response({
            "service_name": service.name,
            "service_description": service.description
        })

    # POST: إرسال طلب الخدمة
    if request.method == "POST":
        refugee = request.user.refugee_profile

        serializer = ServiceRequestCreateSerializer(data=request.data)
        if serializer.is_valid():
            request_obj = serializer.save(
                refugee=refugee,
                service=service,
                organization=organization,
                status="pending"
            )

            return Response({
                "message": "Request sent successfully",
                "request_id": request_obj.id
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
service_request_form.allowed_roles = ["refugee"]
    
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Q
from .models import Task

class VolunteerHomeAPIView(APIView):
    permission_classes = [IsAuthenticated, IsRole]
    allowed_roles = ["volunteer"]

    def get(self, request):
        volunteer = request.user.volunteer_profile

        # 🔹 معلومات المتطوع
        full_name = volunteer.full_name
        profile_image = volunteer.profile_image

        # 🔹 كل المهام تبعه
        tasks = Task.objects.filter(volunteer_id=volunteer)

        # 🔹 الإحصائيات
        stats = tasks.aggregate(
            completed=Count('id', filter=Q(status='completed')),
            failed=Count('id', filter=Q(status='failed')),
            pending=Count('id', filter=Q(status='pending')),
        )

        # 🔹 آخر 3 مهام (الأحدث)
        last_tasks = tasks.select_related('service_request_id__service')\
                          .order_by('-created_at')[:3]

        from .serializers import TaskHomeSerializer
        last_tasks_data = TaskHomeSerializer(
            last_tasks,
            many=True,
            context={'request': request}  # 🔥 مهم
        ).data

        return Response({
            "full_name": full_name,
            "profile_image": profile_image,
            "statistics": stats,
            "recent_tasks": last_tasks_data
        })

from rest_framework.generics import ListAPIView
from .serializers import TaskListSerializer

class VolunteerTasksAPIView(ListAPIView):
    serializer_class = TaskListSerializer
    permission_classes=[IsAuthenticated,IsRole]
    allowed_roles = ["volunteer"]

    def get_queryset(self):
        volunteer = self.request.user.volunteer_profile
        status_filter = self.request.query_params.get('status', 'all')

        queryset = Task.objects.filter(
            volunteer_id=volunteer
        ).select_related('service_request_id')

        if status_filter != 'all':
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)        


class TaskUpdateAPIView(APIView):
    permission_classes=[IsAuthenticated,IsRole]
    allowed_roles = ["volunteer"]

    def get(self, request, id):
        volunteer = request.user.volunteer_profile

        try:
            task = Task.objects.get(id=id, volunteer_id=volunteer, status='pending')
        except Task.DoesNotExist:
            return Response({"error": "Task not found"}, status=404)

        return Response({
            "title": task.title,
            "request_display": f"Request#{str(task.service_request_id.id).zfill(4)}"
        })
    def patch(self, request, id):
      volunteer = request.user.volunteer_profile

      try:
        task = Task.objects.get(id=id, volunteer_id=volunteer)
      except Task.DoesNotExist:
        return Response({"error": "Task not found"}, status=404)

      if task.status != 'pending':
        return Response({"error": "Only pending tasks can be updated"}, status=400)

      new_status = request.data.get('status')
      reason = request.data.get('rejection_reason')

      if new_status not in ['completed', 'failed']:
        return Response({"error": "Invalid status"}, status=400)

      if new_status == 'failed':
        if not reason:
            return Response({"error": "Reason required"}, status=400)
        task.rejection_reason = reason

      elif new_status == 'completed':
        task.rejection_reason = None

      task.status = new_status
      task.save()  # 🔥 updated_at بيتحدث هون تلقائي

      from .serializers import TaskSerializer
      serializer = TaskSerializer(task, context={'request': request})
      return Response(serializer.data)
    
    
from .serializers import ServiceRequestCreateSecondSerializer
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@permission_classes([IsRole])
def service_request_form_two(request, organization_id):
    """
    GET: يعرض قائمة الخدمات التابعة للمنظمة (id + name)
    POST: ينشئ طلب خدمة بعد اختيار واحدة من هذه الخدمات
    """
    try:
        organization = Organization.objects.get(id=organization_id)
    except Organization.DoesNotExist:
        return Response({"error": "Organization not found"}, status=404)

    if request.method == "GET":
        # جلب جميع الخدمات المرتبطة بالمنظمة
        services = OrganizationService.objects.filter(organization=organization)
        data = [{"id": s.service.id, "name": s.service.name} for s in services]
        return Response({"services": data})

    if request.method == "POST":
        refugee = request.user.refugee_profile
        service_id = request.data.get("service_id")  # النازح يرسل id الخدمة
        if not service_id:
            return Response({"error": "service_id is required"}, status=400)

        # تحقق أن الخدمة ضمن المنظمة
        if not OrganizationService.objects.filter(
            organization=organization, service_id=service_id
        ).exists():
            return Response(
                {"error": "This service does not belong to the organization."},
                status=400
            )

        service = Service.objects.get(id=service_id)
        serializer = ServiceRequestCreateSecondSerializer(data=request.data)
        if serializer.is_valid():
            request_obj = serializer.save(
                refugee=refugee,
                service=service,
                organization=organization,
                status="pending"
            )
            return Response({
                "message": "Request sent successfully",
                "request_id": request_obj.id
            }, status=201)
        return Response(serializer.errors, status=400)    
service_request_form_two.allowed_roles = ["refugee"]
    

    