from rest_framework import serializers
from django.core.validators import validate_email
from .models import Incident, IncidentResponse, IncidentAttachment, IncidentNotification
from apps.sites.serializers import SiteListSerializer

class IncidentResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentResponse
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class IncidentAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentAttachment
        fields = '__all__'
        read_only_fields = ['uploaded_at']

class IncidentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing incidents"""
    site_name = serializers.CharField(source='site.name', read_only=True)
    company_name = serializers.CharField(source='site.company.name', read_only=True)
    age_in_days = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    reporter_display_name = serializers.ReadOnlyField(source='get_reporter_display_name')

    class Meta:
        model = Incident
        fields = [
            'id', 'incident_number', 'title', 'description', 'location_description', 'incident_type', 'criticality',
            'status', 'site_name', 'company_name', 'reporter_display_name', 'reporter_name', 'reporter_phone',
            'created_at', 'age_in_days', 'is_overdue', 'priority_score'
        ]

class IncidentDetailSerializer(serializers.ModelSerializer):
    """Full serializer for incident details"""
    site_name = serializers.CharField(source='site.name', read_only=True)
    company_name = serializers.CharField(source='site.company.name', read_only=True)
    site_details = SiteListSerializer(source='site', read_only=True)
    responses = IncidentResponseSerializer(many=True, read_only=True)
    attachments = IncidentAttachmentSerializer(many=True, read_only=True)

    # Computed fields
    age_in_days = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    reporter_display_name = serializers.ReadOnlyField(source='get_reporter_display_name')
    coordinates = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = '__all__'
        read_only_fields = [
            'incident_id', 'incident_number', 'priority_score',
            'created_at', 'updated_at', 'acknowledged_at',
            'resolved_at', 'closed_at'
        ]

    def get_coordinates(self, obj):
        """Get coordinates as dict"""
        coords = obj.get_coordinates()
        if coords:
            return {'latitude': coords[0], 'longitude': coords[1]}
        return None

class IncidentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating incidents"""

    class Meta:
        model = Incident
        fields = [
            'site', 'incident_type', 'title', 'description',
            'location_description', 'latitude', 'longitude',
            'criticality', 'reporter_name', 'reporter_email',
            'reporter_phone', 'employee_id', 'department',
            'device_id', 'device_type', 'tags'
        ]

    def validate_reporter_email(self, value):
        """Validate reporter email if provided"""
        if value:
            validate_email(value)
        return value

    def validate_title(self, value):
        """Validate title length and content"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Title must be at least 10 characters long."
            )
        return value.strip()

    def validate_description(self, value):
        """Validate description length and content"""
        if len(value.strip()) < 20:
            raise serializers.ValidationError(
                "Description must be at least 20 characters long."
            )
        return value.strip()

    def validate(self, data):
        """Cross-field validation"""
        # Validate coordinates if provided
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if latitude is not None and longitude is None:
            raise serializers.ValidationError({
                'longitude': 'Longitude is required when latitude is provided.'
            })

        if longitude is not None and latitude is None:
            raise serializers.ValidationError({
                'latitude': 'Latitude is required when longitude is provided.'
            })

        # Validate coordinate ranges
        if latitude is not None and (latitude < -90 or latitude > 90):
            raise serializers.ValidationError({
                'latitude': 'Latitude must be between -90 and 90 degrees.'
            })

        if longitude is not None and (longitude < -180 or longitude > 180):
            raise serializers.ValidationError({
                'longitude': 'Longitude must be between -180 and 180 degrees.'
            })

        return data

    def create(self, validated_data):
        """Create incident with additional processing"""
        # Extract request metadata if available
        request = self.context.get('request')
        if request:
            validated_data['ip_address'] = self.get_client_ip(request)
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')

        return super().create(validated_data)

    def get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

class AnonymousIncidentSerializer(serializers.ModelSerializer):
    """Serializer for anonymous incident reports"""
    is_headquarters = serializers.BooleanField(required=False, default=False)
    severity = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = Incident
        fields = [
            'site', 'incident_type', 'title', 'description',
            'location_description', 'latitude', 'longitude',
            'criticality', 'device_id', 'device_type', 'tags',
            'is_headquarters', 'severity'
        ]

    def validate(self, data):
        """Validate that site is provided unless it's a headquarters incident"""
        is_headquarters = data.get('is_headquarters', False)
        site = data.get('site')
        
        if not is_headquarters and not site:
            raise serializers.ValidationError({
                'site': 'Site is required for non-headquarters incidents.'
            })
        
        return data

    def validate_title(self, value):
        """Validate title for anonymous reports"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Title must be at least 10 characters long."
            )
        return value.strip()

    def validate_description(self, value):
        """Validate description for anonymous reports"""
        if len(value.strip()) < 20:
            raise serializers.ValidationError(
                "Description must be at least 20 characters long."
            )
        return value.strip()

    def create(self, validated_data):
        """Create anonymous incident"""
        validated_data['is_anonymous'] = True

        # Map severity to criticality if provided
        severity = validated_data.pop('severity', None)
        if severity:
            validated_data['criticality'] = severity

        # Extract request metadata if available
        request = self.context.get('request')
        if request:
            validated_data['ip_address'] = self.get_client_ip(request)
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')

        return super().create(validated_data)

    def get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

class IncidentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating incidents"""

    class Meta:
        model = Incident
        fields = [
            'status', 'criticality', 'assigned_to', 'assigned_at',
            'resolution_notes', 'corrective_actions', 'preventive_actions',
            'estimated_resolution_date', 'actual_resolution_date', 'tags'
        ]

    def update(self, instance, validated_data):
        """Update incident with status change handling"""
        old_status = instance.status
        new_status = validated_data.get('status', old_status)

        # Handle status change logic
        if old_status != new_status:
            validated_data = self.handle_status_change(
                instance, validated_data, old_status, new_status
            )

        return super().update(instance, validated_data)

    def handle_status_change(self, instance, validated_data, old_status, new_status):
        """Handle status change with appropriate timestamps"""
        from django.utils import timezone

        now = timezone.now()

        if new_status == 'ACKNOWLEDGED' and not instance.acknowledged_at:
            validated_data['acknowledged_at'] = now
        elif new_status == 'RESOLVED' and not instance.resolved_at:
            validated_data['resolved_at'] = now
        elif new_status == 'CLOSED' and not instance.closed_at:
            validated_data['closed_at'] = now

        return validated_data

class IncidentStatsSerializer(serializers.Serializer):
    """Serializer for incident statistics"""
    total_incidents = serializers.IntegerField()
    by_type = serializers.DictField()
    by_criticality = serializers.DictField()
    by_status = serializers.DictField()
    overdue_incidents = serializers.IntegerField()
    recent_incidents = IncidentListSerializer(many=True)
    average_resolution_time = serializers.FloatField()

class IncidentNotificationSerializer(serializers.ModelSerializer):
    """Serializer for incident notifications"""

    class Meta:
        model = IncidentNotification
        fields = '__all__'
        read_only_fields = ['created_at', 'sent_at', 'delivered_at']

class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = '__all__'
