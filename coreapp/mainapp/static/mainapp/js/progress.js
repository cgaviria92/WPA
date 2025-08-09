/**
 * Sistema de progreso para WPA
 * Maneja indicadores de progreso y operaciones asíncronas
 */

class ProgressManager {
    constructor() {
        this.activeProcesses = new Map();
        this.initializeProgressModal();
    }

    /**
     * Inicializa el modal de progreso
     */
    initializeProgressModal() {
        // Crear modal si no existe
        if (!document.getElementById('progressModal')) {
            const modalHTML = `
                <div class="modal fade" id="progressModal" tabindex="-1" data-bs-backdrop="static" data-bs-keyboard="false">
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content">
                            <div class="modal-header border-0">
                                <h5 class="modal-title" id="progressModalTitle">Procesando...</h5>
                            </div>
                            <div class="modal-body text-center">
                                <div class="progress mb-3" style="height: 20px;">
                                    <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                         role="progressbar" style="width: 0%" id="progressBar">
                                        <span id="progressPercentage">0%</span>
                                    </div>
                                </div>
                                <p class="mb-0" id="progressMessage">Iniciando...</p>
                                <div class="mt-3">
                                    <span class="badge bg-info" id="progressStep">Paso 1 de 5</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }
    }

    /**
     * Muestra el progreso
     */
    showProgress(title = 'Procesando...') {
        const modal = new bootstrap.Modal(document.getElementById('progressModal'));
        document.getElementById('progressModalTitle').textContent = title;
        this.updateProgress(0, 'Iniciando...', 1, 5);
        modal.show();
        return modal;
    }

    /**
     * Actualiza el progreso
     */
    updateProgress(percentage, message, currentStep = null, totalSteps = null) {
        const progressBar = document.getElementById('progressBar');
        const progressPercentage = document.getElementById('progressPercentage');
        const progressMessage = document.getElementById('progressMessage');
        const progressStep = document.getElementById('progressStep');

        progressBar.style.width = `${percentage}%`;
        progressPercentage.textContent = `${Math.round(percentage)}%`;
        progressMessage.textContent = message;

        if (currentStep && totalSteps) {
            progressStep.textContent = `Paso ${currentStep} de ${totalSteps}`;
        }

        // Cambiar color según el progreso
        progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
        if (percentage >= 100) {
            progressBar.classList.add('bg-success');
        } else if (percentage >= 75) {
            progressBar.classList.add('bg-info');
        } else if (percentage >= 50) {
            progressBar.classList.add('bg-warning');
        } else {
            progressBar.classList.add('bg-primary');
        }
    }

    /**
     * Oculta el progreso
     */
    hideProgress() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('progressModal'));
        if (modal) {
            modal.hide();
        }
    }

    /**
     * Muestra mensaje de éxito
     */
    showSuccess(message, redirectUrl = null) {
        this.updateProgress(100, message, null, null);
        
        setTimeout(() => {
            this.hideProgress();
            if (redirectUrl) {
                window.location.href = redirectUrl;
            }
        }, 2000);
    }

    /**
     * Muestra mensaje de error
     */
    showError(message) {
        const progressBar = document.getElementById('progressBar');
        progressBar.className = 'progress-bar bg-danger';
        this.updateProgress(100, `Error: ${message}`, null, null);
        
        setTimeout(() => {
            this.hideProgress();
        }, 3000);
    }

    /**
     * Simula progreso para operaciones largas
     */
    simulateProgress(duration = 5000, steps = 5) {
        return new Promise((resolve) => {
            let currentStep = 0;
            const stepDuration = duration / steps;
            
            const interval = setInterval(() => {
                currentStep++;
                const percentage = (currentStep / steps) * 100;
                const messages = [
                    'Validando datos...',
                    'Procesando información...',
                    'Creando estructura...',
                    'Aplicando configuración...',
                    'Finalizando proceso...'
                ];
                
                this.updateProgress(
                    percentage,
                    messages[currentStep - 1] || 'Procesando...',
                    currentStep,
                    steps
                );
                
                if (currentStep >= steps) {
                    clearInterval(interval);
                    resolve();
                }
            }, stepDuration);
        });
    }
}

/**
 * Gestor de formularios con progreso
 */
class FormCreationManager {
    constructor() {
        this.progressManager = new ProgressManager();
    }

    /**
     * Crear formulario desde plantilla con progreso
     */
    async createFormFromTemplate(formData) {
        try {
            const modal = this.progressManager.showProgress('Creando Formulario desde Plantilla');
            
            // Paso 1: Validación
            this.progressManager.updateProgress(20, 'Validando datos del formulario...', 1, 5);
            await this.delay(800);
            
            // Paso 2: Verificar monedas
            this.progressManager.updateProgress(40, 'Verificando costo y monedas disponibles...', 2, 5);
            await this.delay(600);
            
            // Paso 3: Crear estructura
            this.progressManager.updateProgress(60, 'Creando estructura del formulario...', 3, 5);
            await this.delay(1000);
            
            // Paso 4: Agregar campos
            this.progressManager.updateProgress(80, 'Agregando campos al formulario...', 4, 5);
            await this.delay(800);
            
            // Paso 5: Finalizar
            this.progressManager.updateProgress(100, 'Finalizando creación...', 5, 5);
            await this.delay(500);
            
            // Enviar datos al servidor
            const response = await fetch('/api/form-creation-progress/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(formData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.progressManager.showSuccess(
                    result.message || 'Formulario creado exitosamente',
                    result.redirect_url
                );
            } else {
                this.progressManager.showError(result.message || 'Error al crear el formulario');
            }
            
        } catch (error) {
            console.error('Error:', error);
            this.progressManager.showError('Error de conexión. Por favor, intenta nuevamente.');
        }
    }

    /**
     * Delay helper
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Obtener token CSRF
     */
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
}

/**
 * Gestor de botones con loading
 */
class LoadingButton {
    constructor(button) {
        this.button = button;
        this.originalText = button.innerHTML;
        this.originalDisabled = button.disabled;
    }

    /**
     * Mostrar estado de carga
     */
    showLoading(text = 'Procesando...') {
        this.button.disabled = true;
        this.button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </span>
            ${text}
        `;
    }

    /**
     * Ocultar estado de carga
     */
    hideLoading() {
        this.button.disabled = this.originalDisabled;
        this.button.innerHTML = this.originalText;
    }

    /**
     * Mostrar éxito temporalmente
     */
    showSuccess(text = 'Completado', duration = 2000) {
        const originalClass = this.button.className;
        this.button.className = this.button.className.replace(/btn-\w+/, 'btn-success');
        this.button.innerHTML = `
            <i class="fas fa-check me-2"></i>
            ${text}
        `;
        
        setTimeout(() => {
            this.button.className = originalClass;
            this.hideLoading();
        }, duration);
    }

    /**
     * Mostrar error temporalmente
     */
    showError(text = 'Error', duration = 3000) {
        const originalClass = this.button.className;
        this.button.className = this.button.className.replace(/btn-\w+/, 'btn-danger');
        this.button.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${text}
        `;
        
        setTimeout(() => {
            this.button.className = originalClass;
            this.hideLoading();
        }, duration);
    }
}

/**
 * Utilidades globales
 */
window.WPA = {
    ProgressManager,
    FormCreationManager,
    LoadingButton,
    
    // Instancia global del progress manager
    progress: new ProgressManager(),
    
    // Instancia global del form creation manager
    formCreation: new FormCreationManager(),
    
    /**
     * Crear loading button para cualquier botón
     */
    createLoadingButton(selector) {
        const button = document.querySelector(selector);
        return button ? new LoadingButton(button) : null;
    },

    /**
     * Mostrar notificación toast
     */
    showToast(message, type = 'info') {
        // Crear toast si no existe el container
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '1060';
            document.body.appendChild(toastContainer);
        }

        const toastHTML = `
            <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                            data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        const toastElement = toastContainer.lastElementChild;
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        // Remover el toast después de que se oculte
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    },

    /**
     * Confirmar acción con modal
     */
    confirm(message, title = 'Confirmar Acción') {
        return new Promise((resolve) => {
            // Crear modal de confirmación si no existe
            let confirmModal = document.getElementById('confirmModal');
            if (!confirmModal) {
                const modalHTML = `
                    <div class="modal fade" id="confirmModal" tabindex="-1">
                        <div class="modal-dialog modal-dialog-centered">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title" id="confirmModalTitle">Confirmar</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body" id="confirmModalBody">
                                    ¿Estás seguro?
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                        Cancelar
                                    </button>
                                    <button type="button" class="btn btn-primary" id="confirmModalConfirm">
                                        Confirmar
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                document.body.insertAdjacentHTML('beforeend', modalHTML);
                confirmModal = document.getElementById('confirmModal');
            }

            document.getElementById('confirmModalTitle').textContent = title;
            document.getElementById('confirmModalBody').textContent = message;
            
            const modal = new bootstrap.Modal(confirmModal);
            const confirmBtn = document.getElementById('confirmModalConfirm');
            
            // Limpiar event listeners previos
            const newConfirmBtn = confirmBtn.cloneNode(true);
            confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
            
            newConfirmBtn.addEventListener('click', () => {
                modal.hide();
                resolve(true);
            });
            
            confirmModal.addEventListener('hidden.bs.modal', () => {
                resolve(false);
            }, { once: true });
            
            modal.show();
        });
    }
};

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('WPA Progress System initialized');
});
