from django.core.management.base import BaseCommand
from django.db import transaction
import inspect
import importlib

class Command(BaseCommand):
    help = 'Auditar vistas para verificar el uso de transacciones atómicas'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                '🔍 AUDITORÍA DE TRANSACCIONES EN VISTAS\n'
                '=' * 50
            )
        )
        
        # Importar el módulo de vistas
        views_module = importlib.import_module('mainapp.views')
        
        # Vistas que DEBEN tener transacciones (operaciones críticas)
        critical_views = [
            'create_organization',
            'create_form',
            'create_form_from_template',
            'add_field_to_form',
            'delete_field',
            'view_form',  # Para submissions
            'register',   # Para crear usuarios
        ]
        
        # Vistas que PUEDEN tener transacciones (operaciones menores)
        optional_views = [
            'edit_form',
            'form_submissions',
            'team_management',
        ]
        
        self.stdout.write('\n📋 Vistas críticas que DEBEN tener transacciones:')
        for view_name in critical_views:
            if hasattr(views_module, view_name):
                view_func = getattr(views_module, view_name)
                has_transaction = self._check_for_transaction(view_func)
                
                if has_transaction:
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✓ {view_name} - Tiene transacciones')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ {view_name} - SIN transacciones')
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(f'   ⚠️  {view_name} - Vista no encontrada')
                )
        
        self.stdout.write('\n📝 Vistas opcionales:')
        for view_name in optional_views:
            if hasattr(views_module, view_name):
                view_func = getattr(views_module, view_name)
                has_transaction = self._check_for_transaction(view_func)
                
                if has_transaction:
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✓ {view_name} - Tiene transacciones')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'   ⚠️  {view_name} - Sin transacciones (opcional)')
                    )
        
        # Buscar todas las vistas que usan models para operaciones de escritura
        self.stdout.write('\n🔎 Analizando todas las vistas por operaciones de escritura:')
        all_functions = inspect.getmembers(views_module, inspect.isfunction)
        
        write_operations = ['save()', 'create(', 'update(', 'delete(', 'bulk_create', 'bulk_update']
        
        for func_name, func in all_functions:
            if func_name.startswith('_'):  # Ignorar funciones privadas
                continue
                
            source = inspect.getsource(func)
            has_write_ops = any(op in source for op in write_operations)
            has_transaction = self._check_for_transaction(func)
            
            if has_write_ops and not has_transaction:
                self.stdout.write(
                    self.style.WARNING(f'   ⚠️  {func_name} - Tiene operaciones de escritura pero sin transacciones')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n✅ Auditoría completada!\n'
                'Recomendaciones:\n'
                '• Todas las vistas críticas deben usar @transaction.atomic o with transaction.atomic()\n'
                '• Las operaciones de escritura múltiples deben estar envueltas en transacciones\n'
                '• Usar try-except para manejo de errores dentro de las transacciones\n'
            )
        )
    
    def _check_for_transaction(self, func):
        """Verificar si una función usa transacciones atómicas"""
        try:
            source = inspect.getsource(func)
            return (
                'transaction.atomic' in source or
                '@transaction.atomic' in source or
                'with transaction.atomic' in source
            )
        except (OSError, TypeError):
            return False
