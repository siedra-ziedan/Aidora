from django.db import models
class ServiceRequest(models.Model):

    URGENCY_CHOICES = [
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    refugee = models.ForeignKey(
        'accounts.RefugeeProfile',
        on_delete=models.CASCADE
    )

    service = models.ForeignKey(
        'organizations.Service',
        on_delete=models.CASCADE
    )

    family_members = models.PositiveIntegerField()

    urgency_level = models.CharField(
        max_length=10,
        choices=URGENCY_CHOICES,
        default='normal'
    )

    description = models.TextField()
    organization = models.ForeignKey('organizations.Organization', on_delete=models.SET_NULL, null=True,blank=True)
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    location = models.CharField(max_length=255)
    delivery_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def str(self):
        return f"{self.refugee} - {self.service}"



class Task(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('completed', 'Completed'),
    ]

    service_request_id = models.ForeignKey(
        'requests.ServiceRequest',
        on_delete=models.CASCADE,
        related_name='tasks'
    )

    volunteer_id = models.ForeignKey(
        'accounts.VolunteerProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks'
    )

    title = models.CharField(max_length=255)

    instructions = models.TextField()

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    rejection_reason = models.TextField(
        blank=True,
        null=True
    )
    report_reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def str(self):
        return f"{self.title} - {self.volunteer}"
    

