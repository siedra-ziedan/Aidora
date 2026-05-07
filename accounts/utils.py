#utils.py
from django.utils import timezone
from random import randint
from django.core.mail import send_mail
from django.conf import settings

def get_or_create_pin(volunteer_profile):
    now = timezone.now()
    if volunteer_profile.verification_pin and volunteer_profile.pin_expires_at > now:
        return volunteer_profile.verification_pin
    else:
        pin = f"{randint(1000, 9999)}"
        volunteer_profile.verification_pin = pin
        volunteer_profile.pin_expires_at = now + timezone.timedelta(minutes=10)
        volunteer_profile.save()
        return pin

def send_verification_pin(volunteer_profile):
    """
    دالة مشتركة لإرسال PIN، تستخدم من أي signal
    """
    pin = get_or_create_pin(volunteer_profile)
    send_mail(
        subject="Aidora Verification PIN",
        message=f"Your verification PIN is: {pin}",
        from_email=f"Aidora <{settings.EMAIL_HOST_USER}>",
        recipient_list=[volunteer_profile.user.email],
    )