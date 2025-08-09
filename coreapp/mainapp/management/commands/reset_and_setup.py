from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db import connection, transaction
import os
import sys
import subprocess

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
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Ejecuta automáticamente sin confirmación (para Docker)',
        )
        parser.add_argument(
            '--initial-data',
            action='store_true',
            help='Configura datos iniciales',
        )
        parser.add_argument(
            '--admin-user',
            type=str,
            default='admin',
            help='Nombre de usuario del administrador',
        )
        parser.add_argument(
            '--admin-password',
            type=str,
            default='admin1234',
            help='Contraseña del administrador',
        )
        parser.add_argument(
            '--admin-email',
            type=str,
            default='admin@example.com',
            help='Email del administrador',
        )
        parser.add_argument(
            '--serve',
            action='store_true',
            help='Inicia el servidor después de la configuración',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                '🚀 SCRIPT DE INICIALIZACIÓN COMPLETA DE WPA\n'
                '=' * 50
            )
        )

        # Confirmación de seguridad (saltar si es --execute para Docker)
        if not options['force'] and not options['execute']:
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
            admin_user = options['admin_user']
            admin_password = options['admin_password'] 
            admin_email = options['admin_email']
            
            with transaction.atomic():
                if not User.objects.filter(username=admin_user).exists():
                    User.objects.create_superuser(
                        username=admin_user,
                        email=admin_email,
                        password=admin_password,
                        monedas=10000
                    )
                    self.stdout.write(self.style.SUCCESS(f'   ✓ Superusuario creado ({admin_user}/{admin_password})'))
                else:
                    self.stdout.write(self.style.WARNING(f'   ⚠️  Superusuario {admin_user} ya existe'))

            # 4. Poblar tipos de campo
            self.stdout.write('\n📝 Paso 4: Configurando tipos de campo...')
            try:
                call_command('populate_field_types', verbosity=0)
                self.stdout.write(self.style.SUCCESS('   ✓ Tipos de campo configurados'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠️  {str(e)}'))

            # 5. Configurar datos iniciales (solo si se especifica)
            if options['initial_data']:
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
            admin_user = options['admin_user']
            admin_password = options['admin_password']
            
            self.stdout.write(
                self.style.SUCCESS(
                    '\n🎉 ¡CONFIGURACIÓN COMPLETADA EXITOSAMENTE!\n'
                    '=' * 50 + '\n'
                    '📊 Resumen de lo configurado:\n'
                    '   • Base de datos SQLite creada\n'
                    '   • Migraciones aplicadas\n'
                    f'   • Superusuario: {admin_user} / {admin_password}\n'
                    '   • Tipos de campo configurados\n'
                    + ('   • Organización de ejemplo creada\n' if options['initial_data'] else '') +
                    ('   • 5 plantillas de formularios\n' if options['initial_data'] else '') +
                    '   • Sistema listo para usar\n\n'
                    '🌐 Accede en: http://localhost:8000\n'
                    f'   Usuario: {admin_user}\n'
                    f'   Contraseña: {admin_password}\n'
                )
            )

            # Si se especifica --serve, iniciar el servidor
            if options['serve']:
                self.stdout.write(
                    self.style.SUCCESS(
                        '\n🚀 Iniciando servidor en puerto 8000...\n'
                    )
                )
                # Ejecutar collectstatic antes de servir
                call_command('collectstatic', '--noinput', '--clear')
                
                # Iniciar el servidor
                call_command('runserver', '0.0.0.0:8000')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'\n❌ ERROR durante la configuración:\n{str(e)}\n'
                    'Por favor revisa los logs y vuelve a intentar.'
                )
            )
            sys.exit(1)
