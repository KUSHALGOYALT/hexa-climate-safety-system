from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmergencyContactViewSet, NationalEmergencyContactViewSet

router = DefaultRouter()
router.register(r'emergency-contacts', EmergencyContactViewSet)
router.register(r'national-contacts', NationalEmergencyContactViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
