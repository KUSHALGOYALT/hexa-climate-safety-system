from django.contrib import admin
from .models import Employee, EmployeeAssignment

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['name', 'employee_id', 'company', 'position', 'employment_type', 'is_active', 'created_at']
    list_filter = ['employment_type', 'is_active', 'company', 'created_at']
    search_fields = ['name', 'employee_id', 'position', 'company__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'name', 'employee_id', 'position', 'employment_type')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship')
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

@admin.register(EmployeeAssignment)
class EmployeeAssignmentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'site', 'is_primary', 'is_active', 'assigned_date']
    list_filter = ['is_primary', 'is_active', 'assigned_date', 'site__company']
    search_fields = ['employee__name', 'site__name', 'site__company__name']
    readonly_fields = ['assigned_date']
    ordering = ['-assigned_date']
    
    fieldsets = (
        ('Assignment', {
            'fields': ('employee', 'site')
        }),
        ('Status', {
            'fields': ('is_primary', 'is_active')
        }),
        ('Dates', {
            'fields': ('assigned_date', 'end_date')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee', 'site', 'site__company')
