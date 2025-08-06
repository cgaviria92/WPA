from django.core.management.base import BaseCommand
from mainapp.models import FieldType

class Command(BaseCommand):
    help = 'Poblar tipos de campos con sus costos'

    def handle(self, *args, **options):
        field_types_data = [
            {
                'name': 'text',
                'display_name': 'Texto Corto',
                'cost': 10,
                'storage_multiplier': 1.0
            },
            {
                'name': 'textarea',
                'display_name': 'Texto Largo',
                'cost': 25,
                'storage_multiplier': 2.0
            },
            {
                'name': 'number',
                'display_name': 'Número',
                'cost': 5,
                'storage_multiplier': 0.5
            },
            {
                'name': 'email',
                'display_name': 'Email',
                'cost': 15,
                'storage_multiplier': 1.2
            },
            {
                'name': 'date',
                'display_name': 'Fecha',
                'cost': 8,
                'storage_multiplier': 0.8
            },
            {
                'name': 'file',
                'display_name': 'Archivo',
                'cost': 50,
                'storage_multiplier': 5.0
            },
            {
                'name': 'boolean',
                'display_name': 'Verdadero/Falso',
                'cost': 3,
                'storage_multiplier': 0.3
            },
            {
                'name': 'choice',
                'display_name': 'Selección',
                'cost': 20,
                'storage_multiplier': 1.5
            },
        ]

        for field_data in field_types_data:
            field_type, created = FieldType.objects.get_or_create(
                name=field_data['name'],
                defaults={
                    'display_name': field_data['display_name'],
                    'cost': field_data['cost'],
                    'storage_multiplier': field_data['storage_multiplier']
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Creado tipo de campo: {field_type.display_name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Ya existe: {field_type.display_name}')
                )
