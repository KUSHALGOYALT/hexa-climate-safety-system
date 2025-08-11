from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmergencyContactViewSet

router = DefaultRouter()
router.register(r'emergency-contacts', EmergencyContactViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 