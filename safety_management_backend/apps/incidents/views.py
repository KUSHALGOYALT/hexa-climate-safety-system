from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Count
from .models import Incident, IncidentResponse, IncidentNotification
from .serializers import IncidentSerializer, IncidentResponseSerializer, IncidentListSerializer, IncidentDetailSerializer

class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'incident_type', 'criticality']
    search_fields = ['title', 'description', 'reporter_name', 'incident_number']
    ordering_fields = ['created_at', 'status', 'criticality', 'incident_type']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return IncidentListSerializer
        elif self.action == 'retrieve':
            return IncidentDetailSerializer
        return IncidentSerializer

    def get_queryset(self):
        """Override queryset to handle headquarters filtering"""
        queryset = super().get_queryset()
        
        # Handle headquarters filter
        site_filter = self.request.query_params.get('site', None)
        if site_filter == 'headquarters':
            queryset = queryset.filter(site__isnull=True)
        elif site_filter:
            queryset = queryset.filter(site=site_filter)
            
        return queryset

    def send_incident_notification(self, incident):
        """Send email notification to parent company (Hexa Climate)"""
        try:
            # Get parent company email from settings
            parent_company_email = settings.PARENT_COMPANY_EMAIL
            parent_company_name = settings.PARENT_COMPANY_NAME
            
            # Create notification record
            notification = IncidentNotification.objects.create(
                incident=incident,
                notification_type='EMAIL',
                recipient_email=parent_company_email,
                recipient_name=parent_company_name,
                subject=f"New Safety Incident Report - {incident.incident_number}",
                message=self.create_notification_message(incident),
                status='PENDING'
            )
            
            # Send email
            send_mail(
                subject=notification.subject,
                message=notification.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[parent_company_email],
                fail_silently=False,
            )
            
            # Update notification status
            notification.status = 'SENT'
            notification.sent_at = timezone.now()
            notification.save()
            
            return True
        except Exception as e:
            # Log error and update notification status
            if 'notification' in locals():
                notification.status = 'FAILED'
                notification.error_message = str(e)
                notification.save()
            return False

    def create_notification_message(self, incident):
        """Create notification message for the incident"""
        if incident.site:
            site_name = incident.site.name
            company_name = incident.site.company.name if incident.site.company else "Unknown Company"
        else:
            # Headquarters incident
            site_name = "Hexa Climate Headquarters"
            company_name = "Hexa Climate"
        
        message = f"""
NEW SAFETY INCIDENT REPORT

Incident Number: {incident.incident_number}
Site: {site_name}
Company: {company_name}
Type: {incident.get_incident_type_display()}
Criticality: {incident.get_criticality_display()}

Title: {incident.title}
Description: {incident.description}

Location: {incident.location_description or 'Not specified'}

Reporter Information:
- Name: {incident.reporter_name or 'Anonymous'}
- Email: {incident.reporter_email or 'Not provided'}
- Phone: {incident.reporter_phone or 'Not provided'}
- Employee ID: {incident.employee_id or 'Not provided'}
- Department: {incident.department or 'Not provided'}

Device Information:
- Device Type: {incident.get_device_type_display()}
- IP Address: {incident.ip_address or 'Not available'}

Reported At: {incident.created_at.strftime('%Y-%m-%d %H:%M:%S')}

Please review and take appropriate action.

Best regards,
Safety Management System
        """
        return message.strip()

    def create(self, request, *args, **kwargs):
        """Override create to handle field mapping and use site location"""
        data = request.data.copy()
        
        # Map frontend field names to model field names
        field_mapping = {
            'incident_latitude': 'latitude',
            'incident_longitude': 'longitude',
            'reporter_name': 'reporter_name',
            'reporter_contact': 'reporter_phone',
            'reporter_employee_id': 'employee_id',
            'reporter_department': 'department'
        }
        
        # Apply field mapping
        for frontend_field, model_field in field_mapping.items():
            if frontend_field in data:
                data[model_field] = data.pop(frontend_field)
        
        # Use site location if no coordinates provided
        if 'site' in data and not data.get('latitude') and not data.get('longitude'):
            try:
                from apps.sites.models import Site
                site = Site.objects.get(id=data['site'])
                data['latitude'] = site.latitude
                data['longitude'] = site.longitude
            except Site.DoesNotExist:
                pass
        
        request._full_data = data
        response = super().create(request, *args, **kwargs)
        
        # Send notification to parent company
        if response.status_code == 201:
            incident = Incident.objects.get(id=response.data['id'])
            self.send_incident_notification(incident)
        
        return response

    @action(detail=False, methods=['post'], url_path='anonymous')
    def anonymous(self, request):
        """Create an anonymous incident report"""
        try:
            # Add site information from session or request
            data = request.data.copy()
            
            # Set default values for anonymous reports
            data['is_anonymous'] = True
            data['status'] = 'REPORTED'  # Use valid status choice
            
            # Map frontend field names to model field names
            field_mapping = {
                'incident_latitude': 'latitude',
                'incident_longitude': 'longitude',
                'reporter_name': 'reporter_name',
                'reporter_contact': 'reporter_phone',
                'reporter_employee_id': 'employee_id',
                'reporter_department': 'department'
            }
            
            # Apply field mapping
            for frontend_field, model_field in field_mapping.items():
                if frontend_field in data:
                    data[model_field] = data.pop(frontend_field)
            
            # Handle headquarters incidents
            if data.get('is_headquarters'):
                # Set headquarters location (Gurugram coordinates)
                data['latitude'] = 28.4595
                data['longitude'] = 77.0266
                data['site'] = None  # No specific site for headquarters
            # Use site location if no coordinates provided
            elif 'site' in data and not data.get('latitude') and not data.get('longitude'):
                try:
                    from apps.sites.models import Site
                    site = Site.objects.get(id=data['site'])
                    data['latitude'] = site.latitude
                    data['longitude'] = site.longitude
                except Site.DoesNotExist:
                    pass
            
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                incident = serializer.save()
                
                # Send notification to parent company
                self.send_incident_notification(incident)
                
                return Response({
                    'success': True,
                    'message': 'Incident reported successfully',
                    'incident_id': incident.id
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error creating incident: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='notifications')
    def get_notifications(self, request, pk=None):
        """Get notifications for a specific incident"""
        incident = self.get_object()
        notifications = incident.notifications.all()
        
        notification_data = []
        for notification in notifications:
            notification_data.append({
                'id': notification.id,
                'type': notification.notification_type,
                'recipient_email': notification.recipient_email,
                'recipient_name': notification.recipient_name,
                'subject': notification.subject,
                'status': notification.status,
                'created_at': notification.created_at,
                'sent_at': notification.sent_at,
                'error_message': notification.error_message
            })
        
        return Response({
            'incident_id': incident.id,
            'incident_number': incident.incident_number,
            'notifications': notification_data
        })

    @action(detail=False, methods=['get'], url_path='all-notifications')
    def get_all_notifications(self, request):
        """Get all notifications for admin dashboard"""
        notifications = IncidentNotification.objects.all().order_by('-created_at')
        
        notification_data = []
        for notification in notifications:
            notification_data.append({
                'id': notification.id,
                'incident_id': notification.incident.id,
                'incident_number': notification.incident.incident_number,
                'type': notification.notification_type,
                'recipient_email': notification.recipient_email,
                'recipient_name': notification.recipient_name,
                'subject': notification.subject,
                'status': notification.status,
                'created_at': notification.created_at,
                'sent_at': notification.sent_at,
                'error_message': notification.error_message
            })
        
        return Response({
            'total_notifications': len(notification_data),
            'notifications': notification_data
        })

    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        """Update incident status"""
        try:
            incident = self.get_object()
            new_status = request.data.get('status')
            
            if not new_status:
                return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate status
            valid_statuses = [choice[0] for choice in Incident.STATUS_CHOICES]
            if new_status not in valid_statuses:
                return Response({'error': f'Invalid status. Valid choices: {valid_statuses}'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Update status
            incident.status = new_status
            incident.update_status_timestamps()
            incident.save()
            
            return Response({
                'id': incident.id,
                'status': incident.status,
                'message': f'Incident status updated to {new_status}'
            })
            
        except Incident.DoesNotExist:
            return Response({'error': 'Incident not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """Get dashboard statistics for incidents"""
        company_id = request.query_params.get('company')
        site_id = request.query_params.get('site')
        queryset = self.get_queryset()

        # Filter by company if provided
        if company_id:
            queryset = queryset.filter(site__entity__company_id=company_id)

        # Filter by site if provided
        if site_id:
            queryset = queryset.filter(site_id=site_id)

        # Get date range filter
        days = request.query_params.get('days', 30)
        if days:
            try:
                days = int(days)
                from datetime import timedelta
                start_date = timezone.now() - timedelta(days=days)
                queryset = queryset.filter(created_at__gte=start_date)
            except ValueError:
                pass

        stats = {
            'total_incidents': queryset.count(),
            'pending_incidents': queryset.filter(status='PENDING').count(),
            'resolved_incidents': queryset.filter(status='RESOLVED').count(),
            'critical_incidents': queryset.filter(criticality='CRITICAL').count(),
            'by_type': dict(
                queryset.values_list('incident_type')
                .annotate(count=Count('id'))
                .order_by('incident_type')
            ),
            'by_criticality': dict(
                queryset.values_list('criticality')
                .annotate(count=Count('id'))
                .order_by('criticality')
            ),
            'by_status': dict(
                queryset.values_list('status')
                .annotate(count=Count('id'))
                .order_by('status')
            ),
            'by_site': dict(
                queryset.values_list('site__name')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]  # Top 10 sites
            ),
            'by_company': dict(
                queryset.values_list('site__entity__company__name')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]  # Top 10 companies
            ),
            'recent_incidents': queryset.order_by('-created_at')[:5].values(
                'id', 'incident_number', 'incident_type', 'criticality', 
                'status', 'created_at', 'site__name'
            )
        }

        return Response(stats)

class IncidentResponseViewSet(viewsets.ModelViewSet):
    queryset = IncidentResponse.objects.all()
    serializer_class = IncidentResponseSerializer
