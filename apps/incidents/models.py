from django.db import models
from django.conf import settings

class Incident(models.Model):
    """Incident model - represents safety incidents"""
    SEVERITY_CHOICES = [
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
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    location_type = models.CharField(max_length=20, choices=[
        ('headquarters', 'Headquarters'),
        ('entity', 'Entity'),
        ('site', 'Site'),
    ])
    location_id = models.CharField(max_length=50)  # Can be 'headquarters' or actual ID
    reporter_name = models.CharField(max_length=200, blank=True)
    reporter_email = models.EmailField(blank=True)
    reporter_phone = models.CharField(max_length=20, blank=True)
    incident_date = models.DateTimeField()
    reported_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Incidents"
        ordering = ['-reported_date']

    def __str__(self):
        return f"{self.title} - {self.severity}"

    @property
    def location_name(self):
        """Get the location name based on location_type and location_id"""
        if self.location_type == 'headquarters':
            return 'Hexa Climate'
        elif self.location_type == 'entity':
            return f'Entity {self.location_id}'
        elif self.location_type == 'site':
            return f'Site {self.location_id}'
        return 'Unknown Location' 