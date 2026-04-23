from django.urls import path
from .views import OrganizationServicesView 
from .views import OrganizationApplicationsAPIView ,OrganizationDashboardAPIView, TaskReportAPIView ,AssignTaskAPIView,TaskListAPIView
from .views import ReassignTaskAPIView ,MyOrganizationView
#شهد

from .views import ServiceTypeListAPIView
from .views import OrganizationCardListAPIView
from .views import OrganizationDetailAPIView
from .views import OrganizationsByServiceTypeAPIView


urlpatterns = [
    path('<int:id>/services/',OrganizationServicesView.as_view(),name='organization-services' ),
    path('applications/',OrganizationApplicationsAPIView.as_view(),name='organization-applications'),
    path('applications/<int:pk>/update-status/',OrganizationApplicationsAPIView.as_view()),
    path('dashboard/',OrganizationDashboardAPIView.as_view()),
    path('tasks/', TaskListAPIView.as_view(), name='task-list'),
    path('tasks/<int:pk>/report/', TaskReportAPIView.as_view()),
    path('assign-task/<int:request_id>/', AssignTaskAPIView.as_view()),
    path('tasks/<int:task_id>/reassign/', ReassignTaskAPIView.as_view()),
    path('my-organization/', MyOrganizationView.as_view(), name='my-organization'),
#شهد
    #للخدمات
    path('services/', ServiceTypeListAPIView.as_view(), name='service-type-list'),
    #فلترة منظمة حسب الخدمة
    path('filter/<str:service_type>/', OrganizationsByServiceTypeAPIView.as_view()),
    #للمنظمات الستة
    path('cards/', OrganizationCardListAPIView.as_view()),
    #تفاصيل المنظمة
    path('<int:pk>/', OrganizationDetailAPIView.as_view(),
         name='organization-detail'),





]




