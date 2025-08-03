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
from apps.companies.models import Company, Entity
from .utils import reverse_geocode, validate_coordinates, geocode_address

logger = logging.getLogger(__name__)

class SiteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing sites with full CRUD operations
    """
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
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return SiteListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            # Use FrontendSiteSerializer for better frontend compatibility
            return FrontendSiteSerializer
        return SiteSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()

        # Filter by company code if provided
        company_code = self.request.query_params.get('company_code')
        if company_code:
            queryset = queryset.filter(entity__company__company_code=company_code)

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

    @action(detail=True, methods=['get'], url_path='form-configuration')
    def get_form_configuration(self, request, pk=None):
        """Get form configuration for a specific site"""
        site = self.get_object()
        serializer = SiteFormConfigurationSerializer(site)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='display-configuration')
    def get_display_configuration(self, request, pk=None):
        """Get display configuration for a specific site"""
        site = self.get_object()
        
        # Get or create site configuration
        config, created = SiteConfiguration.objects.get_or_create(site=site)
        
        return Response({
            'site_id': site.id,
            'site_code': site.site_code,
            'site_name': site.name,
            'show_safety_officer': config.show_safety_officer,
            'show_emergency_contacts': config.show_emergency_contacts,
            'show_quick_info': config.show_quick_info,
            'quick_info_config': config.get_quick_info_config(),
            'custom_title': config.custom_title,
            'custom_description': config.custom_description
        })

    @action(detail=True, methods=['post'], url_path='update-display-configuration')
    def update_display_configuration(self, request, pk=None):
        """Update display configuration for a specific site"""
        site = self.get_object()
        config, created = SiteConfiguration.objects.get_or_create(site=site)
        
        # Update display settings
        if 'show_safety_officer' in request.data:
            config.show_safety_officer = request.data['show_safety_officer']
        if 'show_emergency_contacts' in request.data:
            config.show_emergency_contacts = request.data['show_emergency_contacts']
        if 'show_quick_info' in request.data:
            config.show_quick_info = request.data['show_quick_info']
        if 'quick_info_config' in request.data:
            config.quick_info_config = request.data['quick_info_config']
        if 'custom_title' in request.data:
            config.custom_title = request.data['custom_title']
        if 'custom_description' in request.data:
            config.custom_description = request.data['custom_description']
        
        config.save()
        
        return Response({
            'message': 'Display configuration updated successfully',
            'show_safety_officer': config.show_safety_officer,
            'show_emergency_contacts': config.show_emergency_contacts,
            'show_quick_info': config.show_quick_info,
            'quick_info_config': config.get_quick_info_config(),
            'custom_title': config.custom_title,
            'custom_description': config.custom_description
        })

    @action(detail=True, methods=['get'], url_path='menu-configuration')
    def get_menu_configuration(self, request, pk=None):
        """Get complete menu configuration including forms and display settings"""
        site = self.get_object()
        config, created = SiteConfiguration.objects.get_or_create(site=site)
        
        return Response({
            'site_id': site.id,
            'site_code': site.site_code,
            'site_name': site.name,
            'enabled_forms': site.get_enabled_forms(),
            'form_configuration': site.get_form_configuration(),
            'all_available_forms': [choice[0] for choice in site.FORM_TYPES],
            'display_config': {
                'show_safety_officer': config.show_safety_officer,
                'show_emergency_contacts': config.show_emergency_contacts,
                'show_quick_info': config.show_quick_info,
                'quick_info_config': config.get_quick_info_config(),
                'custom_title': config.custom_title,
                'custom_description': config.custom_description
            }
        })

    @action(detail=True, methods=['post'], url_path='update-form-configuration')
    def update_form_configuration(self, request, pk=None):
        """Update form configuration for a specific site"""
        site = self.get_object()
        enabled_forms = request.data.get('enabled_forms', [])
        
        # Validate form types
        valid_forms = [choice[0] for choice in site.FORM_TYPES]
        for form_type in enabled_forms:
            if form_type not in valid_forms:
                return Response({
                    'error': f'Invalid form type: {form_type}',
                    'valid_forms': valid_forms
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update enabled forms
        site.enabled_forms = enabled_forms
        site.save()
        
        return Response({
            'message': 'Form configuration updated successfully',
            'enabled_forms': site.get_enabled_forms(),
            'form_configuration': site.get_form_configuration()
        })

    @action(detail=True, methods=['post'], url_path='enable-form')
    def enable_form(self, request, pk=None):
        """Enable a specific form type for a site"""
        site = self.get_object()
        form_type = request.data.get('form_type')
        
        if not form_type:
            return Response({
                'error': 'form_type is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            site.enable_form(form_type)
            return Response({
                'message': f'Form {form_type} enabled successfully',
                'enabled_forms': site.get_enabled_forms()
            })
        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='disable-form')
    def disable_form(self, request, pk=None):
        """Disable a specific form type for a site"""
        site = self.get_object()
        form_type = request.data.get('form_type')
        
        if not form_type:
            return Response({
                'error': 'form_type is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            site.disable_form(form_type)
            return Response({
                'message': f'Form {form_type} disabled successfully',
                'enabled_forms': site.get_enabled_forms()
            })
        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='bulk-qr')
    def bulk_qr_generation(self, request):
        """Generate QR codes for multiple sites"""
        site_ids = request.query_params.get('site_ids', '').split(',')
        if not site_ids or site_ids[0] == '':
            return Response({
                'error': 'site_ids parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        sites = Site.objects.filter(id__in=site_ids)
        qr_data = []
        
        for site in sites:
            site_qr_data = site.generate_qr_data()
            qr_data.append({
                'id': site.id,
                'name': site.name,
                'site_code': site.site_code,
                'company_name': site.entity.company.name,
                'qr_code_image': site_qr_data['qr_code'],
                'site_data': site_qr_data['site_data']
            })
        
        return Response(qr_data)

    @action(detail=False, methods=['get'], url_path='available-companies')
    def available_companies(self, request):
        """Get list of available companies for site creation"""
        companies = Company.objects.filter(is_active=True).values('id', 'name', 'company_code')
        return Response({
            'companies': list(companies)
        })

    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """Get dashboard statistics for sites"""
        company_id = request.query_params.get('company')
        queryset = self.get_queryset()

        if company_id:
            queryset = queryset.filter(entity__company_id=company_id)

        stats = {
            'total_sites': queryset.count(),
            'active_sites': queryset.filter(is_active=True).count(),
            'operational_sites': queryset.filter(
                is_active=True,
                operational_status='OPERATIONAL'
            ).count(),
            'by_status': dict(
                queryset.values_list('operational_status')
                .annotate(count=Count('id'))
                .order_by('operational_status')
            ),
            'by_plant_type': dict(
                queryset.filter(plant_type__isnull=False)
                .exclude(plant_type='')
                .values_list('plant_type')
                .annotate(count=Count('id'))
                .order_by('plant_type')
            ),
            'by_state': dict(
                queryset.values_list('state')
                .annotate(count=Count('id'))
                .order_by('state')[:10]  # Top 10 states
            )
        }

        return Response(stats)

    @action(detail=True, methods=['post'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        """Toggle site active status"""
        site = self.get_object()
        site.is_active = not site.is_active
        site.save()

        return Response({
            'message': f"Site {'activated' if site.is_active else 'deactivated'} successfully",
            'is_active': site.is_active
        })

    @action(detail=True, methods=['patch'], url_path='update-status')
    def update_operational_status(self, request, pk=None):
        """Update operational status of site"""
        site = self.get_object()
        new_status = request.data.get('operational_status')

        if new_status not in dict(Site.OPERATIONAL_STATUS_CHOICES):
            return Response(
                {'error': 'Invalid operational status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        site.operational_status = new_status
        site.save()

        return Response({
            'message': 'Operational status updated successfully',
            'operational_status': site.operational_status
        })

    @action(detail=True, methods=['get'], url_path='qr-types')
    def get_qr_types(self, request, pk=None):
        """Get available QR code types for a site"""
        site = self.get_object()
        return Response({
            'site_id': site.id,
            'site_name': site.name,
            'available_qr_types': site.get_available_qr_types(),
            'entity_types': site.get_entity_types()
        })

    @action(detail=True, methods=['get'], url_path='qr-generate')
    def generate_qr_code(self, request, pk=None):
        """Generate QR code with specified type and entity type"""
        site = self.get_object()
        qr_type = request.GET.get('type', 'orm')
        entity_type = request.GET.get('entity_type', 'site')
        
        # Validate QR type
        available_types = [qt['type'] for qt in site.get_available_qr_types()]
        if qr_type not in available_types:
            qr_type = 'orm'
        
        # Validate entity type
        available_entity_types = [et['type'] for et in site.get_entity_types()]
        if entity_type not in available_entity_types:
            entity_type = 'site'
        
        qr_data = site.generate_qr_data(qr_type, entity_type)
        return Response(qr_data)

    @action(detail=True, methods=['post'], url_path='bulk-qr-generate')
    def bulk_qr_generation(self, request, pk=None):
        """Generate multiple QR codes with different types and entity types"""
        site = self.get_object()
        qr_types = request.data.get('qr_types', ['orm'])
        entity_type = request.data.get('entity_type', 'site')
        
        # Validate entity type
        available_entity_types = [et['type'] for et in site.get_entity_types()]
        if entity_type not in available_entity_types:
            entity_type = 'site'
        
        results = []
        for qr_type in qr_types:
            qr_data = site.generate_qr_data(qr_type, entity_type)
            results.append({
                'qr_type': qr_type,
                'entity_type': entity_type,
                'qr_code': qr_data['qr_code'],
                'site_data': qr_data['site_data']
            })
        
        return Response({
            'site_id': site.id,
            'site_name': site.name,
            'entity_type': entity_type,
            'generated_qr_codes': results
        })

    @action(detail=False, methods=['get'], url_path='headquarters-qr')
    def generate_headquarters_qr(self, request):
        """Generate headquarters QR code without requiring a specific site"""
        # Create a dummy site for headquarters QR
        from apps.companies.models import Company
        try:
            company = Company.objects.first()
            if not company:
                return Response({'error': 'No company found'}, status=400)
            
            # Get parameters from request
            qr_type = request.GET.get('type', 'orm')
            entity_type = request.GET.get('entity_type', 'headquarters')
            enabled_forms = request.GET.getlist('enabled_forms', ['UNSAFE_ACT', 'UNSAFE_CONDITION', 'NEAR_MISS', 'FEEDBACK'])
            
            # Get headquarters details from request
            headquarters_details = request.GET.get('headquarters_details')
            if headquarters_details:
                try:
                    import json
                    hq_details = json.loads(headquarters_details)
                except:
                    hq_details = None
            else:
                hq_details = None
            
            # Create a temporary site object for headquarters
            class HeadquartersSite:
                def __init__(self, company, hq_details=None):
                    self.company = company
                    self.site_code = "HEXA_HQ"
                    
                    # Use provided details or defaults
                    if hq_details:
                        self.name = hq_details.get('name', 'Hexa Climate')
                        self.address = hq_details.get('address', 'Sector 49, Gurugram')
                        self.city = hq_details.get('city', 'Gurugram')
                        self.state = hq_details.get('state', 'Haryana')
                        self.country = "India"
                        self.postal_code = hq_details.get('postal_code', '122001')
                        self.phone = hq_details.get('phone', '')
                        self.email = hq_details.get('email', '')
                        self.description = hq_details.get('description', 'Hexa Climate Headquarters')
                    else:
                        # Default values
                        self.name = "Hexa Climate"
                        self.address = "Sector 49, Gurugram"
                        self.city = "Gurugram"
                        self.state = "Haryana"
                        self.country = "India"
                        self.postal_code = "122001"
                        self.phone = ""
                        self.email = ""
                        self.description = "Hexa Climate Headquarters"
                    
                    # Default coordinates for Gurugram
                    self.latitude = 28.4595
                    self.longitude = 77.0266
                    
                def get_enabled_forms(self):
                    return enabled_forms
                
                def get_available_qr_types(self):
                    return [
                        {
                            'type': 'orm',
                            'name': 'ORM',
                            'description': 'Operational Risk Management QR code',
                            'color': 'Black on White'
                        },
                        {
                            'type': 'headquarters',
                            'name': 'Headquarters',
                            'description': 'Hexa Climate Headquarters QR code',
                            'color': 'Black on White'
                        },
                        {
                            'type': 'construction',
                            'name': 'Construction',
                            'description': 'Construction site QR code',
                            'color': 'Black on White'
                        }
                    ]
                
                def get_entity_types(self):
                    return [
                        {
                            'type': 'headquarters',
                            'name': 'Headquarters',
                            'description': 'QR code for Hexa Climate headquarters',
                            'icon': '🏛️'
                        }
                    ]
                
                def generate_qr_data(self, qr_type='orm', entity_type='headquarters'):
                    # Generate headquarters public URL
                    public_url = f"http://localhost:3000/public/HEXA001/HEXA_HQ"
                    
                    site_data = {
                        'site_code': self.site_code,
                        'site_name': self.name,
                        'company_name': self.company.name,
                        'address': f"{self.address}, {self.city}, {self.state}, {self.country} - {self.postal_code}",
                        'latitude': float(self.latitude),
                        'longitude': float(self.longitude),
                        'enabled_forms': self.get_enabled_forms(),
                        'qr_type': qr_type,
                        'entity_type': entity_type,
                        'headquarters_name': self.name,
                        'headquarters_description': self.description,
                        'contact_info': {
                            'email': self.email or 'info@hexaclimate.com',
                            'phone': self.phone or '9660027799',
                            'address': f"{self.address}, {self.city}, {self.state}, {self.country}"
                        },
                        'public_url': public_url,
                        'type': 'headquarters',
                        'description': 'Headquarters QR code for Hexa Climate',
                        'location_type': 'Headquarters'
                    }
                    
                    # Generate QR code with the URL instead of JSON data
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=4,
                    )
                    qr.add_data(public_url)
                    qr.make(fit=True)
                    
                    # Basic black and white QR code
                    img = qr.make_image(fill_color="black", back_color="white")
                    
                    buffer = BytesIO()
                    img.save(buffer, format='PNG')
                    img_str = base64.b64encode(buffer.getvalue()).decode()
                    
                    return {
                        'qr_code': f"data:image/png;base64,{img_str}",
                        'site_data': site_data,
                        'qr_type': qr_type,
                        'entity_type': entity_type
                    }
            
            hq_site = HeadquartersSite(company, hq_details)
            qr_data = hq_site.generate_qr_data(qr_type, entity_type)
            
            return Response(qr_data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @action(detail=True, methods=['get'], url_path='fun-stats')
    def get_fun_stats(self, request, pk=None):
        """Get fun statistics for the admin dashboard"""
        site = self.get_object()
        total_incidents = site.incidents.count()
        recent_incidents = site.incidents.filter(created_at__gte=timezone.now() - timedelta(days=30)).count()
        
        # Calculate safety score
        safety_score = max(0, 100 - (recent_incidents * 10))
        
        # Professional messages
        fun_messages = {
            'safety_emoji': '🛡️',
            'safety_message': f'Safety Score: {safety_score}% - {total_incidents} total incidents',
            'plant_emoji': '⚡',
            'plant_fun_fact': f'Power Plant Status: Operational',
            'daily_joke': 'Safety is our priority - every incident reported helps us improve.'
        }
        
        power_levels = {
            'current_power': '30MWp',
            'fun_power': 'Safety First'
        }
        
        return Response({
            'site_id': site.id,
            'site_name': site.name,
            'stats': {
                'total_incidents': total_incidents,
                'recent_incidents': recent_incidents,
                'safety_score': safety_score
            },
            'fun_messages': fun_messages,
            'power_levels': power_levels
        })

    def perform_create(self, serializer):
        """Custom create logic"""
        logger.info(f"Creating new site: {serializer.validated_data.get('name')}")
        serializer.save()

    def perform_update(self, serializer):
        """Custom update logic"""
        logger.info(f"Updating site: {serializer.instance.name}")
        serializer.save()

    def perform_destroy(self, instance):
        """Soft delete by setting is_active to False"""
        logger.info(f"Soft deleting site: {instance.name}")
        instance.is_active = False
        instance.save()

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

@method_decorator(csrf_exempt, name='dispatch')
class PublicSiteAccessView(viewsets.ReadOnlyModelViewSet):
    """
    Public access view for QR code scanning
    No authentication required
    """
    serializer_class = PublicSiteSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Site.objects.select_related('entity__company').filter(is_active=True)

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
                    'phone': '',
                    'email': '',
                    'description': 'Hexa Climate Headquarters'
                }
                
                # Create headquarters site data
                headquarters_site_data = {
                    'id': None,
                    'name': f"{headquarters_details['name']} Headquarters",
                    'site_code': 'HEXA_HQ',
                    'company_name': headquarters_details['name'],
                    'address': headquarters_details['address'],
                    'city': headquarters_details['city'],
                    'state': headquarters_details['state'],
                    'country': 'India',
                    'postal_code': headquarters_details['postal_code'],
                    'phone': headquarters_details['phone'],
                    'email': headquarters_details['email'],
                    'operational_status': 'OPERATIONAL',
                    'enabled_forms': ['UNSAFE_ACT', 'UNSAFE_CONDITION', 'NEAR_MISS', 'FEEDBACK'],
                    'is_operational': True,
                    'is_headquarters': True
                }
                
                return Response({
                    'success': True,
                    'site': headquarters_site_data,
                    'access_time': timezone.now().isoformat()
                })

            # Find company first
            company = get_object_or_404(
                Company,
                company_code=company_code.upper(),
                is_active=True
            )

            # Find site within company
            site = Site.objects.filter(
                entity__company=company,
                site_code=site_code.upper(),
                is_active=True
            ).first()
            
            if not site:
                return Response(
                    {'error': 'Site not found or inactive'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check if site is accessible
            if not site.is_operational():
                return Response({
                    'error': 'Site is currently not operational',
                    'operational_status': site.operational_status
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            serializer = self.get_serializer(site)

            return Response({
                'success': True,
                'site': serializer.data,
                'access_time': site.updated_at.isoformat() if site.updated_at else None
            })

        except Company.DoesNotExist:
            return Response(
                {'error': 'Company not found or inactive'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Site.DoesNotExist:
            return Response(
                {'error': 'Site not found or inactive'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Internal server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Function-based view for public site access
@csrf_exempt
def validate_site_qr(request, company_code, site_code):
    """
    Public site access endpoint for QR codes
    Returns full site data for public interface
    """
    if request.method == 'GET':
        try:
            # Handle headquarters specially
            if site_code.upper() == 'HEXA_HQ':
                headquarters_details = {
                    'name': 'Hexa Climate',
                    'address': 'Sector 49, Gurugram',
                    'city': 'Gurugram',
                    'state': 'Haryana',
                    'postal_code': '122001',
                    'phone': '',
                    'email': '',
                    'description': 'Hexa Climate Headquarters'
                }
                
                site_data = {
                    'id': None,
                    'name': f"{headquarters_details['name']} Headquarters",
                    'site_code': 'HEXA_HQ',
                    'company_name': headquarters_details['name'],
                    'entity_name': 'Headquarters',
                    'address': headquarters_details['address'],
                    'city': headquarters_details['city'],
                    'state': headquarters_details['state'],
                    'country': 'India',
                    'postal_code': headquarters_details['postal_code'],
                    'phone': headquarters_details['phone'],
                    'email': headquarters_details['email'],
                    'operational_status': 'OPERATIONAL',
                    'enabled_forms': ['UNSAFE_ACT', 'UNSAFE_CONDITION', 'NEAR_MISS', 'FEEDBACK'],
                    'is_operational': True,
                    'is_headquarters': True
                }
                
                return JsonResponse({
                    'success': True,
                    'site': site_data,
                    'access_time': timezone.now().isoformat()
                })

            # Find company first
            company = get_object_or_404(
                Company,
                company_code=company_code.upper(),
                is_active=True
            )

            # Find site within company
            site = Site.objects.filter(
                entity__company=company,
                site_code=site_code.upper(),
                is_active=True
            ).first()
            
            if not site:
                return JsonResponse(
                    {'error': 'Site not found or inactive'},
                    status=404
                )

            # Prepare site data
            site_data = {
                'id': site.id,
                'name': site.name,
                'site_code': site.site_code,
                'company_name': site.entity.company.name,
                'entity_name': site.entity.name,
                'address': site.address,  # Just the street address, not full_address
                'city': site.city,
                'state': site.state,
                'country': site.country,
                'phone': site.phone,
                'email': site.email,
                'operational_status': site.operational_status,
                'enabled_forms': site.get_enabled_forms(),
                'is_operational': site.is_operational(),
                'is_headquarters': False
            }

            return JsonResponse({
                'success': True,
                'site': site_data,
                'access_time': site.updated_at.isoformat() if site.updated_at else None
            })

        except Company.DoesNotExist:
            return JsonResponse(
                {'error': 'Company not found or inactive'},
                status=404
            )
        except Exception as e:
            return JsonResponse(
                {'error': f'Internal server error: {str(e)}'},
                status=500
            )

    return JsonResponse({'error': 'Method not allowed'}, status=405)


# Function-based view for public entity access
@csrf_exempt
def validate_entity_qr(request, company_code, entity_code):
    """
    Public entity access endpoint for QR codes
    Returns full entity data for public interface
    """
    if request.method == 'GET':
        try:
            # Find company first
            company = get_object_or_404(
                Company,
                company_code=company_code.upper(),
                is_active=True
            )

            # Find entity within company
            entity = get_object_or_404(
                Entity,
                company=company,
                entity_code=entity_code.upper(),
                is_active=True
            )

            # Prepare entity data
            entity_data = {
                'id': entity.id,
                'name': entity.name,
                'entity_code': entity.entity_code,
                'company_name': entity.company.name,
                'address': entity.address,
                'city': entity.city,
                'state': entity.state,
                'country': entity.country,
                'phone': entity.phone,
                'email': entity.email,
                'description': entity.description,
                'enabled_forms': ['UNSAFE_ACT', 'UNSAFE_CONDITION', 'NEAR_MISS', 'FEEDBACK'],
                'is_operational': True,
                'is_entity': True
            }

            return JsonResponse({
                'success': True,
                'entity': entity_data,
                'access_time': entity.updated_at.isoformat() if entity.updated_at else None
            })

        except Company.DoesNotExist:
            return JsonResponse(
                {'error': 'Company not found or inactive'},
                status=404
            )
        except Entity.DoesNotExist:
            return JsonResponse(
                {'error': 'Entity not found or inactive'},
                status=404
            )
        except Exception as e:
            return JsonResponse(
                {'error': f'Internal server error: {str(e)}'},
                status=500
            )

    return JsonResponse({'error': 'Method not allowed'}, status=405)
