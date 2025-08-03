from django.db import models

class DeviceStatus(models.Model):
    DEVICE_TYPES = [
        ('MOBILE', 'Mobile Device'),
        ('TABLET', 'Tablet'),
        ('KIOSK', 'Reporting Kiosk'),
    ]

    device_id = models.CharField(max_length=100, unique=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES, default='MOBILE')
    site = models.ForeignKey('sites.Site', on_delete=models.CASCADE, related_name='devices')
    last_active = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    location_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'device_status'

    def __str__(self):
        return f"{self.device_id} - {self.site.name}"
