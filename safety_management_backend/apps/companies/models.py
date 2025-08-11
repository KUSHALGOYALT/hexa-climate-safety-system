from django.db import models
from django.utils import timezone
import qrcode
import base64
from io import BytesIO

class Company(models.Model):
    """
    Company model - serves as both company and headquarters
    """
    COMPANY_TYPES = [
        ('HEADQUARTERS', 'Headquarters'),
        ('SUBSIDIARY', 'Subsidiary'),
        ('BRANCH', 'Branch'),
    ]
    
    name = models.CharField(max_length=200)
    company_code = models.CharField(max_length=50, unique=True)
    company_type = models.CharField(max_length=20, choices=COMPANY_TYPES, default='HEADQUARTERS')
    parent_company = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subsidiaries')
    
    # Address fields
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    postal_code = models.CharField(max_length=20)
    
    # Contact information
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    
    # Location coordinates
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Companies"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.company_code})"
    
    @property
    def is_headquarters(self):
        return self.company_type == 'HEADQUARTERS'
    
    @property
    def full_address(self):
        return f"{self.address}, {self.city}, {self.state} {self.postal_code}, {self.country}"

    def generate_qr_data(self):
        """Generate QR code data for company"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"http://localhost:3000/public/{self.company_code}/headquarters")
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            'qr_code': f'data:image/png;base64,{img_str}',
            'company_data': {
                'name': self.name,
                'company_code': self.company_code,
                'public_url': f"http://localhost:3000/public/{self.company_code}/headquarters"
            }
        }

class Entity(models.Model):
    """Entity model - represents different business units under the company"""
    ENTITY_TYPES = [
        ('MANUFACTURING', 'Manufacturing'),
        ('OFFICE', 'Office'),
        ('WAREHOUSE', 'Warehouse'),
        ('RETAIL', 'Retail'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    entity_code = models.CharField(max_length=20, unique=True)
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPES, default='OTHER')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='entities')
    description = models.TextField(blank=True)
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
        verbose_name_plural = "Entities"
        unique_together = ['company', 'entity_code']

    def __str__(self):
        return f"{self.name} ({self.entity_code})"

    def generate_qr_data(self):
        """Generate QR code data for entity"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"http://localhost:3000/public/{self.company.company_code}/entity/{self.entity_code}")
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            'qr_code': f'data:image/png;base64,{img_str}',
            'entity_data': {
                'name': self.name,
                'entity_code': self.entity_code,
                'company_name': self.company.name,
                'company_code': self.company.company_code,
                'public_url': f"http://localhost:3000/public/{self.company.company_code}/entity/{self.entity_code}"
            }
        }
