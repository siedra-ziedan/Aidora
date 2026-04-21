from django.db import models

# =====================================================
# Organization and related models
# =====================================================

from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    logo = models.ImageField(upload_to='organizations/logos/')
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='organization',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=255, unique=True,null=True)
    about = models.TextField()
    official_website = models.URLField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)

    # صور التأثير (بدل جدول Impact)
    impact_image1 = models.ImageField(upload_to='organizations/impact/', blank=True, null=True)
    impact_image2 = models.ImageField(upload_to='organizations/impact/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    

class Service(models.Model):

    SERVICE_TYPES = [
        ('health', 'Health'),
        ('protection', 'Protection'),
        ('food', 'Food'),
        ('vaccination', 'Vaccination'),
        ('logistics', 'Logistics Support'),
        ('emergency', 'Emergency Response'),
        ('water', 'Water and Sanitation'),
        ('education', 'Education'),
        ('legal', 'Legal Assistance'),
        ('shelter', 'Shelter'),
    ]
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    icon= models.CharField(max_length=255)
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPES )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class OrganizationService(models.Model):
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='organization_services'
    )
    service = models.ForeignKey(
        'Service',
        on_delete=models.CASCADE,
        related_name='organization_services'
    )

    class Meta:
        unique_together = ('organization', 'service')

    def __str__(self):
        return f"{self.organization.name} - {self.service.name}"



class TargetGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
   
    def __str__(self):
        return self.name
    
class OrganizationTargetGroup(models.Model):
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, related_name='target_groups')
    target_group = models.ForeignKey(TargetGroup, on_delete=models.CASCADE, related_name='organizations')

    class Meta:
        unique_together = ('organization', 'target_group')

    def __str__(self):
        return f"{self.organization.name} - {self.target_group.name}"
