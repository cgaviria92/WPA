from django.core.management.base import BaseCommand
from mainapp.models import FormTemplate

class Command(BaseCommand):
    help = 'Crear plantillas predefinidas de formularios'

    def handle(self, *args, **options):
        templates = [
            {
                'name': 'Sistema de Inventario Completo',
                'description': 'Gestión completa de inventario con compras, ventas y control de stock',
                'category': 'inventory',
                'icon': 'fas fa-boxes',
                'template_data': {
                    'title': 'Gestión de Inventario',
                    'submissions_label': 'Transacciones',
                    'fields': [
                        {
                            'field_type': 'text_short',
                            'label': 'Tipo de Transacción',
                            'choices': 'Compra\nVenta\nAjuste\nDevolución',
                            'is_required': True,
                            'help_text': 'Selecciona el tipo de movimiento'
                        },
                        {
                            'field_type': 'text_short',
                            'label': 'Producto/Artículo',
                            'is_required': True,
                            'help_text': 'Nombre del producto'
                        },
                        {
                            'field_type': 'text_short',
                            'label': 'SKU/Código',
                            'is_required': True,
                            'help_text': 'Código único del producto'
                        },
                        {
                            'field_type': 'number',
                            'label': 'Cantidad',
                            'is_required': True,
                            'help_text': 'Cantidad de productos'
                        },
                        {
                            'field_type': 'number',
                            'label': 'Precio Unitario',
                            'is_required': True,
                            'help_text': 'Precio por unidad'
                        },
                        {
                            'field_type': 'text_short',
                            'label': 'Proveedor/Cliente',
                            'help_text': 'Nombre del proveedor o cliente'
                        },
                        {
                            'field_type': 'text_long',
                            'label': 'Notas',
                            'help_text': 'Observaciones adicionales'
                        }
                    ]
                },
                'business_logic': '''
# Lógica de inventario automática
def process_inventory_transaction(submission_data):
    from mainapp.models import InventoryItem, InventoryTransaction
    from decimal import Decimal
    
    # Extraer datos
    transaction_type = submission_data.get('field_1', '').lower()
    product_name = submission_data.get('field_2', '')
    sku = submission_data.get('field_3', '')
    quantity = int(submission_data.get('field_4', 0))
    unit_price = Decimal(submission_data.get('field_5', 0))
    
    # Crear o actualizar artículo
    item, created = InventoryItem.objects.get_or_create(
        organization=organization,
        sku=sku,
        defaults={
            'name': product_name,
            'purchase_price': unit_price if transaction_type == 'compra' else 0,
            'sale_price': unit_price if transaction_type == 'venta' else 0,
        }
    )
    
    # Crear transacción
    transaction = InventoryTransaction.objects.create(
        organization=organization,
        item=item,
        transaction_type=transaction_type.replace('compra', 'purchase').replace('venta', 'sale'),
        quantity=quantity,
        unit_price=unit_price,
        created_by=user,
        related_form_submission=form_submission
    )
    
    return {
        'success': True,
        'message': f'Transacción procesada: {transaction}',
        'stock_actual': item.current_stock,
        'margen_ganancia': f"{item.profit_margin:.2f}%"
    }
                '''
            },
            {
                'name': 'Control de Ventas con Margen',
                'description': 'Registro de ventas con cálculo automático de márgenes de ganancia',
                'category': 'sales',
                'icon': 'fas fa-chart-line',
                'template_data': {
                    'title': 'Control de Ventas',
                    'submissions_label': 'Ventas',
                    'fields': [
                        {
                            'field_type': 'date',
                            'label': 'Fecha de Venta',
                            'is_required': True
                        },
                        {
                            'field_type': 'text_short',
                            'label': 'Cliente',
                            'is_required': True
                        },
                        {
                            'field_type': 'text_short',
                            'label': 'Producto Vendido',
                            'is_required': True
                        },
                        {
                            'field_type': 'number',
                            'label': 'Cantidad',
                            'is_required': True
                        },
                        {
                            'field_type': 'number',
                            'label': 'Precio de Venta Unitario',
                            'is_required': True
                        },
                        {
                            'field_type': 'selection',
                            'label': 'Método de Pago',
                            'choices': 'Efectivo\nTarjeta\nTransferencia\nCrédito',
                            'is_required': True
                        },
                        {
                            'field_type': 'text_long',
                            'label': 'Observaciones'
                        }
                    ]
                },
                'business_logic': '''
def process_sale(submission_data):
    from mainapp.models import InventoryItem, InventoryTransaction
    from decimal import Decimal
    
    # Calcular totales y márgenes automáticamente
    producto = submission_data.get('field_3', '')
    cantidad = int(submission_data.get('field_4', 0))
    precio_venta = Decimal(submission_data.get('field_5', 0))
    
    # Buscar producto en inventario
    try:
        item = InventoryItem.objects.get(organization=organization, name=producto)
        margen = ((precio_venta - item.purchase_price) / item.purchase_price) * 100
        ganancia_total = (precio_venta - item.purchase_price) * cantidad
        
        return {
            'success': True,
            'total_venta': precio_venta * cantidad,
            'margen_porcentaje': f"{margen:.2f}%",
            'ganancia_total': ganancia_total,
            'stock_restante': item.current_stock - cantidad
        }
    except InventoryItem.DoesNotExist:
        return {'success': False, 'error': 'Producto no encontrado en inventario'}
                '''
            },
            {
                'name': 'Registro de Empleados',
                'description': 'Formulario completo para registro de nuevos empleados',
                'category': 'hr',
                'icon': 'fas fa-users',
                'template_data': {
                    'title': 'Registro de Empleados',
                    'submissions_label': 'Empleados',
                    'fields': [
                        {
                            'field_type': 'text_short',
                            'label': 'Nombre Completo',
                            'is_required': True
                        },
                        {
                            'field_type': 'email',
                            'label': 'Email Corporativo',
                            'is_required': True
                        },
                        {
                            'field_type': 'text_short',
                            'label': 'Teléfono',
                            'is_required': True
                        },
                        {
                            'field_type': 'selection',
                            'label': 'Departamento',
                            'choices': 'Administración\nVentas\nIT\nRecursos Humanos\nContabilidad\nOperaciones',
                            'is_required': True
                        },
                        {
                            'field_type': 'text_short',
                            'label': 'Cargo',
                            'is_required': True
                        },
                        {
                            'field_type': 'date',
                            'label': 'Fecha de Ingreso',
                            'is_required': True
                        },
                        {
                            'field_type': 'number',
                            'label': 'Salario',
                            'is_required': True
                        },
                        {
                            'field_type': 'text_long',
                            'label': 'Observaciones'
                        }
                    ]
                }
            },
            {
                'name': 'Soporte al Cliente',
                'description': 'Sistema de tickets para atención al cliente',
                'category': 'customer',
                'icon': 'fas fa-headset',
                'template_data': {
                    'title': 'Soporte al Cliente',
                    'submissions_label': 'Tickets',
                    'fields': [
                        {
                            'field_type': 'text_short',
                            'label': 'Nombre del Cliente',
                            'is_required': True
                        },
                        {
                            'field_type': 'email',
                            'label': 'Email de Contacto',
                            'is_required': True
                        },
                        {
                            'field_type': 'selection',
                            'label': 'Prioridad',
                            'choices': 'Baja\nMedia\nAlta\nUrgente',
                            'is_required': True
                        },
                        {
                            'field_type': 'selection',
                            'label': 'Categoría',
                            'choices': 'Técnico\nFacturación\nConsulta General\nReclamo\nSugerencia',
                            'is_required': True
                        },
                        {
                            'field_type': 'text_short',
                            'label': 'Asunto',
                            'is_required': True
                        },
                        {
                            'field_type': 'text_long',
                            'label': 'Descripción del Problema',
                            'is_required': True
                        },
                        {
                            'field_type': 'file',
                            'label': 'Adjuntar Archivo'
                        }
                    ]
                }
            },
            {
                'name': 'Control de Gastos',
                'description': 'Registro y control de gastos empresariales',
                'category': 'finance',
                'icon': 'fas fa-dollar-sign',
                'template_data': {
                    'title': 'Control de Gastos',
                    'submissions_label': 'Gastos',
                    'fields': [
                        {
                            'field_type': 'date',
                            'label': 'Fecha del Gasto',
                            'is_required': True
                        },
                        {
                            'field_type': 'selection',
                            'label': 'Categoría',
                            'choices': 'Oficina\nTransporte\nComidas\nMaterial\nServicios\nMarketing\nOtros',
                            'is_required': True
                        },
                        {
                            'field_type': 'text_short',
                            'label': 'Concepto',
                            'is_required': True
                        },
                        {
                            'field_type': 'number',
                            'label': 'Monto',
                            'is_required': True
                        },
                        {
                            'field_type': 'text_short',
                            'label': 'Proveedor',
                            'is_required': True
                        },
                        {
                            'field_type': 'selection',
                            'label': 'Método de Pago',
                            'choices': 'Efectivo\nTarjeta Corporativa\nTransferencia\nCheque',
                            'is_required': True
                        },
                        {
                            'field_type': 'boolean',
                            'label': '¿Tiene Factura?'
                        },
                        {
                            'field_type': 'file',
                            'label': 'Adjuntar Recibo/Factura'
                        }
                    ]
                }
            }
        ]

        created_count = 0
        for template_data in templates:
            template, created = FormTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Creada plantilla: {template.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'- Plantilla ya existe: {template.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Proceso completado! {created_count} plantillas nuevas creadas.')
        )
