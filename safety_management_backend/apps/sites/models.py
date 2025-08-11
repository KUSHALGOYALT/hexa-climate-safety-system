from django.db import models
from django.utils import timezone
from apps.companies.models import Company
import qrcode
import base64
from io import BytesIO

class Site(models.Model):
    """
    Site model for solar power plants and other facilities
    """
    PLANT_TYPES = [
        ('SOLAR', 'Solar Power Plant'),
        ('WIND', 'Wind Power Plant'),
        ('HYDRO', 'Hydro Power Plant'),
        ('THERMAL', 'Thermal Power Plant'),
        ('OTHER', 'Other'),
    ]
    
    OPERATIONAL_STATUS = [
        ('OPERATIONAL', 'Operational'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('SHUTDOWN', 'Shutdown'),
        ('PLANNING', 'Planning Phase'),
    ]
    
    # Basic information
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sites')
    name = models.CharField(max_length=200)
    site_code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    # Address fields
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    postal_code = models.CharField(max_length=20)
    
    # Location coordinates
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    
    # Contact information
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    
    # Plant information
    plant_type = models.CharField(max_length=20, choices=PLANT_TYPES, default='SOLAR')
    capacity = models.CharField(max_length=50, blank=True)
    operational_status = models.CharField(max_length=20, choices=OPERATIONAL_STATUS, default='OPERATIONAL')
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.site_code})"
    
    @property
    def full_address(self):
        return f"{self.address}, {self.city}, {self.state} {self.postal_code}, {self.country}"
    
    def is_operational(self):
        return self.operational_status == 'OPERATIONAL' and self.is_active
    
    def get_enabled_forms(self):
        """Get list of enabled incident reporting forms"""
        try:
            config = self.siteconfiguration
            return config.enabled_forms if config.enabled_forms else []
        except SiteConfiguration.DoesNotExist:
            return ['UNSAFE_ACT', 'UNSAFE_CONDITION', 'NEAR_MISS']
    
    def generate_qr_data(self, qr_type='orm'):
        """Generate QR code data for the site"""
        if qr_type == 'url':
            # Generate URL-based QR code
            qr_url = f"http://localhost:3000/public/{self.company.company_code}/{self.site_code}"
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_code = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                'qr_code': qr_code,
                'qr_code_image': f"data:image/png;base64,{qr_code}",
                'url': qr_url
            }
        else:
            # Generate ORM-based QR code
            qr_data = {
                'company_code': self.company.company_code,
                'site_code': self.site_code,
                'site_name': self.name,
                'company_name': self.company.name
            }
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(str(qr_data))
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_code = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                'qr_code': qr_code,
                'qr_code_image': f"data:image/png;base64,{qr_code}",
                'data': qr_data
            }

class SiteConfiguration(models.Model):
    """
    Configuration for site-specific settings
    """
    site = models.OneToOneField(Site, on_delete=models.CASCADE, related_name='siteconfiguration')
    
    # Form configuration
    enabled_forms = models.JSONField(default=list, blank=True)
    
    # Display configuration
    show_phone = models.BooleanField(default=True)
    show_email = models.BooleanField(default=True)
    show_address = models.BooleanField(default=True)
    
    # Quick info configuration
    quick_info_config = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configurations"
    
    def __str__(self):
        return f"Configuration for {self.site.name}"
