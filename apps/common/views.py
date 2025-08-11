from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from apps.sites.models import Site
from apps.companies.models import Entity
from apps.employees.models import Employee
from apps.incidents.models import Incident

class DashboardViewSet(viewsets.ViewSet):
    """ViewSet for dashboard functionality"""
    
    @action(detail=False, methods=['get'], url_path='stats')
    def dashboard_stats(self, request):
        """Get comprehensive dashboard statistics"""
        # Site statistics
        total_sites = Site.objects.filter(is_active=True).count()
        operational_sites = Site.objects.filter(
            is_active=True, operational_status='OPERATIONAL'
        ).count()
        maintenance_sites = Site.objects.filter(
            is_active=True, operational_status='MAINTENANCE'
        ).count()
        
        # Entity statistics
        total_entities = Entity.objects.filter(is_active=True).count()
        
        # Employee statistics
        total_employees = Employee.objects.filter(is_active=True).count()
        emergency_contacts = Employee.objects.filter(
            locations__show_in_emergency_contacts=True,
            locations__is_active=True,
            is_active=True
        ).distinct().count()
        
        # Incident statistics
        total_incidents = Incident.objects.filter(is_active=True).count()
        open_incidents = Incident.objects.filter(
            is_active=True, status='OPEN'
        ).count()
        critical_incidents = Incident.objects.filter(
            is_active=True, severity='CRITICAL'
        ).count()
        
        return Response({
            'sites': {
                'total': total_sites,
                'operational': operational_sites,
                'maintenance': maintenance_sites,
            },
            'entities': {
                'total': total_entities,
            },
            'employees': {
                'total': total_employees,
                'emergency_contacts': emergency_contacts,
            },
            'incidents': {
                'total': total_incidents,
                'open': open_incidents,
                'critical': critical_incidents,
            },
        })

    @action(detail=False, methods=['get'], url_path='site-stats')
    def site_stats(self, request):
        """Get detailed site statistics"""
        sites_by_status = Site.objects.filter(is_active=True).values('operational_status').annotate(
            count=Count('id')
        )
        sites_by_type = Site.objects.filter(is_active=True).values('plant_type').annotate(
            count=Count('id')
        )
        
        return Response({
            'by_status': list(sites_by_status),
            'by_type': list(sites_by_type),
        })

    @action(detail=False, methods=['get'], url_path='entity-stats')
    def entity_stats(self, request):
        """Get detailed entity statistics"""
        entities_by_type = Entity.objects.filter(is_active=True).values('entity_type').annotate(
            count=Count('id')
        )
        
        return Response({
            'by_type': list(entities_by_type),
        })

    @action(detail=False, methods=['get'], url_path='incident-stats')
    def incident_stats(self, request):
        """Get detailed incident statistics"""
        incidents_by_severity = Incident.objects.filter(is_active=True).values('severity').annotate(
            count=Count('id')
        )
        incidents_by_status = Incident.objects.filter(is_active=True).values('status').annotate(
            count=Count('id')
        )
        
        return Response({
            'by_severity': list(incidents_by_severity),
            'by_status': list(incidents_by_status),
        }) 