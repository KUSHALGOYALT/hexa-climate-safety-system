from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import qrcode
from io import BytesIO
import base64
import json
from PIL import Image, ImageDraw, ImageFont
import os

class Site(models.Model):
    OPERATIONAL_STATUS_CHOICES = [
        ('OPERATIONAL', 'Operational'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('SHUTDOWN', 'Shutdown'),
        ('COMMISSIONING', 'Under Commissioning'),
        ('DECOMMISSIONED', 'Decommissioned'),
    ]

    PLANT_TYPE_CHOICES = [
        ('SOLAR', 'Solar Power Plant'),
        ('WIND', 'Wind Power Plant'),
        ('THERMAL', 'Thermal Power Plant'),
        ('HYDRO', 'Hydro Power Plant'),
        ('NUCLEAR', 'Nuclear Power Plant'),
        ('BIOMASS', 'Biomass Power Plant'),
        ('GEOTHERMAL', 'Geothermal Power Plant'),
        ('HYBRID', 'Hybrid Power Plant'),
        ('OTHER', 'Other'),
    ]

    # Form configuration choices
    FORM_TYPES = [
        ('UNSAFE_ACT', 'Unsafe Act'),
        ('UNSAFE_CONDITION', 'Unsafe Condition'),
        ('NEAR_MISS', 'Near Miss'),
        ('FEEDBACK', 'General Feedback'),
    ]

    # Basic Information
    entity = models.ForeignKey(
        'companies.Entity',
        on_delete=models.CASCADE,
        related_name='sites',
        null=True,
        blank=True
    )
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
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        help_text="Latitude coordinate (-90 to 90)"
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        help_text="Longitude coordinate (-180 to 180)"
    )

    # Contact information
    phone = models.CharField(max_length=20)
    email = models.EmailField()

    # Plant specific details
    plant_type = models.CharField(
        max_length=20,
        choices=PLANT_TYPE_CHOICES,
        blank=True
    )
    capacity = models.CharField(
        max_length=100,
        blank=True,
        help_text="Plant capacity (e.g., 100 MW, 50 MWp)"
    )
    operational_status = models.CharField(
        max_length=20,
        choices=OPERATIONAL_STATUS_CHOICES,
        default='OPERATIONAL'
    )

    # Form Configuration - JSON field to store enabled forms
    enabled_forms = models.JSONField(
        default=list,
        blank=True,
        help_text="List of enabled form types for this site"
    )

    # Additional metadata
    commissioned_date = models.DateField(blank=True, null=True)
    last_maintenance_date = models.DateField(blank=True, null=True)
    next_maintenance_date = models.DateField(blank=True, null=True)

    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'sites'
        unique_together = ['entity', 'site_code']
        ordering = ['entity', 'name']
        indexes = [
            models.Index(fields=['entity', 'is_active']),
            models.Index(fields=['site_code']),
            models.Index(fields=['operational_status']),
        ]

    def __str__(self):
        return f"{self.entity.company.name} - {self.entity.name} - {self.name} ({self.site_code})"

    @property
    def company_name(self):
        return self.entity.company.name if self.entity else "Unknown Company"

    @property
    def entity_name(self):
        return self.entity.name if self.entity else "Unknown Entity"

    @property
    def full_address(self):
        return f"{self.address}, {self.city}, {self.state}, {self.country} - {self.postal_code}"

    def get_enabled_forms(self):
        """Get list of enabled form types for this site"""
        if not self.enabled_forms:
            # Default to all forms if none specified
            return [choice[0] for choice in self.FORM_TYPES]
        return self.enabled_forms

    def is_form_enabled(self, form_type):
        """Check if a specific form type is enabled for this site"""
        enabled_forms = self.get_enabled_forms()
        return form_type in enabled_forms

    def enable_form(self, form_type):
        """Enable a specific form type for this site"""
        if form_type not in [choice[0] for choice in self.FORM_TYPES]:
            raise ValueError(f"Invalid form type: {form_type}")
        
        enabled_forms = self.get_enabled_forms()
        if form_type not in enabled_forms:
            enabled_forms.append(form_type)
            self.enabled_forms = enabled_forms
            self.save()

    def disable_form(self, form_type):
        """Disable a specific form type for this site"""
        enabled_forms = self.get_enabled_forms()
        if form_type in enabled_forms:
            enabled_forms.remove(form_type)
            self.enabled_forms = enabled_forms
            self.save()

    def generate_qr_data(self, qr_type='orm', entity_type='site'):
        """Generate QR code data for the site with URL-based QR codes"""
        # Generate the public URL for the site
        if self.entity and self.entity.company:
            public_url = f"http://localhost:3000/public/{self.entity.company.company_code}/{self.site_code}"
        else:
            # Fallback for sites without proper entity/company
            public_url = f"http://localhost:3000/public/UNKNOWN/{self.site_code}"
        
        # Base site data
        site_data = {
            'site_code': self.site_code,
            'site_name': self.name,
            'company_name': self.entity.company.name if self.entity else "Unknown Company",
            'address': self.full_address,
            'latitude': float(self.latitude),
            'longitude': float(self.longitude),
            'enabled_forms': self.get_enabled_forms(),
            'qr_type': qr_type,
            'entity_type': entity_type,
            'public_url': public_url
        }
        
        # Filter data based on entity type
        if entity_type == 'site':
            # Site-specific data only
            site_data.update({
                'type': 'site',
                'description': f'Site-specific QR code for {self.name}',
                'location_type': 'Site Location'
            })
        elif entity_type == 'entity':
            # Entity-specific data only
            site_data.update({
                'type': 'entity',
                'description': f'Entity-level QR code for {self.entity.name if self.entity else "Unknown Entity"}',
                'location_type': 'Entity Level'
            })
        elif entity_type == 'headquarters':
            # Headquarters-specific data only
            site_data.update({
                'type': 'headquarters',
                'headquarters_name': 'Hexa Climate Headquarters',
                'headquarters_description': 'Hexa Climate Headquarters - Central management and safety coordination center for all solar power operations.',
                'contact_info': {
                    'email': 'info@hexaclimate.com',
                    'phone': '9660027799',
                    'address': 'Kumbhari, Maharashtra, India'
                },
                'description': 'Headquarters QR code for Hexa Climate',
                'location_type': 'Headquarters'
            })
        
        # Generate QR code with the URL instead of JSON data
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(public_url)
        qr.make(fit=True)
        
        # Generate basic black and white QR code
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return {'qr_code': f"data:image/png;base64,{img_str}", 'site_data': site_data, 'qr_type': qr_type, 'entity_type': entity_type}

    def get_available_qr_types(self):
        """Get available QR code types with descriptions"""
        return [
            {
                'type': 'orm',
                'name': 'ORM',
                'description': 'Operational Risk Management QR code',
                'color': 'Black on White'
            },
            {
                'type': 'headquarters',
                'name': 'Headquarters',
                'description': 'Hexa Climate Headquarters QR code',
                'color': 'Black on White'
            },
            {
                'type': 'construction',
                'name': 'Construction',
                'description': 'Construction site QR code',
                'color': 'Black on White'
            },
            {
                'type': 'safety',
                'name': 'Safety',
                'description': 'Safety-focused QR code',
                'color': 'Black on White'
            },
            {
                'type': 'maintenance',
                'name': 'Maintenance',
                'description': 'Maintenance and repair QR code',
                'color': 'Black on White'
            },
            {
                'type': 'quality',
                'name': 'Quality Control',
                'description': 'Quality control and inspection QR code',
                'color': 'Black on White'
            }
        ]

    def get_entity_types(self):
        """Get available entity types for QR generation"""
        return [
            {
                'type': 'site',
                'name': 'Site Specific',
                'description': 'QR code for specific site location',
                'icon': '🏭'
            },
            {
                'type': 'entity',
                'name': 'Entity Level',
                'description': 'QR code for company entity',
                'icon': '🏢'
            },
            {
                'type': 'headquarters',
                'name': 'Headquarters',
                'description': 'QR code for Hexa Climate headquarters',
                'icon': '🏛️'
            }
        ]

    def get_form_configuration(self):
        """Get complete form configuration for this site"""
        all_forms = [
            {
                'type': choice[0],
                'title': choice[1],
                'enabled': self.is_form_enabled(choice[0])
            }
            for choice in self.FORM_TYPES
        ]
        return all_forms

    def is_operational(self):
        """Check if site is operational"""
        return (
            self.is_active and 
            self.operational_status == 'OPERATIONAL'
        )


class SiteConfiguration(models.Model):
    """Model to store additional site-specific configurations"""
    site = models.OneToOneField(
        Site,
        on_delete=models.CASCADE,
        related_name='configuration'
    )
    
    # Form-specific configurations
    form_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Configuration for individual forms"
    )
    
    # Display settings for MenuPage sections
    show_safety_officer = models.BooleanField(default=True, help_text="Show Safety Officer section")
    show_emergency_contacts = models.BooleanField(default=True, help_text="Show Emergency Contacts section")
    show_quick_info = models.BooleanField(default=True, help_text="Show Quick Info section")
    
    # Quick Info section configuration
    quick_info_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Configuration for Quick Info cards"
    )
    
    # Custom settings
    custom_title = models.CharField(max_length=200, blank=True)
    custom_description = models.TextField(blank=True)
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'site_configurations'
    
    def __str__(self):
        return f"Configuration for {self.site.name}"
    
    def get_form_config(self, form_type):
        """Get configuration for a specific form type"""
        return self.form_config.get(form_type, {})
    
    def set_form_config(self, form_type, config):
        """Set configuration for a specific form type"""
        self.form_config[form_type] = config
        self.save()
    
    def get_quick_info_config(self):
        """Get quick info configuration"""
        return self.quick_info_config or {}
