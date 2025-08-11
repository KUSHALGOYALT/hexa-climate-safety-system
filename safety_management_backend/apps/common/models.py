from django.db import models
from django.utils import timezone
from apps.companies.models import Company
from apps.sites.models import Site

# Create your models here.

class EmergencyContact(models.Model):
    """
    Emergency contact model for managing emergency contact information
    """
    CONTACT_TYPES = [
        ('SITE_MANAGER', 'Site Manager'),
        ('SAFETY_OFFICER', 'Safety Officer'),
        ('EMERGENCY_RESPONSE', 'Emergency Response'),
        ('GENERAL', 'General Contact'),
    ]
    
    # Basic information
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='emergency_contacts')
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='emergency_contacts', null=True, blank=True)
    
    name = models.CharField(max_length=200)
    position = models.CharField(max_length=100)
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPES, default='GENERAL')
    
    # Contact information
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    alternate_phone = models.CharField(max_length=20, blank=True)
    
    # Availability
    is_available_24_7 = models.BooleanField(default=False)
    availability_notes = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_primary', 'name']
        verbose_name = "Emergency Contact"
        verbose_name_plural = "Emergency Contacts"
    
    def __str__(self):
        site_name = f" - {self.site.name}" if self.site else ""
        return f"{self.name} ({self.position}){site_name}"
    
    @property
    def display_name(self):
        return f"{self.name} - {self.position}"
    
    @property
    def primary_contact(self):
        return self.is_primary and self.is_active
    
    def get_contact_info(self):
        """Get formatted contact information"""
        return {
            'name': self.name,
            'position': self.position,
            'phone': self.phone,
            'email': self.email,
            'alternate_phone': self.alternate_phone,
            'is_available_24_7': self.is_available_24_7,
            'availability_notes': self.availability_notes
        }
