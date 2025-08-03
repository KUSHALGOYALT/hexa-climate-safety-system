from django.contrib import admin
from django.utils.html import format_html
from .models import Company, Entity

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'company_code', 'company_type', 'parent_company',
        'city', 'state', 'is_active', 'entities_count', 'created_at'
    ]
    list_filter = [
        'company_type', 'is_active', 'state', 'country', 'created_at'
    ]
    search_fields = [
        'name', 'company_code', 'city', 'state', 'address'
    ]
    readonly_fields = ['created_at', 'updated_at', 'entities_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'company_code', 'company_type', 'parent_company',
                'is_active'
            )
        }),
        ('Address', {
            'fields': (
                'address', 'city', 'state', 'country', 'country_code', 'postal_code'
            )
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'website')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 25

    def entities_count(self, obj):
        return obj.entities.count()
    entities_count.short_description = 'Entities'

@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'entity_code', 'entity_type', 'company', 'city', 'state',
        'is_active', 'sites_count', 'employees_count', 'created_at'
    ]
    list_filter = [
        'entity_type', 'company', 'is_active', 'state', 'country', 'created_at'
    ]
    search_fields = [
        'name', 'entity_code', 'city', 'state', 'company__name'
    ]
    readonly_fields = ['created_at', 'updated_at', 'sites_count', 'employees_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'entity_code', 'entity_type', 'company',
                'description', 'is_active'
            )
        }),
        ('Address', {
            'fields': (
                'address', 'city', 'state', 'country'
            )
        }),
        ('Contact Information', {
            'fields': ('phone', 'email')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 25

    def sites_count(self, obj):
        return obj.get_sites_count()
    sites_count.short_description = 'Sites'

    def employees_count(self, obj):
        return obj.get_employees_count()
    employees_count.short_description = 'Employees'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('company')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize foreign key fields"""
        if db_field.name == "company":
            kwargs["queryset"] = kwargs["queryset"].filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs) 