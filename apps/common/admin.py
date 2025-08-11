from django.contrib import admin
from .models import DashboardStats

@admin.register(DashboardStats)
class DashboardStatsAdmin(admin.ModelAdmin):
    list_display = ['total_sites', 'total_entities', 'total_employees', 'total_incidents', 'last_updated']
    readonly_fields = ['last_updated'] 