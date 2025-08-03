from django.core.management.base import BaseCommand
from apps.companies.models import Company, Entity
from apps.sites.models import Site
from apps.employees.models import Employee

class Command(BaseCommand):
    help = 'Set up Hexa Climate and sample entities'

    def handle(self, *args, **options):
        self.stdout.write('Setting up Hexa Climate hierarchy...')

        # Create Hexa Climate as parent company
        hexa_climate, created = Company.objects.get_or_create(
            company_code='HEXA001',
            defaults={
                'name': 'Hexa Climate',
                'company_type': 'PARENT',
                'address': 'Kumbhari, Maharashtra, India',
                'city': 'Kumbhari',
                'state': 'Maharashtra',
                'country': 'India',
                'postal_code': '413001',
                'phone': '9660027799',
                'email': 'info@hexaclimate.com',
                'website': 'https://hexaclimate.com',
                'is_active': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Hexa Climate company'))
        else:
            self.stdout.write(self.style.WARNING(f'Hexa Climate company already exists'))

        # Create sample entities under Hexa Climate
        entities_data = [
            {
                'name': 'Solar Division',
                'entity_code': 'SOLAR',
                'entity_type': 'DIVISION',
                'description': 'Solar power plant operations and maintenance',
                'city': 'Kumbhari',
                'state': 'Maharashtra'
            },
            {
                'name': 'Construction Division',
                'entity_code': 'CONSTR',
                'entity_type': 'DIVISION',
                'description': 'Construction and project management',
                'city': 'Kumbhari',
                'state': 'Maharashtra'
            },
            {
                'name': 'Maintenance Division',
                'entity_code': 'MAINT',
                'entity_type': 'DIVISION',
                'description': 'Plant maintenance and technical services',
                'city': 'Kumbhari',
                'state': 'Maharashtra'
            },
            {
                'name': 'Regional Office',
                'entity_code': 'REGION',
                'entity_type': 'REGION',
                'description': 'Regional management and coordination',
                'city': 'Mumbai',
                'state': 'Maharashtra'
            }
        ]

        created_entities = []
        for entity_data in entities_data:
            entity, created = Entity.objects.get_or_create(
                entity_code=entity_data['entity_code'],
                company=hexa_climate,
                defaults={
                    'name': entity_data['name'],
                    'entity_type': entity_data['entity_type'],
                    'description': entity_data['description'],
                    'city': entity_data['city'],
                    'state': entity_data['state'],
                    'country': 'India',
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created entity: {entity.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Entity already exists: {entity.name}'))
            
            created_entities.append(entity)

        # Create sample sites under entities
        sites_data = [
            {
                'entity_code': 'SOLAR',
                'name': '30MWp Hexa Kumbhari Plant',
                'site_code': 'HEXAKUMBHARI',
                'plant_type': 'SOLAR',
                'capacity': '30 MWp',
                'city': 'Kumbhari',
                'state': 'Maharashtra'
            },
            {
                'entity_code': 'CONSTR',
                'name': 'Construction Site A',
                'site_code': 'CONSTRA',
                'plant_type': 'OTHER',
                'capacity': 'N/A',
                'city': 'Kumbhari',
                'state': 'Maharashtra'
            },
            {
                'entity_code': 'MAINT',
                'name': 'Maintenance Hub',
                'site_code': 'MAINTHUB',
                'plant_type': 'OTHER',
                'capacity': 'N/A',
                'city': 'Kumbhari',
                'state': 'Maharashtra'
            }
        ]

        for site_data in sites_data:
            entity = Entity.objects.get(entity_code=site_data['entity_code'], company=hexa_climate)
            site, created = Site.objects.get_or_create(
                site_code=site_data['site_code'],
                entity=entity,
                defaults={
                    'name': site_data['name'],
                    'plant_type': site_data['plant_type'],
                    'capacity': site_data['capacity'],
                    'address': f"{site_data['city']}, {site_data['state']}, India",
                    'city': site_data['city'],
                    'state': site_data['state'],
                    'country': 'India',
                    'latitude': 19.0760,
                    'longitude': 72.8777,
                    'phone': '9660027799',
                    'email': 'info@hexaclimate.com',
                    'operational_status': 'OPERATIONAL',
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created site: {site.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Site already exists: {site.name}'))

        self.stdout.write(self.style.SUCCESS('Hexa Climate hierarchy setup completed!'))
        self.stdout.write(f'Created {len(created_entities)} entities under Hexa Climate') 