from django.urls import path
from .views import login_api ,logout_view, register_refugee , register_volunteer ,submit_volunteer_application,auth_me
from .views import CompleteRefugeeProfileView 
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    VolunteerProfileViewSet,
    VolunteerApplicationDetailView,
   resend_pin ,
   verify_pin,
   volunteer_qr,
   volunteer_profile_view,
   UploadProfileImageAPIView
)
from .views import RefugeeProfileAPIView
from .views import NotificationListAPIView


urlpatterns = [
    # JWT endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/', login_api, name='api-login'),
    path('logout/', logout_view),
    path('register/refugee/', register_refugee),
    path('register/volunteer/', register_volunteer),
    path('refugees/complete-profile/', CompleteRefugeeProfileView.as_view()),
    path(
        'volunteer/profile/',
        VolunteerProfileViewSet.as_view({
            'patch': 'update_profile'
        })
    ),

    path(
        'volunteer/profile/skills/',
        VolunteerProfileViewSet.as_view({
            'patch': 'update_skills'
        })
    ),

    path(
        'volunteer/profile/availability/',
        VolunteerProfileViewSet.as_view({
            'patch': 'update_availability'
        })
    ),
    path('org/<int:id>/volunteer/applications/',submit_volunteer_application, name='volunteer-application'),
    path('org/<int:id>/volunteer/application/details/',VolunteerApplicationDetailView.as_view(),name='volunteer-application-details'),
    path('me/', auth_me, name='auth-me'),
    path('resend-pin/', resend_pin, name='resend-pin'),
    path('verify-pin/', verify_pin, name='verify-pin'),
    path("volunteers/<int:volunteer_id>/qr/", volunteer_qr),
    path("volunteer/profile/view", volunteer_profile_view), #Get
    path('profile/upload-image/',UploadProfileImageAPIView.as_view()),

#شهد
    path('profile/refugee/', RefugeeProfileAPIView.as_view(), name='refugee-profile'),
    path('notifications/', NotificationListAPIView.as_view()),
   
   
    ]







