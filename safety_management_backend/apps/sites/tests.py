from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
import json

from .models import Site
from apps.companies.models import Company

class SiteModelTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            company_code="TEST001",
            address="Test Address",
            city="Test City",
            state="Test State",
            country="India",
            postal_code="123456",
            phone="1234567890",
            email="test@company.com"
        )

        self.site = Site.objects.create(
            company=self.company,
            name="Test Site",
            site_code="TS001",
            address="Site Address",
            city="Site City",
            state="Site State",
            postal_code="654321",
            latitude=Decimal('23.0225'),
            longitude=Decimal('72.5714'),
            phone="9876543210",
            email="site@test.com",
            plant_type="SOLAR",
            capacity="100 MW"
        )

    def test_site_creation(self):
        """Test site model creation"""
        self.assertEqual(self.site.name, "Test Site")
        self.assertEqual(self.site.site_code, "TS001")
        self.assertEqual(self.site.company, self.company)
        self.assertTrue(self.site.is_active)

    def test_qr_data_generation(self):
        """Test QR data generation"""
        qr_data = self.site.generate_qr_data()
        self.assertEqual(qr_data['site_code'], 'TS001')
        self.assertEqual(qr_data['company_code'], 'TEST001')
        self.assertIn('latitude', qr_data)
        self.assertIn('longitude', qr_data)

    def test_qr_code_generation(self):
        """Test QR code image generation"""
        qr_code = self.site.generate_qr_code()
        self.assertTrue(qr_code.startswith('data:image/png;base64,'))

    def test_coordinates_method(self):
        """Test get_coordinates method"""
        coords = self.site.get_coordinates()
        self.assertEqual(coords, (23.0225, 72.5714))

    def test_is_operational_method(self):
        """Test is_operational method"""
        self.assertTrue(self.site.is_operational())

        self.site.operational_status = 'MAINTENANCE'
        self.site.save()
        self.assertFalse(self.site.is_operational())

class SiteAPITest(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="API Test Company",
            company_code="API001",
            address="API Address",
            city="API City",
            state="API State",
            country="India",
            postal_code="123456",
            phone="1234567890",
            email="api@company.com"
        )

        self.site_data = {
            'company': self.company.id,
            'name': 'API Test Site',
            'site_code': 'ATS001',
            'address': 'API Site Address',
            'city': 'API Site City',
            'state': 'API Site State',
            'postal_code': '654321',
            'latitude': '23.0225',
            'longitude': '72.5714',
            'phone': '9876543210',
            'email': 'apisite@test.com',
            'plant_type': 'WIND',
            'capacity': '50 MW'
        }

    def test_create_site(self):
        """Test site creation via API"""
        response = self.client.post('/api/v1/sites/', self.site_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Site.objects.count(), 1)

    def test_list_sites(self):
        """Test sites listing"""
        Site.objects.create(**self.site_data)
        response = self.client.get('/api/v1/sites/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_site_detail(self):
        """Test site detail retrieval"""
        site = Site.objects.create(**self.site_data)
        response = self.client.get(f'/api/v1/sites/{site.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'API Test Site')

    def test_qr_generation_endpoint(self):
        """Test QR code generation endpoint"""
        site = Site.objects.create(**self.site_data)
        response = self.client.get(f'/api/v1/sites/{site.id}/qr/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('qr_code_image', response.data)

    def test_public_site_access(self):
        """Test public site access endpoint"""
        site = Site.objects.create(**self.site_data)
        response = self.client.get(
            f'/api/v1/public/{self.company.company_code}/{site.site_code}/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_invalid_public_access(self):
        """Test invalid public site access"""
        response = self.client.get('/api/v1/public/INVALID/INVALID/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_site_filtering(self):
        """Test site filtering"""
        Site.objects.create(**self.site_data)

        # Test company filter
        response = self.client.get(f'/api/v1/sites/?company={self.company.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        # Test active only filter
        response = self.client.get('/api/v1/sites/?active_only=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint"""
        Site.objects.create(**self.site_data)
        response = self.client.get('/api/v1/sites/dashboard-stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_sites', response.data)
        self.assertEqual(response.data['total_sites'], 1)
