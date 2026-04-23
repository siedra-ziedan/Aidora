from django.urls import path
from .views import service_request_form
from .views import VolunteerHomeAPIView , VolunteerTasksAPIView , TaskUpdateAPIView,service_request_form_two
#شهد
from .views import OrganizationServicesAPIView
from .views import OrganizationServicesAPIView
from .views import MyRequestsAPIView
from .views import ServiceRequestDetailAPIView
from .views import ScanQRAPIView
from .views import RequestsListAPIView
from .views import CreateRequestAPIView
from .views import OrganizationRequestsAPIView
from .views import RequestDetailsAPIView
from .views import ApproveButtonAPIView
from .views import RejectButtonAPIView
urlpatterns = [
path("organizations/<int:organization_id>/services/<int:service_id>/request/",service_request_form),
path("organizations/<int:organization_id>/request/", service_request_form_two),
path('volunteer/home/', VolunteerHomeAPIView.as_view()),
path('volunteer/tasks/', VolunteerTasksAPIView.as_view()),
path('volunteer/tasks/<int:id>/update/', TaskUpdateAPIView.as_view()),
#شهد
path('<int:pk>/services/', OrganizationServicesAPIView.as_view()),
path('<int:pk>/createrequest/', CreateRequestAPIView.as_view()),
path("my-requests/", MyRequestsAPIView.as_view()),
path("<int:pk>/details/", ServiceRequestDetailAPIView.as_view()),
path('scan-qr/', ScanQRAPIView.as_view()),
path('list/', RequestsListAPIView.as_view(), name="requests-list"),
    #api/requests/list/?status=Approved(حالة الطلب يلي بدي فلتر عليها)/
    
#خاصين بتطبيق المنظمة
path('org/requests/', OrganizationRequestsAPIView.as_view()),
path('org/requests/<int:pk>/', RequestDetailsAPIView.as_view()),
path('org/requests/<int:pk>/approve/', ApproveButtonAPIView.as_view()),
path('org/requests/<int:pk>/reject/', RejectButtonAPIView.as_view()),

]













