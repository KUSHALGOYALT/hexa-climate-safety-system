from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, EmployeeLocationViewSet

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet)
router.register(r'employee-locations', EmployeeLocationViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 