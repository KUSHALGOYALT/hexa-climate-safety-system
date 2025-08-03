from django.db import models

class EmergencyContact(models.Model):
    CONTACT_TYPES = [
        ('SAFETY_INCHARGE', 'Safety Incharge'),
        ('PLANT_INCHARGE', 'Plant Incharge'),
        ('ADMIN', 'Admin'),
        ('PLANT_MANAGER', 'Plant Manager'),
        ('SAFETY_OFFICER', 'Safety Officer'),
        ('ELECTRICAL_ENGINEER', 'Electrical Engineer'),
        ('MAINTENANCE_SUPERVISOR', 'Maintenance Supervisor'),
        ('FIRE_DEPARTMENT', 'Fire Department'),
        ('MEDICAL_EMERGENCY', 'Medical Emergency'),
        ('UTILITY_GRID', 'Utility Grid Control'),
        ('SECURITY', 'Plant Security'),
        ('ENVIRONMENTAL_OFFICER', 'Environmental Officer'),
        ('CORPORATE_HQ', 'Corporate Headquarters'),
    ]

    site = models.ForeignKey('sites.Site', on_delete=models.CASCADE, related_name='emergency_contacts')
    contact_type = models.CharField(max_length=30, choices=CONTACT_TYPES)
    name = models.CharField(max_length=200)
    designation = models.CharField(max_length=100)
    primary_phone = models.CharField(max_length=20)
    secondary_phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    department = models.CharField(max_length=100, blank=True)
    is_24x7_available = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    priority_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'emergency_contacts'
        ordering = ['priority_order', 'contact_type']
        unique_together = ['site', 'contact_type', 'name']

    def __str__(self):
        return f"{self.site.name} - {self.name} ({self.get_contact_type_display()})"

class NationalEmergencyContact(models.Model):
    CONTACT_TYPES = [
        ('FIRE_DEPARTMENT', 'Fire Department'),
        ('POLICE', 'Police'),
        ('MEDICAL_EMERGENCY', 'Medical Emergency'),
        ('DISASTER_MANAGEMENT', 'Disaster Management'),
        ('POLLUTION_CONTROL', 'Pollution Control Board'),
        ('ELECTRICITY_BOARD', 'Electricity Board'),
    ]

    contact_type = models.CharField(max_length=30, choices=CONTACT_TYPES)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    state = models.CharField(max_length=100, blank=True)
    is_national = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    priority_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'national_emergency_contacts'
        ordering = ['priority_order', 'contact_type']

    def __str__(self):
        return f"{self.name} - {self.get_contact_type_display()}"
