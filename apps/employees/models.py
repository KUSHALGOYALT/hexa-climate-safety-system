from django.db import models
from django.conf import settings

class Employee(models.Model):
    """Employee model - represents employees who can be deployed to multiple locations"""
    employee_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Employees"

    def __str__(self):
        return f"{self.name} ({self.employee_id})"

    @classmethod
    def get_emergency_contacts_by_headquarters(cls):
        """Get emergency contacts for headquarters"""
        return cls.objects.filter(
            employeelocation__location_type='headquarters',
            employeelocation__show_in_emergency_contacts=True,
            employeelocation__is_active=True,
            is_active=True
        ).distinct()

    @classmethod
    def get_emergency_contacts_by_company(cls):
        """Get emergency contacts for company (same as headquarters)"""
        return cls.get_emergency_contacts_by_headquarters()

    @classmethod
    def get_emergency_contacts_by_entity(cls, entity_id):
        """Get emergency contacts for specific entity"""
        return cls.objects.filter(
            employeelocation__location_type='entity',
            employeelocation__location_id=entity_id,
            employeelocation__show_in_emergency_contacts=True,
            employeelocation__is_active=True,
            is_active=True
        ).distinct()

    @classmethod
    def get_emergency_contacts_by_site(cls, site_id):
        """Get emergency contacts for specific site"""
        return cls.objects.filter(
            employeelocation__location_type='site',
            employeelocation__location_id=site_id,
            employeelocation__show_in_emergency_contacts=True,
            employeelocation__is_active=True,
            is_active=True
        ).distinct()

class EmployeeLocation(models.Model):
    """EmployeeLocation model - represents employee deployment to locations"""
    LOCATION_TYPES = [
        ('headquarters', 'Headquarters'),
        ('company', 'Company'),
        ('entity', 'Entity'),
        ('site', 'Site'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='locations')
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES)
    location_id = models.CharField(max_length=50)  # Can be 'headquarters', 'company', or actual ID
    show_in_emergency_contacts = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Employee Locations"
        unique_together = ['employee', 'location_type', 'location_id']

    def __str__(self):
        return f"{self.employee.name} - {self.location_type} ({self.location_id})"

    @property
    def location_name(self):
        """Get the location name based on location_type and location_id"""
        if self.location_type == 'headquarters':
            return 'Hexa Climate'
        elif self.location_type == 'company':
            return 'Hexa Climate'
        elif self.location_type == 'site':
            return f'Site {self.location_id}'
        elif self.location_type == 'entity':
            return f'Entity {self.location_id}'
        return 'Unknown Location' 