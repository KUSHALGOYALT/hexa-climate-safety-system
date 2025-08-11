from django.db import models
from django.utils import timezone
from apps.sites.models import Site
from apps.employees.models import Employee

class Incident(models.Model):
    """
    Incident model for safety incident reporting
    """
    INCIDENT_TYPES = [
        ('UNSAFE_ACT', 'Unsafe Act'),
        ('UNSAFE_CONDITION', 'Unsafe Condition'),
        ('NEAR_MISS', 'Near Miss'),
        ('ACCIDENT', 'Accident'),
        ('INCIDENT', 'Incident'),
    ]
    
    SEVERITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Basic information
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='incidents')
    incident_type = models.CharField(max_length=20, choices=INCIDENT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    
    # Incident details
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    
    # Reporter information
    reported_by = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    anonymous = models.BooleanField(default=False)
    
    # Assignment
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_incidents')
    
    # Timestamps
    incident_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional fields
    actions_taken = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    cost_estimate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.site.name}"
    
    @property
    def is_open(self):
        return self.status in ['OPEN', 'IN_PROGRESS']
    
    @property
    def is_resolved(self):
        return self.status in ['RESOLVED', 'CLOSED']
    
    @property
    def days_open(self):
        if self.is_open:
            return (timezone.now() - self.created_at).days
        return None
    
    def assign_to(self, employee):
        """Assign incident to an employee"""
        self.assigned_to = employee
        self.status = 'IN_PROGRESS'
        self.save()
    
    def resolve(self, actions_taken='', recommendations=''):
        """Mark incident as resolved"""
        self.status = 'RESOLVED'
        self.actions_taken = actions_taken
        self.recommendations = recommendations
        self.save()
    
    def close(self):
        """Close the incident"""
        self.status = 'CLOSED'
        self.save()
