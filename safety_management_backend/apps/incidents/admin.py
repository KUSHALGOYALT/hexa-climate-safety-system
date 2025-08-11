from django.contrib import admin
from .models import Incident

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ['title', 'site', 'incident_type', 'severity', 'status', 'reported_by', 'created_at']
    list_filter = ['incident_type', 'severity', 'status', 'anonymous', 'site__company', 'created_at']
    search_fields = ['title', 'description', 'reported_by', 'site__name', 'location']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('site', 'incident_type', 'severity', 'status')
        }),
        ('Incident Details', {
            'fields': ('title', 'description', 'location')
        }),
        ('Reporter Information', {
            'fields': ('reported_by', 'contact_number', 'email', 'anonymous')
        }),
        ('Assignment', {
            'fields': ('assigned_to',)
        }),
        ('Timestamps', {
            'fields': ('incident_date', 'created_at', 'updated_at')
        }),
        ('Resolution', {
            'fields': ('actions_taken', 'recommendations', 'cost_estimate')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('site', 'site__company', 'assigned_to')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('created_at', 'updated_at')
        return self.readonly_fields
