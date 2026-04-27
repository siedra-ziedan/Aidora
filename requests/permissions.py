
from rest_framework.permissions import BasePermission

class IsProfileCompleted(BasePermission):
    message = "You must complete your profile first."

    def has_permission(self, request, view):

        if request.method == "GET":
            return True

        profile = getattr(request.user, "refugee_profile", None)

        if not profile:
            return False

        return profile.profile_completed is True