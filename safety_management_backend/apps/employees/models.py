from django.db import models
from django.contrib.auth.models import User

class Employee(models.Model):
    """Simplified employee model with multiple location assignments"""
    
    # Basic employee information
    name = models.CharField(max_length=200)
    employee_id = models.CharField(max_length=50, unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    # Job details
    designation = models.CharField(max_length=100, blank=True, help_text="Job title/position")
    department = models.CharField(max_length=100, blank=True, help_text="Department name")
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employees'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.employee_id})"

    def get_emergency_contacts_for_location(self, location_type, location_id):
        """Get emergency contacts for a specific location"""
        return self.locations.filter(
            location_type=location_type,
            location_id=location_id,
            show_in_emergency_contacts=True,
            is_active=True
        )

    @classmethod
    def get_emergency_contacts_by_site(cls, site_id):
        """Get emergency contacts for a specific site"""
        return cls.objects.filter(
            locations__location_type='site',
            locations__location_id=site_id,
            locations__show_in_emergency_contacts=True,
            locations__is_active=True,
            is_active=True
        ).distinct()

    @classmethod
    def get_emergency_contacts_by_entity(cls, entity_id):
        """Get emergency contacts for a specific entity"""
        return cls.objects.filter(
            locations__location_type='entity',
            locations__location_id=entity_id,
            locations__show_in_emergency_contacts=True,
            locations__is_active=True,
            is_active=True
        ).distinct()

    @classmethod
    def get_emergency_contacts_by_headquarters(cls):
        """Get emergency contacts for headquarters"""
        return cls.objects.filter(
            locations__location_type='headquarters',
            locations__location_id='headquarters',
            locations__show_in_emergency_contacts=True,
            locations__is_active=True,
            is_active=True
        ).distinct()

    @classmethod
    def get_emergency_contacts_by_company(cls):
        """Get emergency contacts for company"""
        return cls.objects.filter(
            locations__location_type='company',
            locations__location_id='company',
            locations__show_in_emergency_contacts=True,
            locations__is_active=True,
            is_active=True
        ).distinct()


class EmployeeLocation(models.Model):
    """Model to handle employee location assignments with individual controls"""
    
    LOCATION_TYPES = [
        ('site', 'Site'),
        ('entity', 'Entity'),
        ('headquarters', 'Headquarters'),
        ('company', 'Company'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='locations')
    
    # Location assignment
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES)
    location_id = models.CharField(max_length=50, help_text="ID of the specific location")
    
    # Visibility controls
    show_in_emergency_contacts = models.BooleanField(default=False, help_text="Show this employee as emergency contact for this location")
    is_active = models.BooleanField(default=True, help_text="Whether this location assignment is active")
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employee_locations'
        unique_together = [('employee', 'location_type', 'location_id')]
        ordering = ['location_type', 'location_id']

    def __str__(self):
        return f"{self.employee.name} - {self.location_type} ({self.location_id})"

    @property
    def location_name(self):
        """Get the location name based on location_type and location_id"""
        if self.location_type == 'headquarters':
            return 'Hexa Climate Headquarters'
        elif self.location_type == 'company':
            return 'Hexa Climate Company'
        elif self.location_type == 'site':
            try:
                from apps.sites.models import Site
                site = Site.objects.get(id=self.location_id)
                return f"{site.name} (Site)"
            except Site.DoesNotExist:
                return 'Unknown Site'
        elif self.location_type == 'entity':
            try:
                from apps.companies.models import Entity
                entity = Entity.objects.get(id=self.location_id)
                return f"{entity.name} (Entity)"
            except Entity.DoesNotExist:
                return 'Unknown Entity'
        return 'Unknown Location'
