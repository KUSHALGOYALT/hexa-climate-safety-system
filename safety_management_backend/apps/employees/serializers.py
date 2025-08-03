from rest_framework import serializers
from .models import Employee, EmployeeLocation
from apps.sites.models import Site
from apps.companies.models import Entity

class EmployeeLocationSerializer(serializers.ModelSerializer):
    """Serializer for employee location assignments"""
    location_name = serializers.CharField(read_only=True)

    class Meta:
        model = EmployeeLocation
        fields = [
            'id', 'location_type', 'location_id', 'location_name',
            'show_in_emergency_contacts', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        """Validate location assignment"""
        location_type = data.get('location_type')
        location_id = data.get('location_id')
        
        if location_type == 'site':
            try:
                Site.objects.get(id=location_id)
            except (Site.DoesNotExist, ValueError):
                raise serializers.ValidationError("Invalid site ID")
        elif location_type == 'entity':
            try:
                Entity.objects.get(id=location_id)
            except (Entity.DoesNotExist, ValueError):
                raise serializers.ValidationError("Invalid entity ID")
        elif location_type == 'headquarters':
            if location_id != 'headquarters':
                raise serializers.ValidationError("Headquarters location_id must be 'headquarters'")
        elif location_type == 'company':
            if location_id != 'company':
                raise serializers.ValidationError("Company location_id must be 'company'")
        
        return data


class EmployeeSerializer(serializers.ModelSerializer):
    """Full serializer for employee details"""
    locations = EmployeeLocationSerializer(many=True, read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'name', 'email', 'phone', 
            'designation', 'department', 'is_active',
            'locations', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_employee_id(self, value):
        """Validate that employee_id is unique"""
        if self.instance:
            if Employee.objects.filter(employee_id=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("Employee ID already exists.")
        else:
            if Employee.objects.filter(employee_id=value).exists():
                raise serializers.ValidationError("Employee ID already exists.")
        return value

    def validate_email(self, value):
        """Validate that email is unique"""
        if self.instance:
            if Employee.objects.filter(email=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("Email already exists.")
        else:
            if Employee.objects.filter(email=value).exists():
                raise serializers.ValidationError("Email already exists.")
        return value


class EmployeeListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing employees"""
    locations = EmployeeLocationSerializer(many=True, read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'name', 'email', 'phone',
            'designation', 'department', 'is_active',
            'locations', 'created_at'
        ]


class EmployeeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating employees"""
    
    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'name', 'email', 'phone',
            'designation', 'department', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_employee_id(self, value):
        """Validate that employee_id is unique"""
        if self.instance:
            if Employee.objects.filter(employee_id=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("Employee ID already exists.")
        else:
            if Employee.objects.filter(employee_id=value).exists():
                raise serializers.ValidationError("Employee ID already exists.")
        return value

    def validate_email(self, value):
        """Validate that email is unique"""
        if self.instance:
            if Employee.objects.filter(email=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("Email already exists.")
        else:
            if Employee.objects.filter(email=value).exists():
                raise serializers.ValidationError("Email already exists.")
        return value


class EmergencyContactSerializer(serializers.ModelSerializer):
    """Serializer for emergency contacts"""
    locations = EmployeeLocationSerializer(many=True, read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'name', 'email', 'phone', 'designation', 'department',
            'locations'
        ]
