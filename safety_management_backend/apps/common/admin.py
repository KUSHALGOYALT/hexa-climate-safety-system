from django.contrib import admin
from .models import EmergencyContact

@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'company', 'site', 'contact_type', 'is_primary', 'is_active']
    list_filter = ['contact_type', 'is_primary', 'is_active', 'is_available_24_7', 'company', 'created_at']
    search_fields = ['name', 'position', 'company__name', 'site__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-is_primary', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'site', 'name', 'position', 'contact_type')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'alternate_phone')
        }),
        ('Availability', {
            'fields': ('is_available_24_7', 'availability_notes')
        }),
        ('Status', {
            'fields': ('is_active', 'is_primary')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'site')
