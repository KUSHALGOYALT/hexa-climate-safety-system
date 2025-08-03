from rest_framework import serializers
from .models import EmergencyContact, NationalEmergencyContact

class EmergencyContactSerializer(serializers.ModelSerializer):
    site_name = serializers.CharField(source='site.name', read_only=True)

    class Meta:
        model = EmergencyContact
        fields = '__all__'

class NationalEmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = NationalEmergencyContact
        fields = '__all__'
