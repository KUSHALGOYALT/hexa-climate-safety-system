from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Company, Entity
from .serializers import (
    CompanySerializer, EntitySerializer, EntityListSerializer, EntityQRSerializer
)

class CompanyViewSet(viewsets.ModelViewSet):
    """ViewSet for managing companies"""
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'company_code']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return CompanySerializer
        return CompanySerializer

    @action(detail=True, methods=['get'], url_path='qr')
    def generate_qr(self, request, pk=None):
        """Generate QR code for specific company"""
        company = self.get_object()
        qr_data = company.generate_qr_data()
        return Response({
            'id': company.id,
            'name': company.name,
            'company_code': company.company_code,
            'qr_code': qr_data['qr_code'],
            'company_data': qr_data['company_data'],
            'public_url': f"http://localhost:3000/public/{company.company_code}/headquarters"
        })

class EntityViewSet(viewsets.ModelViewSet):
    """ViewSet for managing entities"""
    queryset = Entity.objects.select_related('company').all()
    serializer_class = EntitySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['entity_type', 'is_active', 'company']
    search_fields = ['name', 'entity_code', 'city', 'state']
    ordering_fields = ['name', 'created_at', 'entity_code']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return EntityListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EntitySerializer
        return EntitySerializer

    @action(detail=True, methods=['get'], url_path='qr')
    def generate_qr(self, request, pk=None):
        """Generate QR code for specific entity"""
        entity = self.get_object()
        serializer = EntityQRSerializer(entity)
        return Response(serializer.data)

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
            'public_url': f"http://localhost:3000/public/{entity.company.company_code}/entity/{entity.entity_code}"
        }) 