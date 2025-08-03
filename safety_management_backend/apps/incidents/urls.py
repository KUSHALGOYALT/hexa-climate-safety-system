from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IncidentViewSet, IncidentResponseViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'incidents', IncidentViewSet, basename='incidents')
router.register(r'incident-responses', IncidentResponseViewSet, basename='incident-responses')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
]

# Additional URL patterns for specific actions
incident_patterns = [
    path(
        'incidents/<int:pk>/responses/',
        IncidentViewSet.as_view({'post': 'add_response'}),
        name='incident-add-response'
    ),
    path(
        'incidents/<int:pk>/status/',
        IncidentViewSet.as_view({'patch': 'update_status'}),
        name='incident-update-status'
    ),
    path(
        'incidents/<int:pk>/assign/',
        IncidentViewSet.as_view({'post': 'assign_incident'}),
        name='incident-assign'
    ),
    path(
        'incidents/anonymous/',
        IncidentViewSet.as_view({'post': 'anonymous'}),
        name='incident-anonymous'
    ),
    path(
        'incidents/dashboard-stats/',
        IncidentViewSet.as_view({'get': 'dashboard_stats'}),
        name='incident-dashboard-stats'
    ),
    path(
        'incidents/trending/',
        IncidentViewSet.as_view({'get': 'trending_analysis'}),
        name='incident-trending'
    ),
    path(
        'incidents/export/',
        IncidentViewSet.as_view({'get': 'export_data'}),
        name='incident-export'
    ),
]

urlpatterns += incident_patterns
