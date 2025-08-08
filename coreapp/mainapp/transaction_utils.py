"""
Utilities para manejo de transacciones en el sistema WPA
"""
from django.db import transaction
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def atomic_transaction(func):
    """
    Decorador para asegurar que las operaciones de la vista se ejecuten dentro de una transacción atómica.
    En caso de excepción, hace rollback automático.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            with transaction.atomic():
                return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error en transacción para {func.__name__}: {str(e)}")
            # La transacción se hace rollback automáticamente
            raise
    return wrapper

def safe_bulk_create(model_class, objects, batch_size=100):
    """
    Crea objetos en lotes de forma segura con transacciones
    """
    try:
        with transaction.atomic():
            created_objects = []
            for i in range(0, len(objects), batch_size):
                batch = objects[i:i + batch_size]
                created_objects.extend(model_class.objects.bulk_create(batch))
            return created_objects
    except Exception as e:
        logger.error(f"Error en bulk_create para {model_class.__name__}: {str(e)}")
        raise

def safe_bulk_update(queryset, update_fields, batch_size=100):
    """
    Actualiza objetos en lotes de forma segura con transacciones
    """
    try:
        with transaction.atomic():
            objects = list(queryset)
            for i in range(0, len(objects), batch_size):
                batch = objects[i:i + batch_size]
                queryset.model.objects.bulk_update(batch, update_fields)
            return len(objects)
    except Exception as e:
        logger.error(f"Error en bulk_update: {str(e)}")
        raise

class TransactionManager:
    """
    Gestor de contexto para transacciones más complejas
    """
    
    def __init__(self, savepoint=True):
        self.savepoint = savepoint
        self.transaction = None
        
    def __enter__(self):
        if self.savepoint:
            self.transaction = transaction.savepoint()
        else:
            self.transaction = transaction.atomic().__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if self.savepoint:
                transaction.savepoint_rollback(self.transaction)
            else:
                self.transaction.__exit__(exc_type, exc_val, exc_tb)
            logger.error(f"Transacción hecha rollback por excepción: {exc_val}")
            return False
        else:
            if self.savepoint:
                transaction.savepoint_commit(self.transaction)
            else:
                self.transaction.__exit__(exc_type, exc_val, exc_tb)
            return True

# Función para verificar el estado de las transacciones
def get_transaction_status():
    """
    Retorna información sobre el estado actual de las transacciones
    """
    return {
        'in_atomic_block': transaction.get_autocommit(),
        'connection_vendor': transaction.get_connection().vendor,
        'has_pending_transaction': bool(transaction.get_connection().in_atomic_block)
    }
