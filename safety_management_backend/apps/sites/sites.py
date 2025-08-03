from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import qrcode
from io import BytesIO
import base64
import json

class Site(models.Model):
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='sites')
    name = models.CharField(max_length=200)
    site_code = models.CharField(max_length=20)
    description = models.TextField(blank=True)

    # Location details
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    country_code = models.CharField(max_length=5, default='IND')
    postal_code = models.CharField(max_length=20)

    # GPS Coordinates
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )

    # Contact information
    phone = models.CharField(max_length=20)
    email = models.EmailField()

    # Plant specific details
    plant_type = models.CharField(max_length=100, blank=True)
    capacity = models.CharField(max_length=100, blank=True)
    operational_status = models.CharField(
        max_length=20,
        choices=[
            ('OPERATIONAL', 'Operational'),
            ('MAINTENANCE', 'Under Maintenance'),
            ('SHUTDOWN', 'Shutdown'),
        ],
        default='OPERATIONAL'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'sites'
        unique_together = ['company', 'site_code']

    def __str__(self):
        return f"{self.company.company_name} - {self.name} ({self.site_code})"

    @property
    def company_name(self):
        return self.company.name

    def generate_qr_data(self):
        """Generate QR code data for the site"""
        return {
            'site_code': self.site_code,
            'name': self.name,
            'company_code': self.company.company_code,
            'latitude': str(self.latitude),
            'longitude': str(self.longitude),
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'country_code': self.country_code
        }

    def generate_qr_code(self):
        """Generate QR code image as base64 string"""
        qr_data = json.dumps(self.generate_qr_data())
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
