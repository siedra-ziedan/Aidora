
from rest_framework.permissions import BasePermission
class IsProfileCompleted(BasePermission):
    message = "You must complete your profile first."

    def has_permission(self, request, view):
        if request.method == "GET":
            return True

        if not hasattr(request.user, 'refugee_profile'):
            return False

        return request.user.refugee_profile.profile_completed