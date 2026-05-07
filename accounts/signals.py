from django.dispatch import receiver
from django.conf import settings
from .models import RefugeeProfile, VolunteerProfile
from .models import VolunteerApplication
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from accounts.utils import get_or_create_pin
from django.db.models.signals import post_save
from .utils import send_verification_pin


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == 'refugee':
            RefugeeProfile.objects.create(user=instance)
        elif instance.role == 'volunteer':
            VolunteerProfile.objects.create(user=instance)

@receiver(pre_save, sender=VolunteerApplication)
def handle_application_approval(sender, instance, **kwargs):
    # التحقق من وجود instance قديمة في الـ database
    if not instance.pk:
        return

    try:
        old_instance = VolunteerApplication.objects.get(pk=instance.pk)
    except VolunteerApplication.DoesNotExist:
        return

    # التحقق من التغيير من non-approved إلى approved
    if old_instance.status != "approved" and instance.status == "approved":
        profile = getattr(instance.user, "volunteer_profile", None)

        if profile:
            # ❌ لا نكمل البروفايل هون
            # ✅ بس نربط المنظمة
            profile.organization_id = instance.organization_id
            profile.save()

            # ✅ نبعث PIN
            send_verification_pin(profile)