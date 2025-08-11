from rest_framework import serializers
from .models import Site, SiteConfiguration
from apps.companies.serializers import CompanySerializer

class SiteSerializer(serializers.ModelSerializer):
    """Full serializer for Site model"""
    company = CompanySerializer(read_only=True)
    company_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Site
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def to_representation(self, instance):
        """Custom representation for API responses"""
        data = super().to_representation(instance)
        data['full_address'] = instance.full_address
        data['is_operational'] = instance.is_operational()
        data['enabled_forms'] = instance.get_enabled_forms()
        return data

class SiteListSerializer(serializers.ModelSerializer):
    """Simplified serializer for site lists"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_code = serializers.CharField(source='company.company_code', read_only=True)
    
    class Meta:
        model = Site
        fields = [
            'id', 'name', 'site_code', 'company_name', 'company_code',
            'city', 'state', 'plant_type', 'operational_status', 'is_active',
            'created_at'
        ]
        read_only_fields = ('created_at',)

class SiteCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating sites"""
    
    class Meta:
        model = Site
        fields = [
            'company', 'name', 'site_code', 'description',
            'address', 'city', 'state', 'country', 'postal_code',
            'latitude', 'longitude', 'phone', 'email',
            'plant_type', 'capacity', 'operational_status', 'is_active'
        ]
    
    def validate_site_code(self, value):
        """Validate site code uniqueness"""
        if Site.objects.filter(site_code=value).exists():
            raise serializers.ValidationError("Site code must be unique.")
        return value

class SiteQRSerializer(serializers.ModelSerializer):
    """Serializer for QR code generation"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_code = serializers.CharField(source='company.company_code', read_only=True)
    
    class Meta:
        model = Site
        fields = ['id', 'name', 'site_code', 'company_name', 'company_code']
    
    def to_representation(self, instance):
        """Include QR code data"""
        data = super().to_representation(instance)
        qr_data = instance.generate_qr_data()
        data['qr_code'] = qr_data['qr_code']
        data['qr_code_image'] = qr_data['qr_code_image']
        return data

class PublicSiteSerializer(serializers.ModelSerializer):
    """Serializer for public site access"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_code = serializers.CharField(source='company.company_code', read_only=True)
    
    class Meta:
        model = Site
        fields = [
            'id', 'name', 'site_code', 'company_name', 'company_code',
            'address', 'city', 'state', 'country', 'postal_code',
            'phone', 'email', 'operational_status', 'is_active'
        ]
    
    def to_representation(self, instance):
        """Custom representation for public access"""
        data = super().to_representation(instance)
        data['is_operational'] = instance.is_operational()
        data['enabled_forms'] = instance.get_enabled_forms()
        data['is_headquarters'] = False
        return data

class FrontendSiteSerializer(serializers.ModelSerializer):
    """Serializer optimized for frontend compatibility"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_code = serializers.CharField(source='company.company_code', read_only=True)
    
    class Meta:
        model = Site
        fields = [
            'id', 'company', 'company_name', 'company_code',
            'name', 'site_code', 'description',
            'address', 'city', 'state', 'country', 'postal_code',
            'latitude', 'longitude', 'phone', 'email',
            'plant_type', 'capacity', 'operational_status', 'is_active'
        ]
    
    def to_representation(self, instance):
        """Custom representation for frontend"""
        data = super().to_representation(instance)
        data['full_address'] = instance.full_address
        data['is_operational'] = instance.is_operational()
        data['enabled_forms'] = instance.get_enabled_forms()
        return data

class SiteFormConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for site form configuration"""
    
    class Meta:
        model = SiteConfiguration
        fields = ['enabled_forms', 'show_phone', 'show_email', 'show_address', 'quick_info_config'] 