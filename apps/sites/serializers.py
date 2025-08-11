from rest_framework import serializers
from .models import Site

class SiteSerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(source='entity.name', read_only=True)
    company_name = serializers.CharField(source='entity.company.name', read_only=True)
    company_code = serializers.CharField(source='entity.company.company_code', read_only=True)

    class Meta:
        model = Site
        fields = '__all__'

class SiteListSerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(source='entity.name', read_only=True)
    company_name = serializers.CharField(source='entity.company.name', read_only=True)
    company_code = serializers.CharField(source='entity.company.company_code', read_only=True)

    class Meta:
        model = Site
        fields = [
            'id', 'name', 'site_code', 'entity_name', 'company_name', 'company_code',
            'plant_type', 'operational_status', 'city', 'state', 'country', 'is_active',
            'created_at', 'updated_at'
        ]

class SiteQRSerializer(serializers.ModelSerializer):
    qr_code = serializers.SerializerMethodField()
    entity_name = serializers.CharField(source='entity.name', read_only=True)
    company_name = serializers.CharField(source='entity.company.name', read_only=True)
    company_code = serializers.CharField(source='entity.company.company_code', read_only=True)

    class Meta:
        model = Site
        fields = [
            'id', 'name', 'site_code', 'entity_name', 'company_name', 'company_code',
            'qr_code', 'public_url'
        ]

    def get_qr_code(self, obj):
        qr_data = obj.generate_qr_data()
        return qr_data['qr_code']

    @property
    def public_url(self):
        return f"http://localhost:3000/public/{self.entity.company.company_code}/{self.site_code}"

class PublicSiteSerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(source='entity.name', read_only=True)
    company_name = serializers.CharField(source='entity.company.name', read_only=True)
    company_code = serializers.CharField(source='entity.company.company_code', read_only=True)

    class Meta:
        model = Site
        fields = [
            'id', 'name', 'site_code', 'entity_name', 'company_name', 'company_code',
            'plant_type', 'operational_status', 'address', 'city', 'state', 'country',
            'phone', 'email', 'latitude', 'longitude'
        ] 