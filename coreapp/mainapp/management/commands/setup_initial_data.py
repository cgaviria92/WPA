from django.core.management.base import BaseCommand
from mainapp.models import FieldType

class Command(BaseCommand):
    help = 'Inicializar datos básicos del sistema'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando población de datos...')
        
        # Crear tipos de campos si no existen
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

        created_count = 0
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
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Creado tipo de campo: {field_type.display_name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'○ Ya existe: {field_type.display_name}')
                )
        
        self.stdout.write('')
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'¡Listo! Se crearon {created_count} tipos de campo.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Todos los tipos de campo ya estaban creados.')
            )
        
        self.stdout.write('')
        self.stdout.write('📋 Tipos de campo disponibles:')
        for field_type in FieldType.objects.all().order_by('cost'):
            self.stdout.write(f'  • {field_type.display_name}: {field_type.cost} monedas')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('🎉 ¡Inicialización completada exitosamente!'))
        self.stdout.write('')
        self.stdout.write('🚀 Próximos pasos:')
        self.stdout.write('   1. Ejecuta: python manage.py runserver')
        self.stdout.write('   2. Ve a http://localhost:8000')
        self.stdout.write('   3. ¡Regístrate como el primer usuario para ser admin!')
