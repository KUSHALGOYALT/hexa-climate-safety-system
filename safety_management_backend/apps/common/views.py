from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count

from .models import EmergencyContact
from .serializers import (
    EmergencyContactSerializer,
    EmergencyContactListSerializer,
    EmergencyContactCreateUpdateSerializer
)
from apps.companies.models import Company
from apps.sites.models import Site

class EmergencyContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing emergency contacts
    """
    queryset = EmergencyContact.objects.select_related('company', 'site').all()
    serializer_class = EmergencyContactSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['company', 'site', 'contact_type', 'is_active', 'is_primary']
    search_fields = ['name', 'position', 'phone', 'email']
    ordering_fields = ['name', 'created_at', 'contact_type']
    ordering = ['-is_primary', 'name']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return EmergencyContactListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EmergencyContactCreateUpdateSerializer
        return EmergencyContactSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()

        # Filter by company if provided
        company_id = self.request.query_params.get('company')
        if company_id:
            queryset = queryset.filter(company_id=company_id)

        # Filter by site if provided
        site_id = self.request.query_params.get('site')
        if site_id:
            queryset = queryset.filter(site_id=site_id)

        # Filter by active contacts only if specified
        active_only = self.request.query_params.get('active_only')
        if active_only and active_only.lower() == 'true':
            queryset = queryset.filter(is_active=True)

        # Filter by primary contacts only
        primary_only = self.request.query_params.get('primary_only')
        if primary_only and primary_only.lower() == 'true':
            queryset = queryset.filter(is_primary=True)

        return queryset

    @action(detail=False, methods=['get'], url_path='by-company/(?P<company_id>[^/.]+)')
    def by_company(self, request, company_id=None):
        """Get emergency contacts for a specific company"""
        try:
            company = get_object_or_404(Company, id=company_id)
            contacts = self.get_queryset().filter(
                company=company,
                is_active=True
            )
            serializer = self.get_serializer(contacts, many=True)
            return Response(serializer.data)
        except Company.DoesNotExist:
            return Response(
                {'error': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], url_path='by-site/(?P<site_id>[^/.]+)')
    def by_site(self, request, site_id=None):
        """Get emergency contacts for a specific site"""
        try:
            site = get_object_or_404(Site, id=site_id)
            contacts = self.get_queryset().filter(
                site=site,
                is_active=True
            )
            serializer = self.get_serializer(contacts, many=True)
            return Response(serializer.data)
        except Site.DoesNotExist:
            return Response(
                {'error': 'Site not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], url_path='primary')
    def primary_contacts(self, request):
        """Get all primary emergency contacts"""
        contacts = self.get_queryset().filter(
            is_primary=True,
            is_active=True
        )
        serializer = self.get_serializer(contacts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        """Toggle emergency contact active status"""
        contact = self.get_object()
        contact.is_active = not contact.is_active
        contact.save()
        
        return Response({
            'id': contact.id,
            'is_active': contact.is_active,
            'message': f"Emergency contact {'activated' if contact.is_active else 'deactivated'} successfully"
        })

    @action(detail=True, methods=['post'], url_path='toggle-primary')
    def toggle_primary(self, request, pk=None):
        """Toggle primary contact status"""
        contact = self.get_object()
        contact.is_primary = not contact.is_primary
        contact.save()
        
        return Response({
            'id': contact.id,
            'is_primary': contact.is_primary,
            'message': f"Emergency contact {'set as primary' if contact.is_primary else 'removed as primary'} successfully"
        })

    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """Get dashboard statistics for emergency contacts"""
        total_contacts = EmergencyContact.objects.count()
        active_contacts = EmergencyContact.objects.filter(is_active=True).count()
        primary_contacts = EmergencyContact.objects.filter(is_primary=True, is_active=True).count()
        
        # Contact type distribution
        type_distribution = EmergencyContact.objects.values('contact_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Company distribution
        company_distribution = EmergencyContact.objects.values('company__name').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        stats = {
            'total_contacts': total_contacts,
            'active_contacts': active_contacts,
            'primary_contacts': primary_contacts,
            'type_distribution': list(type_distribution),
            'company_distribution': list(company_distribution)
        }
        
        return Response(stats)

    def perform_create(self, serializer):
        """Custom create logic"""
        contact = serializer.save()
        return contact

    def perform_update(self, serializer):
        """Custom update logic"""
        contact = serializer.save()
        return contact

    def perform_destroy(self, instance):
        """Custom delete logic"""
        instance.delete()
