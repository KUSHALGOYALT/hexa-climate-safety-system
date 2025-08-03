from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponse
import csv
from .models import Site

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'site_code', 'entity', 'city', 'state',
        'operational_status', 'plant_type', 'is_active',
        'qr_code_link', 'created_at'
    ]
    list_filter = [
        'entity', 'operational_status', 'plant_type',
        'is_active', 'state', 'country', 'created_at'
    ]
    search_fields = [
        'name', 'site_code', 'city', 'state', 'address',
        'entity__name', 'entity__entity_code', 'entity__company__name'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'qr_code_preview',
        'coordinates_display', 'full_address'
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'entity', 'name', 'site_code', 'description',
                'is_active'
            )
        }),
        ('Location Details', {
            'fields': (
                'address', 'city', 'state', 'country',
                'country_code', 'postal_code', 'latitude',
                'longitude', 'coordinates_display'
            )
        }),
        ('Contact Information', {
            'fields': ('phone', 'email')
        }),
        ('Plant Details', {
            'fields': (
                'plant_type', 'capacity', 'operational_status',
                'commissioned_date', 'last_maintenance_date',
                'next_maintenance_date'
            )
        }),
        ('QR Code', {
            'fields': ('qr_code_preview',),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at', 'full_address'),
            'classes': ('collapse',)
        }),
    )

    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 25

    actions = [
        'activate_sites',
        'deactivate_sites',
        'export_to_csv',
        'mark_operational',
        'mark_maintenance'
    ]

    def qr_code_link(self, obj):
        """Display QR code generation link"""
        url = reverse('admin:sites_site_change', args=[obj.pk])
        return format_html(
            '<a href="{}#qr_code_preview" target="_blank">View QR</a>',
            url
        )
    qr_code_link.short_description = 'QR Code'

    def qr_code_preview(self, obj):
        """Display QR code image in admin"""
        if obj.pk:
            qr_image = obj.generate_qr_code()
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px;" />',
                qr_image
            )
        return "Save the site first to generate QR code"
    qr_code_preview.short_description = 'QR Code Preview'

    def coordinates_display(self, obj):
        """Display coordinates with Google Maps link"""
        if obj.latitude and obj.longitude:
            maps_url = f"https://www.google.com/maps?q={obj.latitude},{obj.longitude}"
            return format_html(
                'Lat: {}, Lng: {} <br><a href="{}" target="_blank">View on Maps</a>',
                obj.latitude, obj.longitude, maps_url
            )
        return "No coordinates set"
    coordinates_display.short_description = 'GPS Coordinates'

    def activate_sites(self, request, queryset):
        """Bulk activate sites"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} sites were successfully activated.'
        )
    activate_sites.short_description = "Activate selected sites"

    def deactivate_sites(self, request, queryset):
        """Bulk deactivate sites"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} sites were successfully deactivated.'
        )
    deactivate_sites.short_description = "Deactivate selected sites"

    def mark_operational(self, request, queryset):
        """Mark sites as operational"""
        updated = queryset.update(operational_status='OPERATIONAL')
        self.message_user(
            request,
            f'{updated} sites marked as operational.'
        )
    mark_operational.short_description = "Mark as operational"

    def mark_maintenance(self, request, queryset):
        """Mark sites as under maintenance"""
        updated = queryset.update(operational_status='MAINTENANCE')
        self.message_user(
            request,
            f'{updated} sites marked as under maintenance.'
        )
    mark_maintenance.short_description = "Mark as under maintenance"

    def export_to_csv(self, request, queryset):
        """Export selected sites to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sites_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Name', 'Site Code', 'Company', 'City', 'State', 'Country',
            'Latitude', 'Longitude', 'Phone', 'Email', 'Plant Type',
            'Capacity', 'Operational Status', 'Is Active', 'Created At'
        ])

        for site in queryset:
            writer.writerow([
                site.name, site.site_code, site.entity.name,
                site.city, site.state, site.country,
                site.latitude, site.longitude, site.phone, site.email,
                site.plant_type, site.capacity, site.operational_status,
                site.is_active, site.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response
    export_to_csv.short_description = "Export selected sites to CSV"

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('entity', 'entity__company')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize foreign key fields"""
        if db_field.name == "entity":
            kwargs["queryset"] = kwargs["queryset"].filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
