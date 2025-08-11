from django.db import models

class DashboardStats(models.Model):
    """Model to store dashboard statistics"""
    total_sites = models.IntegerField(default=0)
    total_entities = models.IntegerField(default=0)
    total_employees = models.IntegerField(default=0)
    total_incidents = models.IntegerField(default=0)
    operational_sites = models.IntegerField(default=0)
    maintenance_sites = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Dashboard Statistics"

    def __str__(self):
        return f"Dashboard Stats - {self.last_updated.strftime('%Y-%m-%d %H:%M')}" 