from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Employee, EmployeeLocation
from .serializers import (
    EmployeeSerializer, EmployeeListSerializer, EmployeeLocationSerializer,
    EmergencyContactSerializer
)

class EmployeeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing employees"""
    queryset = Employee.objects.prefetch_related('locations').all()
    serializer_class = EmployeeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'department']
    search_fields = ['name', 'employee_id', 'email', 'phone']
    ordering_fields = ['name', 'created_at', 'employee_id']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeeListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EmployeeSerializer
        return EmployeeSerializer

    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """Get dashboard statistics for employees"""
        total_employees = Employee.objects.filter(is_active=True).count()
        emergency_contacts = Employee.objects.filter(
            locations__show_in_emergency_contacts=True,
            locations__is_active=True,
            is_active=True
        ).distinct().count()
        
        return Response({
            'total_employees': total_employees,
            'emergency_contacts': emergency_contacts,
        })

class EmployeeLocationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing employee locations"""
    queryset = EmployeeLocation.objects.select_related('employee').all()
    serializer_class = EmployeeLocationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['location_type', 'show_in_emergency_contacts', 'is_active']
    search_fields = ['employee__name', 'location_id']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'], url_path='emergency-contacts')
    def emergency_contacts(self, request):
        """Get all emergency contacts"""
        location_type = request.query_params.get('location_type')
        location_id = request.query_params.get('location_id')
        
        queryset = Employee.objects.filter(
            locations__show_in_emergency_contacts=True,
            locations__is_active=True,
            is_active=True
        ).distinct()
        
        if location_type:
            queryset = queryset.filter(locations__location_type=location_type)
        
        if location_id:
            queryset = queryset.filter(locations__location_id=location_id)
        
        serializer = EmergencyContactSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='emergency-contacts/headquarters')
    def headquarters_emergency_contacts(self, request):
        """Get emergency contacts for headquarters"""
        employees = Employee.get_emergency_contacts_by_headquarters()
        serializer = EmergencyContactSerializer(employees, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='emergency-contacts/company')
    def company_emergency_contacts(self, request):
        """Get emergency contacts for company"""
        employees = Employee.get_emergency_contacts_by_company()
        serializer = EmergencyContactSerializer(employees, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='emergency-contacts/entity/(?P<entity_id>[^/.]+)')
    def entity_emergency_contacts(self, request, entity_id=None):
        """Get emergency contacts for specific entity"""
        employees = Employee.get_emergency_contacts_by_entity(entity_id)
        serializer = EmergencyContactSerializer(employees, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='emergency-contacts/site/(?P<site_id>[^/.]+)')
    def site_emergency_contacts(self, request, site_id=None):
        """Get emergency contacts for specific site"""
        employees = Employee.get_emergency_contacts_by_site(site_id)
        serializer = EmergencyContactSerializer(employees, many=True)
        return Response(serializer.data) 