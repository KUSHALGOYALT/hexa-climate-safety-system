from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Employee, EmployeeLocation
from .serializers import (
    EmployeeSerializer, EmployeeListSerializer, EmployeeCreateUpdateSerializer,
    EmergencyContactSerializer, EmployeeLocationSerializer
)
from apps.sites.models import Site
from apps.companies.models import Entity
from django.db import models


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing employees with multiple location assignments
    """
    queryset = Employee.objects.prefetch_related('locations').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'employee_id', 'email', 'phone', 'designation', 'department']
    ordering_fields = ['name', 'employee_id', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeeListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EmployeeCreateUpdateSerializer
        return EmployeeSerializer

    @action(detail=True, methods=['get'], url_path='locations')
    def get_locations(self, request, pk=None):
        """Get all location assignments for an employee"""
        employee = self.get_object()
        locations = employee.locations.all()
        serializer = EmployeeLocationSerializer(locations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='locations')
    def add_location(self, request, pk=None):
        """Add a location assignment to an employee"""
        employee = self.get_object()
        serializer = EmployeeLocationSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(employee=employee)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='by-location-type/(?P<location_type>[^/.]+)')
    def get_by_location_type(self, request, location_type=None):
        """Get all employees for a specific location type"""
        employees = Employee.objects.filter(
            locations__location_type=location_type,
            locations__is_active=True,
            is_active=True
        ).distinct()
        serializer = EmployeeListSerializer(employees, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by-site/(?P<site_id>[^/.]+)')
    def get_by_site(self, request, site_id=None):
        """Get all employees assigned to a specific site"""
        try:
            site = Site.objects.get(id=site_id, is_active=True)
            employees = Employee.objects.filter(
                locations__location_type='site',
                locations__location_id=site_id,
                locations__is_active=True,
                is_active=True
            ).distinct()
            serializer = EmployeeListSerializer(employees, many=True)
            return Response(serializer.data)
        except Site.DoesNotExist:
            return Response(
                {'error': 'Site not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], url_path='by-entity/(?P<entity_id>[^/.]+)')
    def get_by_entity(self, request, entity_id=None):
        """Get all employees assigned to a specific entity"""
        try:
            entity = Entity.objects.get(id=entity_id, is_active=True)
            employees = Employee.objects.filter(
                locations__location_type='entity',
                locations__location_id=entity_id,
                locations__is_active=True,
                is_active=True
            ).distinct()
            serializer = EmployeeListSerializer(employees, many=True)
            return Response(serializer.data)
        except Entity.DoesNotExist:
            return Response(
                {'error': 'Entity not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], url_path='emergency-contacts')
    def get_emergency_contacts(self, request):
        """Get all employees marked as emergency contacts"""
        employees = Employee.objects.filter(
            is_active=True,
            locations__show_in_emergency_contacts=True,
            locations__is_active=True
        ).distinct()
        serializer = EmergencyContactSerializer(employees, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='emergency-contacts-by-site/(?P<site_id>[^/.]+)')
    def get_emergency_contacts_by_site(self, request, site_id=None):
        """Get emergency contacts for a specific site"""
        try:
            site = Site.objects.get(id=site_id, is_active=True)
            employees = Employee.get_emergency_contacts_by_site(site_id)
            serializer = EmergencyContactSerializer(employees, many=True)
            return Response(serializer.data)
        except Site.DoesNotExist:
            return Response(
                {'error': 'Site not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], url_path='emergency-contacts-by-entity/(?P<entity_id>[^/.]+)')
    def get_emergency_contacts_by_entity(self, request, entity_id=None):
        """Get emergency contacts for a specific entity"""
        try:
            entity = Entity.objects.get(id=entity_id, is_active=True)
            employees = Employee.get_emergency_contacts_by_entity(entity_id)
            serializer = EmergencyContactSerializer(employees, many=True)
            return Response(serializer.data)
        except Entity.DoesNotExist:
            return Response(
                {'error': 'Entity not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], url_path='emergency-contacts-headquarters')
    def get_emergency_contacts_headquarters(self, request):
        """Get emergency contacts for headquarters"""
        employees = Employee.get_emergency_contacts_by_headquarters()
        serializer = EmergencyContactSerializer(employees, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='emergency-contacts-company')
    def get_emergency_contacts_company(self, request):
        """Get emergency contacts for company"""
        employees = Employee.get_emergency_contacts_by_company()
        serializer = EmergencyContactSerializer(employees, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='toggle-active')
    def toggle_active(self, request, pk=None):
        """Toggle employee active status"""
        employee = self.get_object()
        employee.is_active = not employee.is_active
        employee.save()
        serializer = EmployeeSerializer(employee)
        return Response(serializer.data)


class EmployeeLocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing employee location assignments
    """
    queryset = EmployeeLocation.objects.select_related('employee').all()
    serializer_class = EmployeeLocationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'location_type', 'show_in_emergency_contacts']
    search_fields = ['employee__name', 'location_id']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    @action(detail=True, methods=['patch'], url_path='toggle-emergency-contact')
    def toggle_emergency_contact(self, request, pk=None):
        """Toggle emergency contact status for a location assignment"""
        location = self.get_object()
        location.show_in_emergency_contacts = not location.show_in_emergency_contacts
        location.save()
        serializer = EmployeeLocationSerializer(location)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='toggle-active')
    def toggle_active(self, request, pk=None):
        """Toggle location assignment active status"""
        location = self.get_object()
        location.is_active = not location.is_active
        location.save()
        serializer = EmployeeLocationSerializer(location)
        return Response(serializer.data)
