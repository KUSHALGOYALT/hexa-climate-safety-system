from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from .models import Incident
from .serializers import (
    IncidentSerializer,
    IncidentListSerializer,
    IncidentCreateUpdateSerializer,
    AnonymousIncidentSerializer,
    IncidentStatusSerializer,
    IncidentAssignmentSerializer
)
from apps.employees.models import Employee

class IncidentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing incidents
    """
    queryset = Incident.objects.select_related('site', 'assigned_to').all()
    serializer_class = IncidentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['site', 'incident_type', 'severity', 'status', 'anonymous']
    search_fields = ['title', 'description', 'reported_by', 'location']
    ordering_fields = ['created_at', 'incident_date', 'severity', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return IncidentListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return IncidentCreateUpdateSerializer
        return IncidentSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()

        # Filter by site if provided
        site_id = self.request.query_params.get('site')
        if site_id:
            queryset = queryset.filter(site_id=site_id)

        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by incident type if provided
        incident_type = self.request.query_params.get('incident_type')
        if incident_type:
            queryset = queryset.filter(incident_type=incident_type)

        # Filter by severity if provided
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset

    @action(detail=False, methods=['post'], url_path='anonymous')
    def anonymous_incident(self, request):
        """Create anonymous incident"""
        serializer = AnonymousIncidentSerializer(data=request.data)
        if serializer.is_valid():
            incident = serializer.save()
            return Response(
                IncidentSerializer(incident).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        """Update incident status"""
        incident = self.get_object()
        serializer = IncidentStatusSerializer(incident, data=request.data, partial=True)
        if serializer.is_valid():
            incident = serializer.save()
            return Response(IncidentSerializer(incident).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='assign')
    def assign_incident(self, request, pk=None):
        """Assign incident to employee"""
        incident = self.get_object()
        serializer = IncidentAssignmentSerializer(incident, data=request.data, partial=True)
        if serializer.is_valid():
            incident = serializer.save()
            return Response(IncidentSerializer(incident).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """Get dashboard statistics for incidents"""
        total_incidents = Incident.objects.count()
        open_incidents = Incident.objects.filter(status__in=['OPEN', 'IN_PROGRESS']).count()
        resolved_incidents = Incident.objects.filter(status='RESOLVED').count()
        closed_incidents = Incident.objects.filter(status='CLOSED').count()
        
        # Recent activity
        last_30_days = timezone.now() - timedelta(days=30)
        recent_incidents = Incident.objects.filter(created_at__gte=last_30_days).count()
        
        # Incident type distribution
        type_distribution = Incident.objects.values('incident_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Severity distribution
        severity_distribution = Incident.objects.values('severity').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Status distribution
        status_distribution = Incident.objects.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        stats = {
            'total_incidents': total_incidents,
            'open_incidents': open_incidents,
            'resolved_incidents': resolved_incidents,
            'closed_incidents': closed_incidents,
            'recent_incidents': recent_incidents,
            'type_distribution': list(type_distribution),
            'severity_distribution': list(severity_distribution),
            'status_distribution': list(status_distribution)
        }
        
        return Response(stats)

    @action(detail=False, methods=['get'], url_path='trending')
    def trending_incidents(self, request):
        """Get trending incidents analysis"""
        # Get incidents from last 30 days
        last_30_days = timezone.now() - timedelta(days=30)
        recent_incidents = Incident.objects.filter(created_at__gte=last_30_days)
        
        # Most common incident types
        common_types = recent_incidents.values('incident_type').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Most common locations
        common_locations = recent_incidents.values('location').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # High severity incidents
        high_severity = recent_incidents.filter(severity__in=['HIGH', 'CRITICAL']).count()
        
        trending_data = {
            'common_types': list(common_types),
            'common_locations': list(common_locations),
            'high_severity_count': high_severity,
            'total_recent': recent_incidents.count()
        }
        
        return Response(trending_data)

    @action(detail=False, methods=['get'], url_path='export')
    def export_incidents(self, request):
        """Export incidents data"""
        format_type = request.query_params.get('format', 'json')
        date_range = request.query_params.get('date_range', '30')
        
        # Calculate date range
        days = int(date_range)
        start_date = timezone.now() - timedelta(days=days)
        
        incidents = self.get_queryset().filter(created_at__gte=start_date)
        
        if format_type == 'json':
            serializer = IncidentListSerializer(incidents, many=True)
            return Response(serializer.data)
        else:
            # For CSV export, you would implement CSV generation here
            return Response(
                {'error': 'CSV export not implemented yet'},
                status=status.HTTP_501_NOT_IMPLEMENTED
            )

    def perform_create(self, serializer):
        """Custom create logic"""
        incident = serializer.save()
        return incident

    def perform_update(self, serializer):
        """Custom update logic"""
        incident = serializer.save()
        return incident

    def perform_destroy(self, instance):
        """Custom delete logic"""
        instance.delete()
