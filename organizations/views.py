from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from organizations.models import OrganizationService
from .serializers import OrganizationServiceSerializer
from rest_framework.decorators import api_view
from .models import Organization
from accounts.permissions import IsRole
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated


class OrganizationServicesView(APIView):  
    permission_classes = [IsRole,IsAuthenticated]
    allowed_roles = ["volunteer"]
    def get(self, request, id):

        services = OrganizationService.objects.filter(
            organization_id=id
        ).select_related('service')

        serializer = OrganizationServiceSerializer(services, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    

from accounts.models import VolunteerApplication
from .serializers import VolunteerApplicationDetailSerializer
from django.utils.timezone import now    
from django.shortcuts import get_object_or_404

class OrganizationApplicationsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsRole]
    allowed_roles = ["organization"]

    def get(self, request):
        organization = request.user.organization

        status_filter = request.query_params.get('status')

        applications = VolunteerApplication.objects.filter(
            organization=organization
        ).select_related(
            'user',
            'user__volunteer_profile'
        ).prefetch_related(
            'selected_services__service'
        ).order_by('-id')

        # 🔹 الفلترة (للتوبات)
        if status_filter and status_filter != "all":
            applications = applications.filter(status=status_filter)

        serializer = VolunteerApplicationDetailSerializer(
            applications,
            many=True,
            context={'request': request}
        )

        return Response({
            "applications": serializer.data
        })
    
    def patch(self, request, pk):
      organization = request.user.organization

      application = get_object_or_404(
        VolunteerApplication,
        id=pk,
        organization=organization
        )

    # ❌ فقط pending
      if application.status != "pending":
        return Response({
            "error": "Only pending applications can be updated"
        }, status=400)

      new_status = request.data.get("status")

      if new_status not in ["approved", "rejected"]:
        return Response({
            "error": "Invalid status"
        }, status=400)

      application.status = new_status
      application.processed_at = now()
      application.save()

    # 🔥 هون بتحطيه بدل message
      serializer = VolunteerApplicationDetailSerializer(
        application,
        context={'request': request}
       )
      return Response(serializer.data)



from django.db.models import Count
from requests.models import ServiceRequest,Task
from django.db.models import Q
from .serializers import OrganizationRequestSerializer,OrganizationTaskSerializer
class OrganizationDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsRole]
    allowed_roles = ["organization"]

    def get(self, request):
        organization = request.user.organization

        # 🔹 Statistics
        stats = ServiceRequest.objects.filter(
            organization=organization
        ).aggregate(
            pending=Count('id', filter=Q(status='pending')),
            approved=Count('id', filter=Q(status='approved')),
            completed=Count('id', filter=Q(status='completed')),
        )

        # 🔹 Latest 3 requests
        latest_requests = ServiceRequest.objects.filter(
            organization=organization
        ).select_related(
            'service'
        ).order_by('-created_at')[:3]

        requests_serializer = OrganizationRequestSerializer(
            latest_requests,
            many=True
        )

        # 🔹 Completed Tasks
        tasks = Task.objects.filter(
            service_request_id__organization=organization,
            status='completed'
        ).select_related(
            'volunteer_id'
        ).order_by('-updated_at')

        tasks_serializer = OrganizationTaskSerializer(tasks, many=True)
        
        return Response({
        "pending": stats["pending"],
        "approved": stats["approved"],
        "completed": stats["completed"],
        "requests": requests_serializer.data,
        "tasks": tasks_serializer.data
})
    





from .serializers import TaskReportSerializer
class TaskReportAPIView(APIView):
    permission_classes = [IsAuthenticated, IsRole]
    allowed_roles = ["organization"]

    def get_object(self, pk):
        return Task.objects.select_related(
            'service_request_id',
            'volunteer_id'
        ).get(id=pk)

    def get(self, request, pk):
        task = get_object_or_404(Task, id=pk)

        # 🔐 حماية
        if task.status != 'completed' or task.service_request_id.status != 'completed':
            return Response(
                {"error": "Report not available until completion"},
                status=403
            )

        serializer = TaskReportSerializer(task)
        return Response(serializer.data)

    def patch(self, request, pk):
      task = get_object_or_404(Task, id=pk)

    # 🔐 حماية الحالة
      if task.status != 'completed' or task.service_request_id.status != 'completed':
        return Response(
            {"error": "Cannot update before completion"},
            status=403
        )

    # 🚫 منع إعادة التقييم
      if task.report_reviewed:
        return Response(
            {"error": "Already reviewed"},
            status=400
        )

      volunteer = task.volunteer_id
      if not volunteer:
        return Response({"error": "No volunteer assigned"}, status=400)

      points = request.data.get("points")

      if not isinstance(points, int):
        return Response({"error": "Points must be integer"}, status=400)

    # 🔥 تخزين القيمة الجديدة
      volunteer.points = points
      volunteer.save()

    # 🔥 هون النقطة يلي بدك ياها 👇
      task.report_reviewed = True
      task.save()

      serializer = TaskReportSerializer(task)
      return Response(serializer.data)
    
from .serializers import AssignTaskGetSerializer, AssignTaskResponseSerializer
from accounts.models import VolunteerProfile
class AssignTaskAPIView(APIView):
    permission_classes = [IsAuthenticated, IsRole]
    allowed_roles = ["organization"]

    def get(self, request, request_id):
        service_request = get_object_or_404(
            ServiceRequest,
            id=request_id,
            organization=request.user.organization
        )

        serializer = AssignTaskGetSerializer(
            service_request,
            context={'request': request}
        )

        return Response(serializer.data)

    def post(self, request, request_id):
        service_request = get_object_or_404(
            ServiceRequest,
            id=request_id,
            organization=request.user.organization
        )

        # 🔐 لازم يكون approved
        if service_request.status != 'approved':
            return Response(
                {"error": "Request must be approved first"},
                status=400
            )

        # ❌ منع أكثر من Task
        if Task.objects.filter(service_request_id=service_request).exists():
            return Response(
                {"error": "Task already assigned"},
                status=400
            )

        volunteer_id = request.data.get("volunteer_id")
        title = request.data.get("title")
        instructions = request.data.get("instructions")

        volunteer = get_object_or_404(
            VolunteerProfile,
            id=volunteer_id,
            organization=request.user.organization
        )

        task = Task.objects.create(
            service_request_id=service_request,
            volunteer_id=volunteer,
            title=title,
            instructions=instructions
        )

        serializer = AssignTaskResponseSerializer(task)
        return Response(serializer.data, status=201)    
    

    
from .serializers import TaskSerializer
class TaskListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsRole]
    allowed_roles = ["organization"]

    def get(self, request):
        # 🔹 Filter by organization
        tasks = Task.objects.filter(
            service_request_id__organization=request.user.organization
        ).select_related(
            'volunteer_id', 'service_request_id'
        )

        # 🔹 Statistics (counts for each status)
        stats = tasks.aggregate(
            pending=Count('id', filter=Q(status='pending')),
            completed=Count('id', filter=Q(status='completed')),
            failed=Count('id', filter=Q(status='failed'))
        )

        # 🔹 Serialize tasks
        task_serializer = TaskSerializer(tasks, many=True)

        return Response({
        "pending": stats["pending"],
        "approved": stats["failed"],
        "completed": stats["completed"],
        "tasks": task_serializer.data
        })
    









