from rest_framework import serializers
from .models import EmergencyContact
from apps.companies.serializers import CompanySerializer
from apps.sites.serializers import SiteSerializer

class EmergencyContactSerializer(serializers.ModelSerializer):
    """Full serializer for EmergencyContact model"""
    company = CompanySerializer(read_only=True)
    site = SiteSerializer(read_only=True)
    
    class Meta:
        model = EmergencyContact
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def to_representation(self, instance):
        """Custom representation for API responses"""
        data = super().to_representation(instance)
        data['display_name'] = instance.display_name
        data['primary_contact'] = instance.primary_contact
        return data

class EmergencyContactListSerializer(serializers.ModelSerializer):
    """Simplified serializer for emergency contact lists"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    site_name = serializers.CharField(source='site.name', read_only=True)
    
    class Meta:
        model = EmergencyContact
        fields = [
            'id', 'name', 'position', 'contact_type', 'phone', 'email',
            'company_name', 'site_name', 'is_primary', 'is_active'
        ]

class EmergencyContactCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating emergency contacts"""
    
    class Meta:
        model = EmergencyContact
        fields = [
            'company', 'site', 'name', 'position', 'contact_type',
            'phone', 'email', 'alternate_phone', 'is_available_24_7',
            'availability_notes', 'is_active', 'is_primary'
        ] 