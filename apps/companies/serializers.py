from rest_framework import serializers
from .models import Company, Entity

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

class EntitySerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_code = serializers.CharField(source='company.company_code', read_only=True)

    class Meta:
        model = Entity
        fields = '__all__'

class EntityListSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_code = serializers.CharField(source='company.company_code', read_only=True)

    class Meta:
        model = Entity
        fields = [
            'id', 'name', 'entity_code', 'entity_type', 'company_name', 'company_code',
            'city', 'state', 'country', 'is_active', 'created_at', 'updated_at'
        ]

class EntityQRSerializer(serializers.ModelSerializer):
    qr_code = serializers.SerializerMethodField()
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_code = serializers.CharField(source='company.company_code', read_only=True)

    class Meta:
        model = Entity
        fields = [
            'id', 'name', 'entity_code', 'entity_type', 'company_name', 'company_code',
            'qr_code', 'public_url'
        ]

    def get_qr_code(self, obj):
        qr_data = obj.generate_qr_data()
        return qr_data['qr_code']

    @property
    def public_url(self):
        return f"http://localhost:3000/public/{self.company.company_code}/entity/{self.entity_code}" 