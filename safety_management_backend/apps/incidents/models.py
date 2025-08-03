from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import datetime
import uuid

class Incident(models.Model):
    INCIDENT_TYPES = [
        ('UNSAFE_ACT', 'Unsafe Act'),
        ('UNSAFE_CONDITION', 'Unsafe Condition'),
        ('NEAR_MISS', 'Near Miss'),
        ('FEEDBACK', 'General Feedback'),
    ]

    CRITICALITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
        ('EMERGENCY', 'Emergency'),
    ]

    STATUS_CHOICES = [
        ('REPORTED', 'Reported'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('INVESTIGATING', 'Under Investigation'),
        ('IN_PROGRESS', 'Corrective Action in Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]

    DEVICE_TYPES = [
        ('MOBILE', 'Mobile Device'),
        ('TABLET', 'Tablet'),
        ('KIOSK', 'Reporting Kiosk'),
        ('WEB', 'Web Browser'),
    ]

    # Basic Information
    incident_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    site = models.ForeignKey(
        'sites.Site',
        on_delete=models.CASCADE,
        related_name='incidents',
        null=True,
        blank=True
    )
    incident_type = models.CharField(max_length=20, choices=INCIDENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()

    # Location Information
    location_description = models.CharField(max_length=500, blank=True)
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        blank=True,
        null=True,
        help_text="Incident location latitude"
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        blank=True,
        null=True,
        help_text="Incident location longitude"
    )

    # Severity and Status
    criticality = models.CharField(
        max_length=20,
        choices=CRITICALITY_LEVELS,
        default='LOW'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='REPORTED'
    )

    # Reporter Information (optional for anonymous reports)
    reporter_name = models.CharField(max_length=200, blank=True)
    reporter_email = models.EmailField(blank=True)
    reporter_phone = models.CharField(max_length=20, blank=True)
    employee_id = models.CharField(max_length=50, blank=True)
    department = models.CharField(max_length=100, blank=True)

    # Device Information
    device_id = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(
        max_length=20,
        choices=DEVICE_TYPES,
        default='MOBILE'
    )
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)

    # System Fields
    is_anonymous = models.BooleanField(default=False)
    incident_number = models.CharField(max_length=50, unique=True, blank=True)
    priority_score = models.IntegerField(default=1)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)

    # Follow-up fields
    assigned_to = models.CharField(max_length=200, blank=True)
    assigned_at = models.DateTimeField(blank=True, null=True)
    resolution_notes = models.TextField(blank=True)
    corrective_actions = models.TextField(blank=True)
    preventive_actions = models.TextField(blank=True)

    # Additional metadata
    tags = models.JSONField(default=list, blank=True)
    estimated_resolution_date = models.DateTimeField(blank=True, null=True)
    actual_resolution_date = models.DateTimeField(blank=True, null=True)

    # Files and attachments (if needed)
    attachment_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'incidents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['site', 'status']),
            models.Index(fields=['incident_type', 'criticality']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status', 'assigned_to']),
        ]

    def __str__(self):
        return f"{self.incident_number} - {self.title[:50]}"

    def save(self, *args, **kwargs):
        # Generate incident number if not exists
        if not self.incident_number:
            self.incident_number = self.generate_incident_number()

        # Calculate priority score
        self.priority_score = self.calculate_priority_score()

        # Update status timestamps
        self.update_status_timestamps()

        super().save(*args, **kwargs)

    def generate_incident_number(self):
        """Generate unique incident number"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        site_code = self.site.site_code if self.site else 'UNKNOWN'
        incident_type = self.incident_type[:2] if self.incident_type else 'GN'
        return f"INC-{site_code}-{incident_type}-{timestamp}"

    def calculate_priority_score(self):
        """Calculate priority score based on criticality and type"""
        criticality_scores = {
            'EMERGENCY': 10,
            'CRITICAL': 8,
            'HIGH': 6,
            'MEDIUM': 4,
            'LOW': 2
        }

        type_multiplier = {
            'UNSAFE_CONDITION': 1.2,
            'NEAR_MISS': 1.1,
            'UNSAFE_ACT': 1.0,
            'FEEDBACK': 0.8
        }

        base_score = criticality_scores.get(self.criticality, 1)
        multiplier = type_multiplier.get(self.incident_type, 1)

        return int(base_score * multiplier)

    def update_status_timestamps(self):
        """Update timestamps based on status changes"""
        now = timezone.now()

        if self.status == 'ACKNOWLEDGED' and not self.acknowledged_at:
            self.acknowledged_at = now
        elif self.status == 'RESOLVED' and not self.resolved_at:
            self.resolved_at = now
        elif self.status == 'CLOSED' and not self.closed_at:
            self.closed_at = now

    @property
    def site_name(self):
        return self.site.name if self.site else ''

    @property
    def company_name(self):
        return self.site.company.name if self.site and self.site.company else ''

    @property
    def age_in_days(self):
        """Calculate age of incident in days"""
        return (timezone.now() - self.created_at).days

    @property
    def is_overdue(self):
        """Check if incident is overdue based on criticality"""
        if self.status in ['RESOLVED', 'CLOSED']:
            return False

        overdue_days = {
            'EMERGENCY': 0,  # Same day
            'CRITICAL': 1,   # 1 day
            'HIGH': 3,       # 3 days
            'MEDIUM': 7,     # 1 week
            'LOW': 30        # 1 month
        }

        allowed_days = overdue_days.get(self.criticality, 30)
        return self.age_in_days > allowed_days

    def get_coordinates(self):
        """Get coordinates as tuple"""
        if self.latitude and self.longitude:
            return (float(self.latitude), float(self.longitude))
        return None

    def get_reporter_display_name(self):
        """Get display name for reporter"""
        if self.is_anonymous:
            return "Anonymous"
        return self.reporter_name or "Unknown"

class IncidentResponse(models.Model):
    RESPONSE_TYPES = [
        ('INVESTIGATION', 'Investigation'),
        ('CORRECTIVE_ACTION', 'Corrective Action'),
        ('PREVENTIVE_ACTION', 'Preventive Action'),
        ('FOLLOW_UP', 'Follow-up'),
        ('STATUS_UPDATE', 'Status Update'),
        ('CLOSURE', 'Closure'),
    ]

    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='responses'
    )
    response_type = models.CharField(max_length=20, choices=RESPONSE_TYPES)
    response_text = models.TextField()

    # Responder Information
    responder_name = models.CharField(max_length=200)
    responder_email = models.EmailField(blank=True)
    responder_role = models.CharField(max_length=100, blank=True)

    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_internal = models.BooleanField(default=True)
    is_visible_to_reporter = models.BooleanField(default=True)

    class Meta:
        db_table = 'incident_responses'
        ordering = ['-created_at']

    def __str__(self):
        return f"Response to {self.incident.incident_number} - {self.response_type}"

class IncidentAttachment(models.Model):
    ATTACHMENT_TYPES = [
        ('IMAGE', 'Image'),
        ('DOCUMENT', 'Document'),
        ('VIDEO', 'Video'),
        ('AUDIO', 'Audio'),
        ('OTHER', 'Other'),
    ]

    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.IntegerField()
    file_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPES)
    mime_type = models.CharField(max_length=100, blank=True)

    uploaded_by = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # File metadata
    is_public = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'incident_attachments'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.incident.incident_number} - {self.file_name}"

class IncidentNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PUSH', 'Push Notification'),
        ('SYSTEM', 'System Notification'),
    ]

    NOTIFICATION_STATUS = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('DELIVERED', 'Delivered'),
        ('FAILED', 'Failed'),
    ]

    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    recipient_email = models.EmailField(blank=True)
    recipient_phone = models.CharField(max_length=20, blank=True)
    recipient_name = models.CharField(max_length=200)

    subject = models.CharField(max_length=200)
    message = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=NOTIFICATION_STATUS,
        default='PENDING'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'incident_notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.incident.incident_number} - {self.recipient_name}"
