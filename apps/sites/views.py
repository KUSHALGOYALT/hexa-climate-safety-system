from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from .models import Site
from .serializers import (
    SiteSerializer, SiteListSerializer, SiteQRSerializer, PublicSiteSerializer
)

class SiteViewSet(viewsets.ModelViewSet):
    """ViewSet for managing sites"""
    queryset = Site.objects.select_related('entity__company').all()
    serializer_class = SiteSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'entity', 'operational_status', 'is_active',
        'plant_type', 'state', 'country'
    ]
    search_fields = ['name', 'site_code', 'city', 'state', 'address']
    ordering_fields = ['name', 'created_at', 'site_code', 'operational_status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return SiteListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return SiteSerializer
        return SiteSerializer

    @action(detail=True, methods=['get'], url_path='qr')
    def generate_qr(self, request, pk=None):
        """Generate QR code for specific site"""
        site = self.get_object()
        serializer = SiteQRSerializer(site)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='qr-url')
    def generate_url_qr(self, request, pk=None):
        """Generate URL-based QR code for specific site"""
        site = self.get_object()
        qr_data = site.generate_qr_data()
        return Response({
            'id': site.id,
            'name': site.name,
            'site_code': site.site_code,
            'company_name': site.entity.company.name,
            'company_code': site.entity.company.company_code,
            'qr_code': qr_data['qr_code'],
            'site_data': qr_data['site_data'],
            'public_url': f"http://localhost:3000/public/{site.entity.company.company_code}/{site.site_code}"
        })

    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """Get dashboard statistics for sites"""
        total_sites = Site.objects.filter(is_active=True).count()
        operational_sites = Site.objects.filter(
            is_active=True, operational_status='OPERATIONAL'
        ).count()
        maintenance_sites = Site.objects.filter(
            is_active=True, operational_status='MAINTENANCE'
        ).count()
        
        return Response({
            'total_sites': total_sites,
            'operational_sites': operational_sites,
            'maintenance_sites': maintenance_sites,
        })

@method_decorator(csrf_exempt, name='dispatch')
class PublicSiteAccessView(viewsets.ReadOnlyModelViewSet):
    """Public access view for QR code scanning"""
    serializer_class = PublicSiteSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Site.objects.select_related('entity__company').filter(is_active=True)

    @action(detail=False, methods=['get'], url_path='public/(?P<company_code>[^/.]+)/(?P<site_code>[^/.]+)')
    def get_by_codes(self, request, company_code=None, site_code=None):
        """Get site by company code and site code"""
        try:
            site = Site.objects.filter(
                entity__company__company_code=company_code,
                site_code=site_code,
                is_active=True
            ).select_related('entity__company').first()
            
            if not site:
                return Response({
                    'error': 'Site not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = PublicSiteSerializer(site)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({
                'error': 'An error occurred while fetching site data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
def validate_site_qr(request, company_code, site_code):
    """Validate site QR code and return site data"""
    try:
        site = Site.objects.filter(
            entity__company__company_code=company_code,
            site_code=site_code,
            is_active=True
        ).select_related('entity__company').first()
        
        if not site:
            return JsonResponse({
                'error': 'Site not found'
            }, status=404)
        
        site_data = {
            'id': site.id,
            'name': site.name,
            'site_code': site.site_code,
            'entity_name': site.entity.name,
            'company_name': site.entity.company.name,
            'company_code': site.entity.company.company_code,
            'plant_type': site.plant_type,
            'operational_status': site.operational_status,
            'address': site.address,
            'city': site.city,
            'state': site.state,
            'country': site.country,
            'phone': site.phone,
            'email': site.email,
            'latitude': float(site.latitude) if site.latitude else None,
            'longitude': float(site.longitude) if site.longitude else None,
        }
        
        return JsonResponse({
            'success': True,
            'site_data': site_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': 'An error occurred while validating site QR'
        }, status=500) 