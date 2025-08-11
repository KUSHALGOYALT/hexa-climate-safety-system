from django.contrib import admin
from .models import Site

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'site_code', 'entity', 'plant_type', 'operational_status', 'city', 'state', 'is_active']
    list_filter = ['plant_type', 'operational_status', 'is_active', 'entity', 'created_at']
    search_fields = ['name', 'site_code', 'city', 'state', 'address']
    readonly_fields = ['created_at', 'updated_at'] 