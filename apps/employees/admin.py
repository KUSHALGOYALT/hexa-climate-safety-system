from django.contrib import admin
from .models import Employee, EmployeeLocation

class EmployeeLocationInline(admin.TabularInline):
    model = EmployeeLocation
    extra = 1
    fields = ['location_type', 'location_id', 'show_in_emergency_contacts', 'is_active']

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['name', 'employee_id', 'designation', 'department', 'is_active', 'created_at']
    list_filter = ['is_active', 'department', 'created_at']
    search_fields = ['name', 'employee_id', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [EmployeeLocationInline]

@admin.register(EmployeeLocation)
class EmployeeLocationAdmin(admin.ModelAdmin):
    list_display = ['employee', 'location_type', 'location_id', 'show_in_emergency_contacts', 'is_active']
    list_filter = ['location_type', 'show_in_emergency_contacts', 'is_active', 'created_at']
    search_fields = ['employee__name', 'location_id']
    readonly_fields = ['created_at', 'updated_at'] 