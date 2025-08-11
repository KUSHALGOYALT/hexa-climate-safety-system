from rest_framework import serializers
from .models import Incident
from apps.sites.serializers import SiteSerializer
from apps.employees.serializers import EmployeeSerializer

class IncidentSerializer(serializers.ModelSerializer):
    """Full serializer for Incident model"""
    site = SiteSerializer(read_only=True)
    site_id = serializers.IntegerField(write_only=True)
    assigned_to = EmployeeSerializer(read_only=True)
    
    class Meta:
        model = Incident
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def to_representation(self, instance):
        """Custom representation for API responses"""
        data = super().to_representation(instance)
        data['is_open'] = instance.is_open
        data['is_resolved'] = instance.is_resolved
        data['days_open'] = instance.days_open
        return data

class IncidentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for incident lists"""
    site_name = serializers.CharField(source='site.name', read_only=True)
    company_name = serializers.CharField(source='site.company.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.name', read_only=True)
    
    class Meta:
        model = Incident
        fields = [
            'id', 'title', 'incident_type', 'severity', 'status',
            'site_name', 'company_name', 'reported_by', 'assigned_to_name',
            'incident_date', 'created_at'
        ]
        read_only_fields = ('created_at',)

class IncidentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating incidents"""
    
    class Meta:
        model = Incident
        fields = [
            'site', 'incident_type', 'severity', 'status',
            'title', 'description', 'location',
            'reported_by', 'contact_number', 'email', 'anonymous',
            'assigned_to', 'incident_date', 'actions_taken',
            'recommendations', 'cost_estimate'
        ]

class AnonymousIncidentSerializer(serializers.ModelSerializer):
    """Serializer for anonymous incident reporting"""
    
    class Meta:
        model = Incident
        fields = [
            'site', 'incident_type', 'severity', 'title', 'description',
            'location', 'reported_by', 'contact_number', 'email', 'anonymous'
        ]
    
    def create(self, validated_data):
        """Set default values for anonymous incidents"""
        validated_data['status'] = 'OPEN'
        validated_data['anonymous'] = True
        return super().create(validated_data)

class IncidentStatusSerializer(serializers.ModelSerializer):
    """Serializer for updating incident status"""
    
    class Meta:
        model = Incident
        fields = ['status', 'actions_taken', 'recommendations']
    
    def validate_status(self, value):
        """Validate status transitions"""
        instance = self.instance
        if instance and instance.status == 'CLOSED' and value != 'CLOSED':
            raise serializers.ValidationError("Cannot change status of closed incident.")
        return value

class IncidentAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for assigning incidents"""
    
    class Meta:
        model = Incident
        fields = ['assigned_to']
    
    def update(self, instance, validated_data):
        """Update assignment and status"""
        instance.assigned_to = validated_data.get('assigned_to', instance.assigned_to)
        if instance.assigned_to and instance.status == 'OPEN':
            instance.status = 'IN_PROGRESS'
        instance.save()
        return instance 