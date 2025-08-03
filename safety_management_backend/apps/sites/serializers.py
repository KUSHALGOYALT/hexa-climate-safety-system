from rest_framework import serializers
from django.core.validators import validate_email
from .models import Site, SiteConfiguration
from apps.companies.models import Entity

class SiteListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing sites"""
    entity_name = serializers.CharField(read_only=True)
    company_name = serializers.CharField(read_only=True)

    class Meta:
        model = Site
        fields = [
            'id', 'name', 'site_code', 'entity', 'entity_name', 'company_name',
            'address', 'city', 'state', 'country', 'postal_code',
            'latitude', 'longitude', 'phone', 'email',
            'operational_status', 'plant_type',
            'capacity', 'is_active', 'created_at'
        ]

class SiteFormConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for site form configuration"""
    enabled_forms = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="List of enabled form types"
    )
    form_configuration = serializers.SerializerMethodField()
    all_available_forms = serializers.SerializerMethodField()
    site_name = serializers.CharField(source='name', read_only=True)

    class Meta:
        model = Site
        fields = ['id', 'site_code', 'name', 'site_name', 'enabled_forms', 'form_configuration', 'all_available_forms']

    def get_form_configuration(self, obj):
        """Get complete form configuration for this site"""
        return obj.get_form_configuration()

    def get_all_available_forms(self, obj):
        """Get all available form types"""
        return [choice[0] for choice in obj.FORM_TYPES]

    def validate_enabled_forms(self, value):
        """Validate enabled forms list"""
        if value:
            valid_forms = [choice[0] for choice in self.instance.FORM_TYPES if self.instance]
            for form_type in value:
                if form_type not in valid_forms:
                    raise serializers.ValidationError(f"Invalid form type: {form_type}")
        return value

class SiteSerializer(serializers.ModelSerializer):
    """Full serializer for site details"""
    entity_name = serializers.CharField(source='entity.name', read_only=True)
    company_name = serializers.CharField(source='entity.company.name', read_only=True)
    full_address = serializers.CharField(read_only=True)
    qr_code = serializers.SerializerMethodField()
    coordinates = serializers.SerializerMethodField()
    enabled_forms = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="List of enabled form types"
    )
    form_configuration = serializers.SerializerMethodField()

    class Meta:
        model = Site
        fields = '__all__'

    def get_qr_code(self, obj):
        """Generate QR code for the site"""
        return obj.generate_qr_data()

    def get_coordinates(self, obj):
        """Get coordinates as list [lat, lng]"""
        return [float(obj.latitude), float(obj.longitude)]

    def get_form_configuration(self, obj):
        """Get complete form configuration for this site"""
        return obj.get_form_configuration()

    def validate_email(self, value):
        """Validate email field"""
        if value:
            validate_email(value)
        return value

    def validate_site_code(self, value):
        """Validate site code format and uniqueness"""
        if not value.isalnum():
            raise serializers.ValidationError(
                "Site code should contain only alphanumeric characters."
            )

        # Check uniqueness within company
        if self.instance:
            # Update case - exclude current instance
            if Site.objects.filter(
                    entity=self.instance.entity,
                    site_code=value.upper()
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "Site code already exists for this company."
                )
        else:
            # Create case - check if company is provided in validated_data
            entity_id = self.initial_data.get('entity')
            if entity_id and Site.objects.filter(
                    entity_id=entity_id,
                    site_code=value.upper()
            ).exists():
                raise serializers.ValidationError(
                    "Site code already exists for this company."
                )

        return value.upper()

    def validate_enabled_forms(self, value):
        """Validate enabled forms list"""
        if value:
            valid_forms = [choice[0] for choice in self.instance.FORM_TYPES if self.instance]
            for form_type in value:
                if form_type not in valid_forms:
                    raise serializers.ValidationError(f"Invalid form type: {form_type}")
        return value

    def validate(self, data):
        """Cross-field validation"""
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        # Validate coordinate ranges
        if latitude is not None and (latitude < -90 or latitude > 90):
            raise serializers.ValidationError({
                'latitude': 'Latitude must be between -90 and 90 degrees.'
            })

        if longitude is not None and (longitude < -180 or longitude > 180):
            raise serializers.ValidationError({
                'longitude': 'Longitude must be between -180 and 180 degrees.'
            })

        return data

class SiteQRSerializer(serializers.ModelSerializer):
    """Serializer specifically for QR code generation"""
    qr_data = serializers.SerializerMethodField()
    qr_code_image = serializers.SerializerMethodField()
    company_name = serializers.CharField(source='entity.company.name', read_only=True)

    class Meta:
        model = Site
        fields = [
            'id', 'name', 'site_code', 'company_name', 'qr_data', 'qr_code_image',
            'operational_status', 'is_active'
        ]

    def get_qr_data(self, obj):
        """Get QR data as JSON"""
        return obj.generate_qr_data()

    def get_qr_code_image(self, obj):
        """Get QR code as base64 image"""
        return obj.generate_qr_data()

class PublicSiteSerializer(serializers.ModelSerializer):
    """Public serializer for QR code access (limited data)"""
    company_name = serializers.CharField(source='entity.company.name', read_only=True)
    entity_name = serializers.CharField(source='entity.name', read_only=True)
    coordinates = serializers.SerializerMethodField()

    class Meta:
        model = Site
        fields = [
            'name', 'site_code', 'company_name', 'entity_name', 'address', 'city', 'state',
            'country', 'country_code', 'coordinates', 'phone', 'email',
            'plant_type', 'capacity', 'operational_status'
        ]

    def get_coordinates(self, obj):
        """Get coordinates as dict"""
        return {
            'latitude': str(obj.latitude),
            'longitude': str(obj.longitude)
        }

class SiteCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating sites"""

    class Meta:
        model = Site
        exclude = ['created_at', 'updated_at']

    def validate_entity(self, value):
        """Validate entity exists and is active"""
        if not value.is_active:
            raise serializers.ValidationError(
                "Cannot create site for inactive entity."
            )
        return value

class FrontendSiteSerializer(serializers.ModelSerializer):
    """Flexible serializer for frontend site creation with better defaults"""
    entity_name = serializers.CharField(source='entity.name', read_only=True)
    company_name = serializers.CharField(source='entity.company.name', read_only=True)

    class Meta:
        model = Site
        fields = '__all__'
        extra_kwargs = {
            'description': {'required': False, 'allow_blank': True},
            'country': {'required': False, 'default': 'India'},
            'country_code': {'required': False, 'default': 'IND'},
            'plant_type': {'required': False, 'allow_blank': True},
            'capacity': {'required': False, 'allow_blank': True},
            'operational_status': {'required': False, 'default': 'OPERATIONAL'},
            'commissioned_date': {'required': False},
            'last_maintenance_date': {'required': False},
            'next_maintenance_date': {'required': False},
        }

    def validate_email(self, value):
        """Validate email field"""
        if value:
            validate_email(value)
        return value

    def validate_site_code(self, value):
        """Validate site code format and uniqueness"""
        if not value.isalnum():
            raise serializers.ValidationError(
                "Site code should contain only alphanumeric characters."
            )

        # Check uniqueness within company
        if self.instance:
            # Update case - exclude current instance
            if Site.objects.filter(
                    entity=self.instance.entity,
                    site_code=value.upper()
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "Site code already exists for this company."
                )
        else:
            # Create case - check if company is provided in validated_data
            entity_id = self.initial_data.get('entity')
            if entity_id and Site.objects.filter(
                    entity_id=entity_id,
                    site_code=value.upper()
            ).exists():
                raise serializers.ValidationError(
                    "Site code already exists for this company."
                )

        return value.upper()

    def validate(self, data):
        """Cross-field validation with better error messages"""
        errors = {}
        
        # Check for required fields
        required_fields = ['entity', 'name', 'site_code', 'address', 'city', 'state', 
                         'postal_code', 'latitude', 'longitude', 'phone', 'email']
        
        for field in required_fields:
            if field not in data or not data[field]:
                errors[field] = f"{field.replace('_', ' ').title()} is required."
        
        # Validate coordinate ranges
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if latitude is not None and (latitude < -90 or latitude > 90):
            errors['latitude'] = 'Latitude must be between -90 and 90 degrees.'

        if longitude is not None and (longitude < -180 or longitude > 180):
            errors['longitude'] = 'Longitude must be between -180 and 180 degrees.'

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        """Create site with defaults"""
        # Ensure defaults are set
        validated_data.setdefault('country', 'India')
        validated_data.setdefault('country_code', 'IND')
        validated_data.setdefault('operational_status', 'OPERATIONAL')
        validated_data.setdefault('is_active', True)
        
        return super().create(validated_data)
