from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth.models import User

class DashboardViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = None

    @action(detail=False, methods=['get'])
    def stats(self, request):
        return Response({'message': 'Dashboard stats endpoint'})
