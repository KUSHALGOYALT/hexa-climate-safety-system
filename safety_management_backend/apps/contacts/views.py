from rest_framework import viewsets
from .models import EmergencyContact, NationalEmergencyContact
from .serializers import EmergencyContactSerializer, NationalEmergencyContactSerializer

class EmergencyContactViewSet(viewsets.ModelViewSet):
    queryset = EmergencyContact.objects.all()
    serializer_class = EmergencyContactSerializer

class NationalEmergencyContactViewSet(viewsets.ModelViewSet):
    queryset = NationalEmergencyContact.objects.all()
    serializer_class = NationalEmergencyContactSerializer
