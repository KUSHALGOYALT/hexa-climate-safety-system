from django.db import models
from django.core.validators import RegexValidator

class Company(models.Model):
    COMPANY_TYPES = [
        ('PARENT', 'Parent Company'),
        ('SUBSIDIARY', 'Subsidiary'),
        ('DIVISION', 'Division'),
    ]
    
    name = models.CharField(max_length=200)
    company_code = models.CharField(max_length=20, unique=True)
    company_type = models.CharField(max_length=20, choices=COMPANY_TYPES, default='PARENT')
    parent_company = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subsidiaries')
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    country_code = models.CharField(max_length=5, default='IND')
    postal_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'companies'
        verbose_name_plural = 'Companies'

    def __str__(self):
        return f"{self.name} ({self.company_code})"

    @property
    def is_parent(self):
        return self.company_type == 'PARENT'

    @property
    def is_subsidiary(self):
        return self.company_type == 'SUBSIDIARY'

    def get_all_subsidiaries(self):
        """Get all subsidiaries recursively"""
        subsidiaries = list(self.subsidiaries.all())
        for subsidiary in self.subsidiaries.all():
            subsidiaries.extend(subsidiary.get_all_subsidiaries())
        return subsidiaries

class Entity(models.Model):
    """Entity represents a business unit/division under a company"""
    name = models.CharField(max_length=200)
    entity_code = models.CharField(max_length=20)
    entity_type = models.CharField(max_length=50, default='DIVISION')  # Allow any entity type
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='entities')
    description = models.TextField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='India')
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'entities'
        unique_together = ['company', 'entity_code']
        verbose_name_plural = 'Entities'

    def __str__(self):
        return f"{self.company.name} - {self.name} ({self.entity_code})"

    @property
    def full_address(self):
        if self.address:
            return f"{self.address}, {self.city}, {self.state}, {self.country}"
        return f"{self.company.address}, {self.company.city}, {self.company.state}, {self.company.country}"

    def get_sites_count(self):
        """Get count of sites under this entity"""
        return self.sites.count()

    def generate_qr_data(self, qr_type='orm', entity_type='entity'):
        """Generate QR code data for entity"""
        import qrcode
        from io import BytesIO
        import base64
        import json
        
        # Generate entity data - only entity-specific information
        entity_data = {
            'id': self.id,
            'name': self.name,
            'entity_code': self.entity_code,
            'entity_type': self.entity_type,
            'company_name': self.company.name,
            'company_code': self.company.company_code,
            'address': self.full_address,
            'phone': self.phone or self.company.phone,
            'email': self.email or self.company.email,
            'description': self.description,
            'qr_type': qr_type,
            'entity_type': entity_type,
            'enabled_forms': ['UNSAFE_ACT', 'UNSAFE_CONDITION', 'NEAR_MISS', 'FEEDBACK'],
            'type': 'entity',
            'description': f'Entity-level QR code for {self.name}',
            'location_type': 'Entity Level'
        }
        
        # Generate public URL for entity
        public_url = f"http://localhost:3000/public/{self.company.company_code}/entity/{self.entity_code}"
        
        # Create QR code with public URL
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(public_url)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            'qr_code': f"data:image/png;base64,{qr_code_base64}",
            'entity_data': entity_data,
            'public_url': public_url
        }
