from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Company, Entity
from .serializers import (
    CompanySerializer, CompanyListSerializer, CompanyCreateUpdateSerializer,
    EntitySerializer, EntityListSerializer
)

class CompanyViewSet(viewsets.ModelViewSet):
    """ViewSet for managing companies"""
    queryset = Company.objects.all().order_by('-created_at')
    serializer_class = CompanySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['company_type', 'is_active', 'state', 'country']
    search_fields = ['name', 'company_code', 'city', 'state']
    ordering_fields = ['name', 'created_at', 'company_code']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return CompanyListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CompanyCreateUpdateSerializer
        return CompanySerializer

    @action(detail=True, methods=['get'])
    def subsidiaries(self, request, pk=None):
        """Get subsidiaries of a company"""
        company = self.get_object()
        subsidiaries = company.subsidiaries.all()
        serializer = CompanyListSerializer(subsidiaries, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def entities(self, request, pk=None):
        """Get entities of a company"""
        company = self.get_object()
        entities = company.entities.all()
        serializer = EntityListSerializer(entities, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def parent_companies(self, request):
        """Get only parent companies"""
        parent_companies = Company.objects.filter(company_type='PARENT', is_active=True)
        serializer = CompanyListSerializer(parent_companies, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def subsidiaries_list(self, request):
        """Get only subsidiary companies"""
        subsidiaries = Company.objects.filter(company_type='SUBSIDIARY', is_active=True)
        serializer = CompanyListSerializer(subsidiaries, many=True)
        return Response(serializer.data)

class EntityViewSet(viewsets.ModelViewSet):
    """ViewSet for managing entities"""
    queryset = Entity.objects.all().order_by('-created_at')
    serializer_class = EntitySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['entity_type', 'company', 'is_active', 'state', 'country']
    search_fields = ['name', 'entity_code', 'city', 'state']
    ordering_fields = ['name', 'created_at', 'entity_code']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return EntityListSerializer
        return EntitySerializer

    @action(detail=True, methods=['get'])
    def sites(self, request, pk=None):
        """Get sites of an entity"""
        entity = self.get_object()
        sites = entity.sites.all()
        from apps.sites.serializers import SiteListSerializer
        serializer = SiteListSerializer(sites, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        """Get employees of an entity"""
        entity = self.get_object()
        employees = entity.employees.all()
        from apps.employees.serializers import EmployeeSerializer
        serializer = EmployeeSerializer(employees, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_company(self, request):
        """Get entities by company"""
        company_id = request.query_params.get('company_id')
        if company_id:
            entities = Entity.objects.filter(company_id=company_id, is_active=True)
            serializer = EntityListSerializer(entities, many=True)
            return Response(serializer.data)
        return Response({'error': 'company_id parameter is required'}, status=400)

    @action(detail=False, methods=['get'], url_path='by-codes/(?P<company_code>[^/.]+)/(?P<entity_code>[^/.]+)')
    def by_codes(self, request, company_code=None, entity_code=None):
        """Get entity by company code and entity code"""
        try:
            entity = Entity.objects.get(
                company__company_code=company_code,
                entity_code=entity_code,
                is_active=True
            )
            serializer = EntitySerializer(entity)
            return Response(serializer.data)
        except Entity.DoesNotExist:
            return Response({'error': 'Entity not found'}, status=404)

    @action(detail=True, methods=['get'], url_path='qr')
    def generate_qr(self, request, pk=None):
        """Generate QR code for specific entity"""
        entity = self.get_object()
        qr_data = entity.generate_qr_data()
        return Response(qr_data)

    @action(detail=True, methods=['get'], url_path='qr-url')
    def generate_url_qr(self, request, pk=None):
        """Generate URL-based QR code for specific entity"""
        entity = self.get_object()
        qr_data = entity.generate_qr_data()
        return Response({
            'id': entity.id,
            'name': entity.name,
            'entity_code': entity.entity_code,
            'company_name': entity.company.name,
            'company_code': entity.company.company_code,
            'qr_code': qr_data['qr_code'],
            'entity_data': qr_data['entity_data'],
            'public_url': qr_data['public_url']
        })
