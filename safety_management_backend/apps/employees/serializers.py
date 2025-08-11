from rest_framework import serializers
from .models import Employee, EmployeeAssignment
from apps.companies.serializers import CompanySerializer
from apps.sites.serializers import SiteSerializer

class EmployeeSerializer(serializers.ModelSerializer):
    """Full serializer for Employee model"""
    company = CompanySerializer(read_only=True)
    company_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Employee
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def to_representation(self, instance):
        """Custom representation for API responses"""
        data = super().to_representation(instance)
        data['full_name'] = instance.full_name
        data['is_emergency_contact'] = instance.is_emergency_contact
        return data

class EmployeeListSerializer(serializers.ModelSerializer):
    """Simplified serializer for employee lists"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = Employee
        fields = [
            'id', 'name', 'employee_id', 'position', 'employment_type',
            'company_name', 'phone', 'email', 'is_active', 'created_at'
        ]
        read_only_fields = ('created_at',)

class EmployeeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating employees"""
    
    class Meta:
        model = Employee
        fields = [
            'company', 'name', 'employee_id', 'position', 'employment_type',
            'phone', 'email', 'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship', 'is_active'
        ]
    
    def validate_employee_id(self, value):
        """Validate employee ID uniqueness"""
        if Employee.objects.filter(employee_id=value).exists():
            raise serializers.ValidationError("Employee ID must be unique.")
        return value

class EmployeeAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for employee assignments"""
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    site_name = serializers.CharField(source='site.name', read_only=True)
    
    class Meta:
        model = EmployeeAssignment
        fields = [
            'id', 'employee', 'employee_name', 'site', 'site_name',
            'is_primary', 'is_active', 'assigned_date', 'end_date'
        ]
        read_only_fields = ('assigned_date',)

class EmergencyContactSerializer(serializers.ModelSerializer):
    """Serializer for emergency contacts (employees)"""
    
    class Meta:
        model = Employee
        fields = [
            'id', 'name', 'position', 'phone', 'email',
            'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship'
        ]
    
    def to_representation(self, instance):
        """Custom representation for emergency contacts"""
        data = super().to_representation(instance)
        data['contact_name'] = instance.emergency_contact_name or instance.name
        data['contact_phone'] = instance.emergency_contact_phone or instance.phone
        data['contact_relationship'] = instance.emergency_contact_relationship or 'Employee'
        return data 