from django.urls import path
from .views import service_request_form
from .views import VolunteerHomeAPIView , VolunteerTasksAPIView , TaskUpdateAPIView,service_request_form_two
urlpatterns = [
path("organizations/<int:organization_id>/services/<int:service_id>/request/",service_request_form),
path("organizations/<int:organization_id>/request/", service_request_form_two),
path('volunteer/home/', VolunteerHomeAPIView.as_view()),
path('volunteer/tasks/', VolunteerTasksAPIView.as_view()),
path('volunteer/tasks/<int:id>/update/', TaskUpdateAPIView.as_view()),

]






