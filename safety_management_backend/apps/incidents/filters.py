import django_filters
from django.db.models import Q
from .models import Incident

class IncidentFilter(django_filters.FilterSet):
    """Custom filter for incidents"""

    # Date range filters
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte'
    )

    # Multi-choice filters
    incident_types = django_filters.MultipleChoiceFilter(
        field_name='incident_type',
        choices=Incident.INCIDENT_TYPES
    )

    criticalities = django_filters.MultipleChoiceFilter(
        field_name='criticality',
        choices=Incident.CRITICALITY_LEVELS
    )

    statuses = django_filters.MultipleChoiceFilter(
        field_name='status',
        choices=Incident.STATUS_CHOICES
    )

    # Boolean filters
    is_overdue = django_filters.BooleanFilter(method='filter_overdue')
    is_anonymous = django_filters.BooleanFilter()
    has_responses = django_filters.BooleanFilter(method='filter_has_responses')

    # Location filters
    has_location = django_filters.BooleanFilter(method='filter_has_location')

    # Assignment filters
    is_assigned = django_filters.BooleanFilter(method='filter_is_assigned')
    assigned_to = django_filters.CharFilter(lookup_expr='icontains')

    # Priority filter
    min_priority = django_filters.NumberFilter(
        field_name='priority_score',
        lookup_expr='gte'
    )

    class Meta:
        model = Incident
        fields = [
            'site', 'incident_type', 'criticality', 'status',
            'is_anonymous', 'device_type'
        ]

    def filter_overdue(self, queryset, name, value):
        """Filter overdue incidents"""
        if value:
            from django.utils import timezone
            from datetime import timedelta

            now = timezone.now()

            # Define overdue conditions
            overdue_q = Q()

            # Emergency: 4 hours
            overdue_q |= Q(
                criticality='EMERGENCY',
                created_at__lt=now - timedelta(hours=4),
                status__in=['REPORTED', 'ACKNOWLEDGED', 'INVESTIGATING']
            )

            # Critical: 1 day
            overdue_q |= Q(
                criticality='CRITICAL',
                created_at__lt=now - timedelta(days=1),
                status__in=['REPORTED', 'ACKNOWLEDGED', 'INVESTIGATING']
            )

            # High: 3 days
            overdue_q |= Q(
                criticality='HIGH',
                created_at__lt=now - timedelta(days=3),
                status__in=['REPORTED', 'ACKNOWLEDGED', 'INVESTIGATING', 'IN_PROGRESS']
            )

            # Medium: 7 days
            overdue_q |= Q(
                criticality='MEDIUM',
                created_at__lt=now - timedelta(days=7),
                status__in=['REPORTED', 'ACKNOWLEDGED', 'INVESTIGATING', 'IN_PROGRESS']
            )

            # Low: 30 days
            overdue_q |= Q(
                criticality='LOW',
                created_at__lt=now - timedelta(days=30),
                status__in=['REPORTED', 'ACKNOWLEDGED', 'INVESTIGATING', 'IN_PROGRESS']
            )

            return queryset.filter(overdue_q)

        return queryset

    def filter_has_responses(self, queryset, name, value):
        """Filter incidents that have responses"""
        if value:
            return queryset.filter(responses__isnull=False).distinct()
        else:
            return queryset.filter(responses__isnull=True)

    def filter_has_location(self, queryset, name, value):
        """Filter incidents that have GPS coordinates"""
        if value:
            return queryset.filter(
                latitude__isnull=False,
                longitude__isnull=False
            )
        else:
            return queryset.filter(
                Q(latitude__isnull=True) | Q(longitude__isnull=True)
            )

    def filter_is_assigned(self, queryset, name, value):
        """Filter assigned/unassigned incidents"""
        if value:
            return queryset.exclude(assigned_to='').exclude(assigned_to__isnull=True)
        else:
            return queryset.filter(
                Q(assigned_to='') | Q(assigned_to__isnull=True)
            )
