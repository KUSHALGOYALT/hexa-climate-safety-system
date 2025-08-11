from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging
from datetime import timedelta
from django.utils import timezone
import json
import qrcode
from io import BytesIO
import base64

from .models import Site, SiteConfiguration
from .serializers import (
    SiteSerializer,
    SiteListSerializer,
    SiteQRSerializer,
    PublicSiteSerializer,
    SiteCreateUpdateSerializer,
    FrontendSiteSerializer,
    SiteFormConfigurationSerializer
)
from apps.companies.models import Company
from .utils import reverse_geocode, validate_coordinates, geocode_address

logger = logging.getLogger(__name__)

class SiteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing sites with full CRUD operations
    """
    queryset = Site.objects.select_related('company').all()
    serializer_class = SiteSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'company', 'operational_status', 'is_active',
        'plant_type', 'state', 'country'
    ]
    search_fields = ['name', 'site_code', 'city', 'state', 'address']
    ordering_fields = ['name', 'created_at', 'site_code', 'operational_status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return SiteListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return FrontendSiteSerializer
        return SiteSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()

        # Filter by company code if provided
        company_code = self.request.query_params.get('company_code')
        if company_code:
            queryset = queryset.filter(company__company_code=company_code)

        # Filter by active sites only if specified
        active_only = self.request.query_params.get('active_only')
        if active_only and active_only.lower() == 'true':
            queryset = queryset.filter(is_active=True)

        # Filter by operational sites only
        operational_only = self.request.query_params.get('operational_only')
        if operational_only and operational_only.lower() == 'true':
            queryset = queryset.filter(
                is_active=True,
                operational_status='OPERATIONAL'
            )

        return queryset

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
        qr_data = site.generate_qr_data(qr_type='url')
        return Response({
            'id': site.id,
            'name': site.name,
            'site_code': site.site_code,
            'company_name': site.company.name,
            'company_code': site.company.company_code,
            'qr_code': qr_data['qr_code'],
            'qr_code_image': qr_data['qr_code_image'],
            'url': qr_data['url']
        })

    @action(detail=False, methods=['get'], url_path='available-companies')
    def available_companies(self, request):
        """Get companies available for site creation"""
        companies = Company.objects.filter(is_active=True)
        return Response([{
            'id': company.id,
            'name': company.name,
            'company_code': company.company_code,
            'company_type': company.company_type
        } for company in companies])

    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """Get dashboard statistics for sites"""
        total_sites = Site.objects.count()
        active_sites = Site.objects.filter(is_active=True).count()
        operational_sites = Site.objects.filter(
            is_active=True, 
            operational_status='OPERATIONAL'
        ).count()
        
        # Recent activity
        last_30_days = timezone.now() - timedelta(days=30)
        recent_sites = Site.objects.filter(created_at__gte=last_30_days).count()
        
        # Plant type distribution
        plant_distribution = Site.objects.values('plant_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # State distribution
        state_distribution = Site.objects.values('state').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        stats = {
            'total_sites': total_sites,
            'active_sites': active_sites,
            'operational_sites': operational_sites,
            'recent_sites': recent_sites,
            'plant_distribution': list(plant_distribution),
            'state_distribution': list(state_distribution)
        }
        
        return Response(stats)

    @action(detail=True, methods=['post'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        """Toggle site active status"""
        site = self.get_object()
        site.is_active = not site.is_active
        site.save()
        
        return Response({
            'id': site.id,
            'is_active': site.is_active,
            'message': f"Site {'activated' if site.is_active else 'deactivated'} successfully"
        })

    @action(detail=True, methods=['patch'], url_path='update-status')
    def update_operational_status(self, request, pk=None):
        """Update site operational status"""
        site = self.get_object()
        new_status = request.data.get('operational_status')
        
        if new_status not in dict(Site.OPERATIONAL_STATUS):
            return Response(
                {'error': 'Invalid operational status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        site.operational_status = new_status
        site.save()
        
        return Response({
            'id': site.id,
            'operational_status': site.operational_status,
            'message': f"Site status updated to {new_status}"
        })

    @action(detail=False, methods=['post'], url_path='reverse-geocode')
    def reverse_geocode_coordinates(self, request):
        """Reverse geocode coordinates to get address information"""
        try:
            latitude = request.data.get('latitude')
            longitude = request.data.get('longitude')
            
            if not latitude or not longitude:
                return Response(
                    {'error': 'Latitude and longitude are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate coordinates
            is_valid, error_message = validate_coordinates(latitude, longitude)
            if not is_valid:
                return Response(
                    {'error': error_message},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Reverse geocode
            address_data = reverse_geocode(float(latitude), float(longitude))
            
            if not address_data:
                return Response(
                    {'error': 'Unable to get address information for these coordinates'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'success': True,
                'address_data': address_data
            })
            
        except Exception as e:
            logger.error(f"Reverse geocoding error: {e}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='geocode')
    def geocode_address_endpoint(self, request):
        """Geocode address to get coordinates"""
        try:
            address = request.data.get('address')
            
            if not address:
                return Response(
                    {'error': 'Address is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Geocode the address
            coordinates = geocode_address(address)
            
            if not coordinates:
                return Response(
                    {'error': 'Unable to get coordinates for this address'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'success': True,
                'coordinates': coordinates
            })
            
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_create(self, serializer):
        """Custom create logic"""
        site = serializer.save()
        return site

    def perform_update(self, serializer):
        """Custom update logic"""
        site = serializer.save()
        return site

    def perform_destroy(self, instance):
        """Custom delete logic"""
        instance.delete()

@method_decorator(csrf_exempt, name='dispatch')
class PublicSiteAccessView(viewsets.ReadOnlyModelViewSet):
    """
    Public access view for QR code scanning
    No authentication required
    """
    serializer_class = PublicSiteSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Site.objects.select_related('company').filter(is_active=True)

    @action(detail=False, methods=['get'], url_path='public/(?P<company_code>[^/.]+)/(?P<site_code>[^/.]+)')
    def get_by_codes(self, request, company_code=None, site_code=None):
        """Public access endpoint for QR code scans"""
        try:
            # Handle headquarters specially
            if site_code.upper() == 'HEXA_HQ':
                # Load headquarters details from localStorage or use defaults
                headquarters_details = {
                    'name': 'Hexa Climate',
                    'address': 'Sector 49, Gurugram',
                    'city': 'Gurugram',
                    'state': 'Haryana',
                    'postal_code': '122001',
                    'country': 'India',
                    'phone': '+91-124-1234567',
                    'email': 'info@hexaclimate.com',
                    'enabled_forms': ['UNSAFE_ACT', 'UNSAFE_CONDITION', 'NEAR_MISS']
                }
                
                return Response({
                    'site': {
                        'id': 'hq',
                        'name': headquarters_details['name'],
                        'site_code': 'HEXA_HQ',
                        'company_name': 'Hexa Climate',
                        'company_code': company_code,
                        'address': headquarters_details['address'],
                        'city': headquarters_details['city'],
                        'state': headquarters_details['state'],
                        'country': headquarters_details['country'],
                        'postal_code': headquarters_details['postal_code'],
                        'phone': headquarters_details['phone'],
                        'email': headquarters_details['email'],
                        'operational_status': 'OPERATIONAL',
                        'is_active': True,
                        'enabled_forms': headquarters_details['enabled_forms'],
                        'is_operational': True,
                        'is_headquarters': True
                    }
                })
            
            # Get site by company code and site code
            site = get_object_or_404(
                Site.objects.select_related('company'),
                company__company_code=company_code,
                site_code=site_code,
                is_active=True
            )
            
            serializer = self.get_serializer(site)
            return Response({'site': serializer.data})
            
        except Site.DoesNotExist:
            return Response(
                {'error': 'Site not found or inactive'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Public site access error: {e}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@csrf_exempt
def validate_site_qr(request, company_code, site_code):
    """Validate site QR code and return site information"""
    try:
        # Handle headquarters specially
        if site_code.upper() == 'HEXA_HQ':
            site_data = {
                'id': 'hq',
                'name': 'Hexa Climate',
                'site_code': 'HEXA_HQ',
                'company_name': 'Hexa Climate',
                'company_code': company_code,
                'address': 'Sector 49, Gurugram',
                'city': 'Gurugram',
                'state': 'Haryana',
                'country': 'India',
                'postal_code': '122001',
                'phone': '+91-124-1234567',
                'email': 'info@hexaclimate.com',
                'operational_status': 'OPERATIONAL',
                'is_active': True,
                'enabled_forms': ['UNSAFE_ACT', 'UNSAFE_CONDITION', 'NEAR_MISS'],
                'is_operational': True,
                'is_headquarters': True
            }
            
            return JsonResponse({
                'success': True,
                'site': site_data
            })
        
        # Get site by company code and site code
        site = get_object_or_404(
            Site.objects.select_related('company'),
            company__company_code=company_code,
            site_code=site_code,
            is_active=True
        )
        
        # Prepare site data
        site_data = {
            'id': site.id,
            'name': site.name,
            'site_code': site.site_code,
            'company_name': site.company.name,
            'company_code': site.company.company_code,
            'address': site.address,
            'city': site.city,
            'state': site.state,
            'country': site.country,
            'postal_code': site.postal_code,
            'phone': site.phone,
            'email': site.email,
            'operational_status': site.operational_status,
            'enabled_forms': site.get_enabled_forms(),
            'is_operational': site.is_operational(),
            'is_headquarters': False
        }
        
        return JsonResponse({
            'success': True,
            'site': site_data
        })
        
    except Site.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Site not found or inactive'
        }, status=404)
    except Exception as e:
        logger.error(f"Site QR validation error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)
