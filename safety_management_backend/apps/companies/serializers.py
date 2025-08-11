from rest_framework import serializers
from .models import Company

class CompanySerializer(serializers.ModelSerializer):
    """Serializer for Company model"""
    
    class Meta:
        model = Company
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def to_representation(self, instance):
        """Custom representation for API responses"""
        data = super().to_representation(instance)
        data['is_headquarters'] = instance.is_headquarters
        data['full_address'] = instance.full_address
        return data

class CompanyListSerializer(serializers.ModelSerializer):
    """Simplified serializer for company lists"""
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'company_code', 'company_type', 
            'city', 'state', 'country', 'is_active',
            'created_at'
        ]
        read_only_fields = ('created_at',)

class CompanyCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating companies"""
    
    class Meta:
        model = Company
        fields = [
            'name', 'company_code', 'company_type', 'parent_company',
            'address', 'city', 'state', 'country', 'postal_code',
            'phone', 'email', 'latitude', 'longitude', 'is_active'
        ]
    
    def validate_company_code(self, value):
        """Validate company code uniqueness"""
        if Company.objects.filter(company_code=value).exists():
            raise serializers.ValidationError("Company code must be unique.")
        return value 