from django.contrib import admin
from .models import Company, Entity

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'company_code', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'company_code']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ['name', 'entity_code', 'entity_type', 'company', 'city', 'state', 'is_active']
    list_filter = ['entity_type', 'is_active', 'company', 'created_at']
    search_fields = ['name', 'entity_code', 'city', 'state']
    readonly_fields = ['created_at', 'updated_at'] 