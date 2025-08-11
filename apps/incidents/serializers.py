from rest_framework import serializers
from .models import Incident

class IncidentSerializer(serializers.ModelSerializer):
    location_name = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = '__all__'

    def get_location_name(self, obj):
        return obj.location_name

class IncidentListSerializer(serializers.ModelSerializer):
    location_name = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = [
            'id', 'title', 'severity', 'status', 'location_type', 'location_id',
            'location_name', 'reporter_name', 'incident_date', 'reported_date',
            'is_active', 'created_at', 'updated_at'
        ]

    def get_location_name(self, obj):
        return obj.location_name 