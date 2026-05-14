from django.dispatch import receiver
from django.conf import settings
from .models import RefugeeProfile, VolunteerProfile, VolunteerApplication
from django.db.models.signals import pre_save, post_save
from .utils import send_verification_pin


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Create minimal profiles with safe default values to avoid
    integrity errors when users are created.
    The full profile fields are filled later by the registration flow.
    """
    if not created:
        return

    if instance.role == 'refugee':
        RefugeeProfile.objects.create(
            user=instance,
            full_name=getattr(instance, 'username', '') or '',
            phone_number='',
            gender='male',
            location='',
            profile_completed=False,
        )

    elif instance.role == 'volunteer':
        VolunteerProfile.objects.create(
            user=instance,
            full_name=getattr(instance, 'username', '') or '',
            verification_pin='',
            phone_number='',
            gender='male',
            nationality='',
            id_number='',
            current_city='',
            education_level='',
            availability_shift='morning',
            expected_duration='',
            profile_completed=False,
        )

@receiver(pre_save, sender=VolunteerApplication)
def handle_application_approval(sender, instance, **kwargs):
    # if this is a new instance (no PK yet), nothing to compare
    if not instance.pk:
        return

    try:
        old_instance = VolunteerApplication.objects.get(pk=instance.pk)
    except VolunteerApplication.DoesNotExist:
        return

    # detect transition to approved
    if old_instance.status != "approved" and instance.status == "approved":
        profile = getattr(instance.user, "volunteer_profile", None)
        if profile:
            profile.organization_id = instance.organization_id
            profile.save()
            send_verification_pin(profile)