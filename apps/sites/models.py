from django.db import models
from django.conf import settings
import qrcode
import base64
from io import BytesIO

class Site(models.Model):
    """Site model - represents specific locations under entities"""
    OPERATIONAL_STATUS_CHOICES = [
        ('OPERATIONAL', 'Operational'),
        ('MAINTENANCE', 'Maintenance'),
        ('SHUTDOWN', 'Shutdown'),
        ('CONSTRUCTION', 'Under Construction'),
    ]
    
    PLANT_TYPE_CHOICES = [
        ('MANUFACTURING', 'Manufacturing'),
        ('PROCESSING', 'Processing'),
        ('STORAGE', 'Storage'),
        ('OFFICE', 'Office'),
        ('WAREHOUSE', 'Warehouse'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    site_code = models.CharField(max_length=20, unique=True)
    entity = models.ForeignKey('companies.Entity', on_delete=models.CASCADE, related_name='sites')
    plant_type = models.CharField(max_length=20, choices=PLANT_TYPE_CHOICES, default='OTHER')
    operational_status = models.CharField(max_length=20, choices=OPERATIONAL_STATUS_CHOICES, default='OPERATIONAL')
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='India')
    postal_code = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Sites"

    def __str__(self):
        return f"{self.name} ({self.site_code})"

    def is_operational(self):
        """Check if site is operational"""
        return self.operational_status == 'OPERATIONAL'

    def generate_qr_data(self):
        """Generate QR code data for site"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"http://localhost:3000/public/{self.entity.company.company_code}/{self.site_code}")
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            'qr_code': f'data:image/png;base64,{img_str}',
            'site_data': {
                'name': self.name,
                'site_code': self.site_code,
                'entity_name': self.entity.name,
                'company_name': self.entity.company.name,
                'company_code': self.entity.company.company_code,
                'public_url': f"http://localhost:3000/public/{self.entity.company.company_code}/{self.site_code}"
            }
        } 