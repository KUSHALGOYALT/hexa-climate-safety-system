from django.db import models
from django.utils import timezone
from apps.companies.models import Company
from apps.sites.models import Site

class Employee(models.Model):
    """
    Employee model for managing staff information
    """
    EMPLOYMENT_TYPES = [
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('CONTRACT', 'Contract'),
        ('INTERN', 'Intern'),
    ]
    
    # Basic information
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees')
    name = models.CharField(max_length=200)
    employee_id = models.CharField(max_length=50, unique=True)
    position = models.CharField(max_length=100)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default='FULL_TIME')
    
    # Contact information
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.employee_id})"
    
    @property
    def full_name(self):
        return self.name
    
    @property
    def is_emergency_contact(self):
        """Check if this employee should be shown in emergency contacts"""
        return bool(self.emergency_contact_name and self.emergency_contact_phone)

class EmployeeAssignment(models.Model):
    """
    Model to track employee assignments to sites
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='assignments')
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='employee_assignments')
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    assigned_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['employee', 'site']
        ordering = ['-assigned_date']
    
    def __str__(self):
        return f"{self.employee.name} - {self.site.name}"
    
    @property
    def is_current(self):
        return self.is_active and (not self.end_date or self.end_date > timezone.now())
