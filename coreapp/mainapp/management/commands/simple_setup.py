from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.conf import settings
import os
import sys
import sqlite3

User = get_user_model()

class Command(BaseCommand):
    help = 'Configuración inicial simple para Docker'

    def add_arguments(self, parser):
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

    def handle(self, *args, **options):
        admin_user = options['admin_user']
        admin_password = options['admin_password'] 
        admin_email = options['admin_email']

        self.stdout.write("🚀 Iniciando configuración Docker...")

        try:
            # Verificar que podemos conectar a la BD
            self.stdout.write("📊 Verificando conexión a base de datos...")
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            # Verificar si ya hay datos
            user_count = User.objects.count()
            if user_count > 0:
                self.stdout.write(f"✅ Base de datos ya configurada ({user_count} usuarios)")
                return

            # Crear superusuario
            self.stdout.write("👤 Creando usuario administrador...")
            if not User.objects.filter(username=admin_user).exists():
                User.objects.create_superuser(
                    username=admin_user,
                    password=admin_password,
                    email=admin_email
                )
                self.stdout.write(f"✅ Usuario '{admin_user}' creado exitosamente")
            else:
                self.stdout.write(f"ℹ️ Usuario '{admin_user}' ya existe")

            # Ejecutar setup de datos iniciales si existe
            try:
                call_command('setup_initial_data')
                self.stdout.write("✅ Datos iniciales configurados")
            except Exception as e:
                self.stdout.write(f"⚠️ Warning: {e}")

            self.stdout.write("✅ Configuración completada exitosamente")
            self.stdout.write(f"🔑 Credenciales: {admin_user} / {admin_password}")

        except Exception as e:
            self.stdout.write(f"❌ Error: {e}")
            sys.exit(1)
