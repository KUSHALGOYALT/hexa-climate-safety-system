from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SiteViewSet, PublicSiteAccessView, validate_site_qr, validate_entity_qr

# Create router and register viewsets
router = DefaultRouter()
router.register(r'sites', SiteViewSet, basename='sites')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),

    # Public access URLs (no authentication required)
    path(
        'public/<str:company_code>/<str:site_code>/',
        validate_site_qr,
        name='public-site-access'
    ),
    
    # Entity public access URLs
    path(
        'public/<str:company_code>/entity/<str:entity_code>/',
        validate_entity_qr,
        name='public-entity-access'
    ),

    # Simple validation endpoint
    path(
        'validate/<str:company_code>/<str:site_code>/',
        validate_site_qr,
        name='validate-site-qr'
    ),
]

# Additional URL patterns for specific actions
site_detail_patterns = [
    path(
        'sites/<int:pk>/qr/',
        SiteViewSet.as_view({'get': 'generate_qr'}),
        name='site-qr-code'
    ),
    path(
        'sites/bulk-qr/',
        SiteViewSet.as_view({'get': 'bulk_qr_generation'}),
        name='sites-bulk-qr'
    ),
    path(
        'sites/dashboard-stats/',
        SiteViewSet.as_view({'get': 'dashboard_stats'}),
        name='sites-dashboard-stats'
    ),
]

urlpatterns += site_detail_patterns
