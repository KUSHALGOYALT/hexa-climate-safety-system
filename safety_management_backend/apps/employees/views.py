from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from .models import Employee, EmployeeAssignment
from .serializers import (
    EmployeeSerializer,
    EmployeeListSerializer,
    EmployeeCreateUpdateSerializer,
    EmployeeAssignmentSerializer,
    EmergencyContactSerializer
)
from apps.companies.models import Company
from apps.sites.models import Site

class EmployeeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing employees
    """
    queryset = Employee.objects.select_related('company').all()
    serializer_class = EmployeeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['company', 'employment_type', 'is_active']
    search_fields = ['name', 'employee_id', 'position', 'email']
    ordering_fields = ['name', 'created_at', 'employee_id']
    ordering = ['name']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return EmployeeListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EmployeeCreateUpdateSerializer
        return EmployeeSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()

        # Filter by company if provided
        company_id = self.request.query_params.get('company')
        if company_id:
            queryset = queryset.filter(company_id=company_id)

        # Filter by active employees only if specified
        active_only = self.request.query_params.get('active_only')
        if active_only and active_only.lower() == 'true':
            queryset = queryset.filter(is_active=True)

        return queryset

    @action(detail=False, methods=['get'], url_path='emergency-contacts')
    def emergency_contacts(self, request):
        """Get all emergency contacts"""
        employees = self.get_queryset().filter(is_active=True)
        serializer = EmergencyContactSerializer(employees, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='emergency-contacts-by-site/(?P<site_id>[^/.]+)')
    def emergency_contacts_by_site(self, request, site_id=None):
        """Get emergency contacts for a specific site"""
        try:
            site = get_object_or_404(Site, id=site_id)
            # Get employees assigned to this site
            assigned_employees = EmployeeAssignment.objects.filter(
                site=site,
                is_active=True
            ).values_list('employee_id', flat=True)
            
            employees = self.get_queryset().filter(
                id__in=assigned_employees,
                is_active=True
            )
            serializer = EmergencyContactSerializer(employees, many=True)
            return Response(serializer.data)
        except Site.DoesNotExist:
            return Response(
                {'error': 'Site not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], url_path='emergency-contacts-by-company/(?P<company_id>[^/.]+)')
    def emergency_contacts_by_company(self, request, company_id=None):
        """Get emergency contacts for a specific company"""
        try:
            company = get_object_or_404(Company, id=company_id)
            employees = self.get_queryset().filter(
                company=company,
                is_active=True
            )
            serializer = EmergencyContactSerializer(employees, many=True)
            return Response(serializer.data)
        except Company.DoesNotExist:
            return Response(
                {'error': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        """Toggle employee active status"""
        employee = self.get_object()
        employee.is_active = not employee.is_active
        employee.save()
        
        return Response({
            'id': employee.id,
            'is_active': employee.is_active,
            'message': f"Employee {'activated' if employee.is_active else 'deactivated'} successfully"
        })

    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """Get dashboard statistics for employees"""
        total_employees = Employee.objects.count()
        active_employees = Employee.objects.filter(is_active=True).count()
        
        # Employment type distribution
        employment_distribution = Employee.objects.values('employment_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Recent activity
        last_30_days = timezone.now() - timedelta(days=30)
        recent_employees = Employee.objects.filter(created_at__gte=last_30_days).count()
        
        stats = {
            'total_employees': total_employees,
            'active_employees': active_employees,
            'recent_employees': recent_employees,
            'employment_distribution': list(employment_distribution)
        }
        
        return Response(stats)

    def perform_create(self, serializer):
        """Custom create logic"""
        employee = serializer.save()
        return employee

    def perform_update(self, serializer):
        """Custom update logic"""
        employee = serializer.save()
        return employee

    def perform_destroy(self, instance):
        """Custom delete logic"""
        instance.delete()

class EmployeeAssignmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing employee assignments
    """
    queryset = EmployeeAssignment.objects.select_related('employee', 'site').all()
    serializer_class = EmployeeAssignmentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['employee', 'site', 'is_active', 'is_primary']
    search_fields = ['employee__name', 'site__name']
    ordering_fields = ['assigned_date', 'employee__name', 'site__name']
    ordering = ['-assigned_date']

    @action(detail=True, methods=['post'], url_path='toggle-primary')
    def toggle_primary(self, request, pk=None):
        """Toggle primary assignment status"""
        assignment = self.get_object()
        assignment.is_primary = not assignment.is_primary
        assignment.save()
        
        return Response({
            'id': assignment.id,
            'is_primary': assignment.is_primary,
            'message': f"Assignment {'set as primary' if assignment.is_primary else 'removed as primary'} successfully"
        })

    @action(detail=True, methods=['post'], url_path='toggle-active')
    def toggle_active(self, request, pk=None):
        """Toggle assignment active status"""
        assignment = self.get_object()
        assignment.is_active = not assignment.is_active
        assignment.save()
        
        return Response({
            'id': assignment.id,
            'is_active': assignment.is_active,
            'message': f"Assignment {'activated' if assignment.is_active else 'deactivated'} successfully"
        })

    def perform_create(self, serializer):
        """Custom create logic"""
        assignment = serializer.save()
        return assignment

    def perform_update(self, serializer):
        """Custom update logic"""
        assignment = serializer.save()
        return assignment

    def perform_destroy(self, instance):
        """Custom delete logic"""
        instance.delete()
