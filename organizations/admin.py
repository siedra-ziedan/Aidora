from django.contrib import admin


# Register your models here.

from .models import Organization, Service, OrganizationService, TargetGroup, OrganizationTargetGroup

class OrganizationTargetGroupInline(admin.TabularInline):
    model = OrganizationTargetGroup
    extra = 1  # عدد الصفوف الفارغة التي تظهر تلقائياً

class OrganizationServiceInline(admin.TabularInline):
    model = OrganizationService
    extra = 1


class OrganizationAdmin(admin.ModelAdmin):
    inlines = [
        OrganizationTargetGroupInline,  # Target Groups
        OrganizationServiceInline,      # Services
    ]
    list_display = ('name', 'official_website')  # الأعمدة اللي رح تظهر في جدول الـ Admin




admin.site.register(OrganizationService)
admin.site.register(OrganizationTargetGroup)
admin.site.register(Service)
admin.site.register(TargetGroup)
admin.site.register(Organization, OrganizationAdmin)