from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.contrib.postgres.fields import ArrayField

class User(AbstractUser):

    email = models.EmailField(unique=True)

    ROLE_CHOICES = (
        ('refugee', 'Refugee'),
        ('volunteer', 'Volunteer'),
        ('organization', 'Organization'),
    )
    accept_terms = models.BooleanField(default=False)  
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    otp_code = models.CharField(
    max_length=6,
    null=True,
    blank=True)

    otp_expires_at = models.DateTimeField(
    null=True,
    blank=True)

    is_verified = models.BooleanField(default=False)
class RefugeeProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='refugee_profile'
    )
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    gender = models.CharField(max_length=10, choices=(('male','Male'),('female','Female')))
    date_of_birth = models.DateField(null=True,blank=True)
    location = models.CharField(max_length=255)
    sector_name = models.CharField(max_length=255, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    consent_given = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    profile_completed = models.BooleanField(default=False)
    def  __str__(self):
        return self.user.username  

class VolunteerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='volunteer_profile'
    )
    full_name = models.CharField(max_length=255)
    verification_pin = models.CharField(max_length=10, blank=True, null=True)
    pin_expires_at = models.DateTimeField(blank=True, null=True)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.SET_NULL, null=True,blank=True)
    phone_number = models.CharField(max_length=20)
    gender = models.CharField(max_length=10, choices=(('male','Male'),('female','Female')))
    date_of_birth = models.DateField(null=True,blank=True)
    nationality = models.CharField(max_length=50)
    id_number = models.CharField(max_length=50)
    current_city = models.CharField(max_length=100)
    education_level = models.CharField(max_length=50)
    languages = models.JSONField(default=list)  # يمكن تخزين عدة لغات
    previous_experience = models.TextField(null=True, blank=True)
    skills = models.JSONField(default=list)
    availability_shift = models.CharField(max_length=20, choices=(('morning','Morning'),('afternoon','Afternoon'),('evening','Evening')))
    available_days = models.JSONField(default=list)  # أيام الأسبوع المتاحة
    start_date = models.DateField(null=True,blank=True)
    expected_duration = models.CharField(max_length=50)
    points = models.IntegerField(default=0)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    qr_code = models.CharField(max_length=100, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    profile_completed = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username



class FamilyCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def str(self):
        return self.name      
          
class RefugeeFamilyMember(models.Model):
    refugee = models.ForeignKey(
        'RefugeeProfile',
        on_delete=models.CASCADE,
        related_name='family_members'
    )

    family_category = models.ForeignKey(
        FamilyCategory,
        on_delete=models.CASCADE
    )

    count = models.IntegerField()

    class Meta:
        unique_together = ('refugee', 'family_category')

    def __str__(self):
        return f"{self.refugee} - {self.family_category} ({self.count})"



class VolunteerApplication(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='volunteer_applications'
    )

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='volunteer_applications'
    )

    selected_services = models.ManyToManyField( 'organizations.OrganizationService',related_name='volunteer_applications')
    phone_number = models.CharField(max_length=15)
    why_volunteer = models.TextField()

    i_commit = models.BooleanField()
    i_agree_terms = models.BooleanField()
     
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )


    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'organization'],
                name='unique_user_organization_application'
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.organization} ({self.status})"
    

class Notification(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=50)

    def str(self):
         return f"Notification for {self.user.username}: {self.message}"

     