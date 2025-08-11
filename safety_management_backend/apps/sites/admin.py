from django.contrib import admin
from .models import Site, SiteConfiguration

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'site_code', 'company', 'plant_type', 'operational_status', 'is_active', 'created_at']
    list_filter = ['plant_type', 'operational_status', 'is_active', 'state', 'country', 'created_at']
    search_fields = ['name', 'site_code', 'company__name', 'city', 'state']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'name', 'site_code', 'description')
        }),
        ('Address Information', {
            'fields': ('address', 'city', 'state', 'country', 'postal_code')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email')
        }),
        ('Plant Information', {
            'fields': ('plant_type', 'capacity', 'operational_status')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company')

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ['site', 'enabled_forms', 'show_phone', 'show_email', 'show_address']
    list_filter = ['show_phone', 'show_email', 'show_address', 'created_at']
    search_fields = ['site__name', 'site__site_code']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Site', {
            'fields': ('site',)
        }),
        ('Form Configuration', {
            'fields': ('enabled_forms',)
        }),
        ('Display Configuration', {
            'fields': ('show_phone', 'show_email', 'show_address')
        }),
        ('Quick Info Configuration', {
            'fields': ('quick_info_config',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('site')
