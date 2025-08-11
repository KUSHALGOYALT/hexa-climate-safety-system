from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.sites.urls')),
    path('api/v1/', include('apps.incidents.urls')),
    path('api/v1/', include('apps.companies.urls')),
    path('api/v1/', include('apps.employees.urls')),
    path('api/v1/', include('apps.common.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 