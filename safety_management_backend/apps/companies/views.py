from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from .models import Company
from .serializers import (
    CompanySerializer,
    CompanyListSerializer,
    CompanyCreateUpdateSerializer
)

class CompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing companies (headquarters)
    """
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['company_type', 'is_active', 'state', 'country']
    search_fields = ['name', 'company_code', 'city', 'state']
    ordering_fields = ['name', 'created_at', 'company_code']
    ordering = ['name']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return CompanyListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CompanyCreateUpdateSerializer
        return CompanySerializer

    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()

        # Filter by active companies only if specified
        active_only = self.request.query_params.get('active_only')
        if active_only and active_only.lower() == 'true':
            queryset = queryset.filter(is_active=True)

        # Filter by headquarters only
        headquarters_only = self.request.query_params.get('headquarters_only')
        if headquarters_only and headquarters_only.lower() == 'true':
            queryset = queryset.filter(company_type='HEADQUARTERS')

        return queryset

    @action(detail=False, methods=['get'], url_path='headquarters')
    def headquarters(self, request):
        """Get all headquarters companies"""
        headquarters = self.get_queryset().filter(company_type='HEADQUARTERS')
        serializer = self.get_serializer(headquarters, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """Get dashboard statistics for companies"""
        total_companies = Company.objects.count()
        active_companies = Company.objects.filter(is_active=True).count()
        headquarters_count = Company.objects.filter(company_type='HEADQUARTERS').count()
        
        # Recent activity
        last_30_days = timezone.now() - timedelta(days=30)
        recent_companies = Company.objects.filter(created_at__gte=last_30_days).count()
        
        # State distribution
        state_distribution = Company.objects.values('state').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        stats = {
            'total_companies': total_companies,
            'active_companies': active_companies,
            'headquarters_count': headquarters_count,
            'recent_companies': recent_companies,
            'state_distribution': list(state_distribution)
        }
        
        return Response(stats)

    @action(detail=True, methods=['post'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        """Toggle company active status"""
        company = self.get_object()
        company.is_active = not company.is_active
        company.save()
        
        return Response({
            'id': company.id,
            'is_active': company.is_active,
            'message': f"Company {'activated' if company.is_active else 'deactivated'} successfully"
        })

    def perform_create(self, serializer):
        """Custom create logic"""
        company = serializer.save()
        return company

    def perform_update(self, serializer):
        """Custom update logic"""
        company = serializer.save()
        return company

    def perform_destroy(self, instance):
        """Custom delete logic"""
        instance.delete()
