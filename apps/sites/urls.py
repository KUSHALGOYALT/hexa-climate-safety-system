from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SiteViewSet, PublicSiteAccessView, validate_site_qr

router = DefaultRouter()
router.register(r'sites', SiteViewSet)
router.register(r'public', PublicSiteAccessView, basename='public')

urlpatterns = [
    path('', include(router.urls)),
    path('public/<str:company_code>/<str:site_code>/', validate_site_qr, name='validate_site_qr'),
] 