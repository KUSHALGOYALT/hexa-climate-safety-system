from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, timedelta
from django.utils import timezone

from .models import Employee, EmployeeTraining, EmployeeAccess
from apps.sites.models import Site
from apps.companies.models import Company

class EmployeeModelTest(TestCase):
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
            latitude=23.0225,
            longitude=72.5714,
            phone="9876543210",
            email="site@test.com"
        )

    def test_employee_creation(self):
        """Test employee model creation"""
        employee = Employee.objects.create(
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
            phone="+919876543210",
            designation="Safety Officer",
            department="Safety",
            employee_type="SAFETY_OFFICER",
            primary_site=self.site
        )

        self.assertEqual(employee.display_name, "John Doe")
        self.assertEqual(employee.full_name, "John Doe")
        self.assertTrue(employee.is_safety_personnel)
        self.assertFalse(employee.is_manager)

    def test_employee_id_generation(self):
        """Test automatic employee ID generation"""
        employee = Employee.objects.create(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@test.com",
            phone="+919876543211",
            designation="Plant Manager",
            department="Operations",
            employee_type="PLANT_MANAGER",
            primary_site=self.site
        )

        self.assertTrue(employee.employee_id.startswith("TS001-PLA"))

    def test_years_of_service(self):
        """Test years of service calculation"""
        employee = Employee.objects.create(
            first_name="Bob",
            last_name="Wilson",
            email="bob.wilson@test.com",
            phone="+919876543212",
            designation="Operator",
            department="Operations",
            date_of_joining=date.today() - timedelta(days=365)
        )

        self.assertAlmostEqual(employee.years_of_service, 1.0, places=1)

    def test_safety_training_status(self):
        """Test safety training status calculation"""
        employee = Employee.objects.create(
            first_name="Alice",
            last_name="Brown",
            email="alice.brown@test.com",
            phone="+919876543213",
            designation="Technician",
            department="Maintenance",
            safety_training_completed=True,
            safety_training_expiry=date.today() + timedelta(days=15)
        )

        self.assertEqual(employee.safety_training_status, 'EXPIRING_SOON')

class EmployeeAPITest(APITestCase):
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

        self.site = Site.objects.create(
            company=self.company,
            name="API Test Site",
            site_code="ATS001",
            address="API Site Address",
            city="API Site City",
            state="API Site State",
            postal_code="654321",
            latitude=23.0225,
            longitude=72.5714,
            phone="9876543210",
            email="apisite@test.com"
        )

        self.employee_data = {
            'first_name': 'Test',
            'last_name': 'Employee',
            'email': 'test.employee@api.com',
            'phone': '+919876543214',
            'designation': 'Test Designation',
            'department': 'Test Department',
            'employee_type': 'OPERATOR',
            'primary_site': self.site.id
        }

    def test_create_employee(self):
        """Test employee creation via API"""
        response = self.client.post('/api/v1/employees/', self.employee_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Employee.objects.count(), 1)

    def test_list_employees(self):
        """Test employee listing"""
        Employee.objects.create(**self.employee_data)
        response = self.client.get('/api/v1/employees/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_employee_detail(self):
        """Test employee detail retrieval"""
        employee = Employee.objects.create(**self.employee_data)
        response = self.client.get(f'/api/v1/employees/{employee.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['display_name'], 'Test Employee')

    def test_dashboard_stats(self):
        """Test employee dashboard statistics"""
        Employee.objects.create(**self.employee_data)
        response = self.client.get('/api/v1/employees/dashboard-stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_employees', response.data)
        self.assertEqual(response.data['total_employees'], 1)

    def test_employee_filtering(self):
        """Test employee filtering"""
        Employee.objects.create(**self.employee_data)

        # Test site filter
        response = self.client.get(f'/api/v1/employees/?site={self.site.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        # Test active only filter
        response = self.client.get('/api/v1/employees/?active_only=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class EmployeeTrainingTest(TestCase):
    def setUp(self):
        self.employee = Employee.objects.create(
            first_name="Training",
            last_name="Test",
            email="training.test@test.com",
            phone="+919876543215",
            designation="Test",
            department="Test"
        )

    def test_training_creation(self):
        """Test training record creation"""
        training = EmployeeTraining.objects.create(
            employee=self.employee,
            training_type="SAFETY_INDUCTION",
            training_name="Basic Safety Training",
            status="COMPLETED",
            completion_date=date.today(),
            expiry_date=date.today() + timedelta(days=365)
        )

        self.assertEqual(str(training), "Training Test - Basic Safety Training")
        self.assertFalse(training.is_expired)
        self.assertGreater(training.days_to_expiry, 300)
