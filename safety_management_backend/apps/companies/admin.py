from django.contrib import admin
from .models import Company

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'company_code', 'company_type', 'city', 'state', 'is_active', 'created_at']
    list_filter = ['company_type', 'is_active', 'state', 'country', 'created_at']
    search_fields = ['name', 'company_code', 'city', 'state']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'company_code', 'company_type', 'parent_company')
        }),
        ('Address Information', {
            'fields': ('address', 'city', 'state', 'country', 'postal_code')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
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
        return super().get_queryset(request).select_related('parent_company')
