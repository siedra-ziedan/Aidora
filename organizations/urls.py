from django.urls import path
from .views import OrganizationServicesView 
from .views import OrganizationApplicationsAPIView ,OrganizationDashboardAPIView, TaskReportAPIView ,AssignTaskAPIView,TaskListAPIView





urlpatterns = [
    path('<int:id>/services/',OrganizationServicesView.as_view(),name='organization-services' ),
    path('applications/',OrganizationApplicationsAPIView.as_view(),name='organization-applications'),
    path('applications/<int:pk>/update-status/',OrganizationApplicationsAPIView.as_view()),
    path('dashboard/',OrganizationDashboardAPIView.as_view()),
    path('tasks/', TaskListAPIView.as_view(), name='task-list'),
    path('tasks/<int:pk>/report/', TaskReportAPIView.as_view()),
    path('assign-task/<int:request_id>/', AssignTaskAPIView.as_view()),
  



   

]