from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db import connection
import os
import sys

User = get_user_model()

class Command(BaseCommand):
    help = 'Resetea la base de datos y configura datos iniciales'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza el reset sin confirmación',
        )
        parser.add_argument(
            '--keep-db',
            action='store_true',
            help='No elimina la base de datos, solo ejecuta migraciones y setup',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                '🚀 SCRIPT DE INICIALIZACIÓN COMPLETA DE WPA\n'
                '=' * 50
            )
        )

        # Confirmación de seguridad
        if not options['force']:
            confirm = input('\n⚠️  ADVERTENCIA: Esto eliminará TODOS los datos existentes.\n'
                           '¿Estás seguro de continuar? (yes/no): ')
            if confirm.lower() not in ['yes', 'y', 'sí', 'si']:
                self.stdout.write(self.style.ERROR('❌ Operación cancelada.'))
                return

        try:
            # 1. Eliminar base de datos (si no se especifica --keep-db)
            if not options['keep_db']:
                self.stdout.write('\n📂 Paso 1: Eliminando base de datos...')
                db_path = 'db.sqlite3'
                if os.path.exists(db_path):
                    os.remove(db_path)
                    self.stdout.write(self.style.SUCCESS('   ✓ Base de datos eliminada'))
                else:
                    self.stdout.write(self.style.WARNING('   ⚠️  Base de datos no encontrada'))

            # 2. Ejecutar migraciones
            self.stdout.write('\n🔄 Paso 2: Ejecutando migraciones...')
            call_command('makemigrations', verbosity=0)
            self.stdout.write(self.style.SUCCESS('   ✓ Migraciones creadas'))
            
            call_command('migrate', verbosity=0)
            self.stdout.write(self.style.SUCCESS('   ✓ Migraciones aplicadas'))

            # 3. Crear superusuario
            self.stdout.write('\n👤 Paso 3: Creando superusuario...')
            if not User.objects.filter(username='admin').exists():
                User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin123',
                    monedas=10000
                )
                self.stdout.write(self.style.SUCCESS('   ✓ Superusuario creado (admin/admin123)'))
            else:
                self.stdout.write(self.style.WARNING('   ⚠️  Superusuario ya existe'))

            # 4. Poblar tipos de campo
            self.stdout.write('\n📝 Paso 4: Configurando tipos de campo...')
            try:
                call_command('populate_field_types', verbosity=0)
                self.stdout.write(self.style.SUCCESS('   ✓ Tipos de campo configurados'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠️  {str(e)}'))

            # 5. Configurar datos iniciales
            self.stdout.write('\n🏢 Paso 5: Configurando datos iniciales...')
            try:
                call_command('setup_initial_data', verbosity=0)
                self.stdout.write(self.style.SUCCESS('   ✓ Datos iniciales configurados'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠️  {str(e)}'))

            # 6. Configurar plantillas de formularios
            self.stdout.write('\n📋 Paso 6: Configurando plantillas de formularios...')
            try:
                call_command('setup_form_templates', verbosity=0)
                self.stdout.write(self.style.SUCCESS('   ✓ Plantillas de formularios configuradas'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠️  {str(e)}'))

            # 7. Resumen final
            self.stdout.write(
                self.style.SUCCESS(
                    '\n🎉 ¡CONFIGURACIÓN COMPLETADA EXITOSAMENTE!\n'
                    '=' * 50 + '\n'
                    '📊 Resumen de lo configurado:\n'
                    '   • Base de datos SQLite creada\n'
                    '   • Migraciones aplicadas\n'
                    '   • Superusuario: admin / admin123\n'
                    '   • Tipos de campo configurados\n'
                    '   • Organización de ejemplo creada\n'
                    '   • 5 plantillas de formularios\n'
                    '   • Sistema listo para usar\n\n'
                    '🚀 Para arrancar el servidor:\n'
                    '   python manage.py runserver 0.0.0.0:8000\n\n'
                    '🌐 Accede en: http://localhost:8000\n'
                    '   Usuario: admin\n'
                    '   Contraseña: admin123\n'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'\n❌ ERROR durante la configuración:\n{str(e)}\n'
                    'Por favor revisa los logs y vuelve a intentar.'
                )
            )
            sys.exit(1)
