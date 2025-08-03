from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Employee

@receiver(post_save, sender=Employee)
def sync_user_account(sender, instance, created, **kwargs):
    """Sync employee data with user account if user exists"""
    # Only sync if employee has a user account (for admin users)
    if hasattr(instance, 'user') and instance.user:
        # Update user details
        instance.user.email = instance.email
        # Split name into first and last name
        name_parts = instance.name.split(' ', 1)
        instance.user.first_name = name_parts[0] if name_parts else ''
        instance.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        instance.user.is_active = instance.is_active
        instance.user.save()

@receiver(pre_delete, sender=Employee)
def handle_employee_deletion(sender, instance, **kwargs):
    """Handle employee deletion"""
    # Only handle if employee has a user account
    if hasattr(instance, 'user') and instance.user:
        # Don't delete user account, just deactivate
        instance.user.is_active = False
        instance.user.save()
