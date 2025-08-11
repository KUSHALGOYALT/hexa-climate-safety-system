from rest_framework import serializers
from .models import Employee, EmployeeLocation

class EmployeeLocationSerializer(serializers.ModelSerializer):
    location_name = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeLocation
        fields = [
            'id', 'location_type', 'location_id', 'location_name',
            'show_in_emergency_contacts', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_location_name(self, obj):
        """Get the location name based on location_type and location_id"""
        if obj.location_type == 'headquarters':
            return 'Hexa Climate'
        elif obj.location_type == 'company':
            return 'Hexa Climate'
        elif obj.location_type == 'site':
            return f'Site {obj.location_id}'
        elif obj.location_type == 'entity':
            return f'Entity {obj.location_id}'
        return 'Unknown Location'

    def validate(self, data):
        """Validate location assignment"""
        location_type = data.get('location_type')
        location_id = data.get('location_id')

        # Basic validation without database queries
        if location_type == 'headquarters':
            if location_id != 'headquarters':
                raise serializers.ValidationError("Headquarters location_id must be 'headquarters'")
        elif location_type == 'company':
            if location_id != 'company':
                raise serializers.ValidationError("Company location_id must be 'company'")
        elif location_type in ['site', 'entity']:
            # Basic validation - just check if it's a positive integer
            try:
                int(location_id)
                if int(location_id) <= 0:
                    raise serializers.ValidationError(f"Invalid {location_type} ID")
            except (ValueError, TypeError):
                raise serializers.ValidationError(f"Invalid {location_type} ID format")

        return data

class EmployeeSerializer(serializers.ModelSerializer):
    locations = EmployeeLocationSerializer(many=True, read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'name', 'email', 'phone',
            'designation', 'department', 'is_active',
            'locations', 'created_at', 'updated_at'
        ]

class EmployeeListSerializer(serializers.ModelSerializer):
    locations = EmployeeLocationSerializer(many=True, read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'name', 'email', 'phone',
            'designation', 'department', 'is_active',
            'locations', 'created_at', 'updated_at'
        ]

class EmergencyContactSerializer(serializers.ModelSerializer):
    locations = EmployeeLocationSerializer(many=True, read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'name', 'email', 'phone',
            'designation', 'department', 'locations'
        ] 