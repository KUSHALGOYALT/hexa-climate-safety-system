from django.contrib import admin
from .models import Incident

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ['title', 'severity', 'status', 'location_type', 'location_id', 'reporter_name', 'incident_date', 'is_active']
    list_filter = ['severity', 'status', 'location_type', 'is_active', 'incident_date', 'reported_date']
    search_fields = ['title', 'description', 'reporter_name']
    readonly_fields = ['reported_date', 'created_at', 'updated_at'] 