from rest_framework import serializers
from .models import Company, Entity

class EntitySerializer(serializers.ModelSerializer):
    """Serializer for Entity model"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_code = serializers.CharField(source='company.company_code', read_only=True)
    sites_count = serializers.SerializerMethodField()

    class Meta:
        model = Entity
        fields = [
            'id', 'name', 'entity_code', 'entity_type', 'company', 'company_name', 
            'company_code', 'description', 'address', 'city', 'state', 'country',
            'phone', 'email', 'is_active', 'sites_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_sites_count(self, obj):
        return obj.get_sites_count()

    def validate_entity_code(self, value):
        """Validate entity code uniqueness"""
        # Removed alphanumeric validation - allow any characters
        return value

class EntityListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing entities"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    sites_count = serializers.SerializerMethodField()

    class Meta:
        model = Entity
        fields = [
            'id', 'name', 'entity_code', 'entity_type', 'company_name',
            'description', 'address', 'city', 'state', 'country',
            'phone', 'email', 'is_active', 'sites_count'
        ]

    def get_sites_count(self, obj):
        return obj.get_sites_count()

class CompanySerializer(serializers.ModelSerializer):
    """Full serializer for company details"""
    subsidiaries = serializers.SerializerMethodField()
    entities = EntitySerializer(many=True, read_only=True)
    entities_count = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = '__all__'

    def get_subsidiaries(self, obj):
        """Get subsidiaries of this company"""
        subsidiaries = obj.subsidiaries.all()
        return CompanyListSerializer(subsidiaries, many=True).data

    def get_entities_count(self, obj):
        return obj.entities.count()

class CompanyListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing companies"""
    subsidiaries_count = serializers.SerializerMethodField()
    entities_count = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'company_code', 'company_type', 'parent_company',
            'city', 'state', 'country', 'is_active', 'subsidiaries_count',
            'entities_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_subsidiaries_count(self, obj):
        return obj.subsidiaries.count()

    def get_entities_count(self, obj):
        return obj.entities.count()

class CompanyCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating companies"""
    
    class Meta:
        model = Company
        fields = '__all__'
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True}
        }

    def validate_company_code(self, value):
        """Validate company code format and uniqueness"""
        if not value.isalnum():
            raise serializers.ValidationError(
                "Company code should contain only alphanumeric characters."
            )
        return value.upper()

    def validate(self, data):
        """Validate company data"""
        # If this is a subsidiary, ensure parent_company is set
        if data.get('company_type') == 'SUBSIDIARY' and not data.get('parent_company'):
            raise serializers.ValidationError(
                "Parent company must be specified for subsidiaries."
            )
        return data
