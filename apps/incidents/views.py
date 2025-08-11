from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Incident
from .serializers import IncidentSerializer, IncidentListSerializer

class IncidentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing incidents"""
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['severity', 'status', 'location_type', 'is_active']
    search_fields = ['title', 'description', 'reporter_name']
    ordering_fields = ['incident_date', 'reported_date', 'severity', 'status']
    ordering = ['-reported_date']

    def get_serializer_class(self):
        if self.action == 'list':
            return IncidentListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return IncidentSerializer
        return IncidentSerializer

    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """Get dashboard statistics for incidents"""
        total_incidents = Incident.objects.filter(is_active=True).count()
        open_incidents = Incident.objects.filter(
            is_active=True, status='OPEN'
        ).count()
        critical_incidents = Incident.objects.filter(
            is_active=True, severity='CRITICAL'
        ).count()
        
        return Response({
            'total_incidents': total_incidents,
            'open_incidents': open_incidents,
            'critical_incidents': critical_incidents,
        }) 