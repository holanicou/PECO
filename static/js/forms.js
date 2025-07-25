/**
 * PECO Panel de Control - Gestión de Formularios
 * Maneja la validación y envío de formularios
 */

class FormManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupDateFields();
        this.setupFormHandlers();
        this.setupValidation();
    }

    setupDateFields() {
        const today = new Date().toISOString().split('T')[0];
        const fechaGasto = document.getElementById('fecha-gasto');
        const fechaInversion = document.getElementById('fecha-inversion');
        
        if (fechaGasto) fechaGasto.value = today;
        if (fechaInversion) fechaInversion.value = today;
    }

    setupFormHandlers() {
        // Formulario de gastos
        const formRegistrar = document.getElementById('form-registrar');
        if (formRegistrar) {
            formRegistrar.addEventListener('submit', (e) => this.handleGastoSubmit(e));
        }

        // Formulario de inversiones
        const formInvertir = document.getElementById('form-invertir');
        if (formInvertir) {
            formInvertir.addEventListener('submit', (e) => this.handleInversionSubmit(e));
        }

        // Botones de acciones generales
        const btnAnalizar = document.getElementById('btn-analizar');
        if (btnAnalizar) {
            btnAnalizar.addEventListener('click', () => this.handleAnalizar());
        }

        const btnEditarRes = document.getElementById('btn-editar-res');
        if (btnEditarRes) {
            btnEditarRes.addEventListener('click', () => this.handleEditarResolucion());
        }
    }

    setupValidation() {
        // Validación en tiempo real para campos numéricos
        const montoFields = document.querySelectorAll('#monto-gasto, #monto-inversion');
        montoFields.forEach(field => {
            field.addEventListener('input', (e) => this.validateNumericField(e.target));
            field.addEventListener('blur', (e) => this.validateNumericField(e.target));
        });

        // Validación para campos de texto requeridos
        const requiredFields = document.querySelectorAll('input[required], select[required]');
        requiredFields.forEach(field => {
            field.addEventListener('blur', (e) => this.validateRequiredField(e.target));
        });
    }

    validateNumericField(field) {
        const value = parseFloat(field.value);
        const isValid = !isNaN(value) && value > 0;
        
        this.setFieldValidation(field, isValid, 
            isValid ? null : 'Debe ser un número mayor a 0');
        
        return isValid;
    }

    validateRequiredField(field) {
        const isValid = field.value.trim() !== '';
        
        this.setFieldValidation(field, isValid, 
            isValid ? null : 'Este campo es requerido');
        
        return isValid;
    }

    setFieldValidation(field, isValid, errorMessage = null) {
        field.classList.remove('field-error', 'field-success');
        
        if (isValid) {
            field.classList.add('field-success');
        } else if (errorMessage) {
            field.classList.add('field-error');
        }
    }

    async handleGastoSubmit(e) {
        e.preventDefault();
        
        const form = e.target;
        const formData = new FormData(form);
        
        const data = {
            monto: formData.get('monto'),
            categoria: formData.get('categoria'),
            desc: formData.get('desc')
        };

        // Validar datos
        if (!this.validateGastoData(data)) {
            return;
        }

        await this.submitCommand('registrar', data, form);
    }

    async handleInversionSubmit(e) {
        e.preventDefault();
        
        const form = e.target;
        const formData = new FormData(form);
        
        const data = {
            activo: formData.get('activo'),
            tipo: formData.get('tipo'),
            monto: formData.get('monto')
        };

        // Validar datos
        if (!this.validateInversionData(data)) {
            return;
        }

        await this.submitCommand('invertir', data, form);
    }

    async handleAnalizar() {
        const now = new Date();
        const data = {
            mes: now.getMonth() + 1,
            año: now.getFullYear()
        };

        await this.submitCommand('analizar', data);
    }

    async handleEditarResolucion() {
        try {
            window.terminal?.print('Cargando editor de resolución...', 'info');
            
            // Cargar configuración actual
            const response = await fetch('/get-config');
            const config = await response.json();
            
            if (response.ok && config.success) {
                this.showResolutionModal(config.data || config);
            } else {
                throw new Error(config.message || 'Error cargando configuración');
            }
            
        } catch (error) {
            window.terminal?.print(`Error cargando editor: ${error.message}`, 'error');
            window.notificationManager?.error('Error cargando editor de resolución', 
                { error: error.message });
        }
    }

    validateGastoData(data) {
        const errors = [];
        
        if (!data.monto || isNaN(parseFloat(data.monto)) || parseFloat(data.monto) <= 0) {
            errors.push('Monto debe ser un número mayor a 0');
        }
        
        if (!data.categoria || data.categoria.trim() === '') {
            errors.push('Categoría es requerida');
        }
        
        if (!data.desc || data.desc.trim() === '') {
            errors.push('Descripción es requerida');
        }

        if (errors.length > 0) {
            window.notificationManager?.error('Errores en el formulario', 
                { errores: errors.join(', ') });
            return false;
        }
        
        return true;
    }

    validateInversionData(data) {
        const errors = [];
        
        if (!data.activo || data.activo.trim() === '') {
            errors.push('Activo es requerido');
        }
        
        if (!data.tipo || !['Compra', 'Venta'].includes(data.tipo)) {
            errors.push('Tipo debe ser Compra o Venta');
        }
        
        if (!data.monto || isNaN(parseFloat(data.monto)) || parseFloat(data.monto) <= 0) {
            errors.push('Monto debe ser un número mayor a 0');
        }

        if (errors.length > 0) {
            window.notificationManager?.error('Errores en el formulario', 
                { errores: errors.join(', ') });
            return false;
        }
        
        return true;
    }

    async submitCommand(comando, args, form = null) {
        const submitButton = form?.querySelector('button[type="submit"]');
        
        try {
            // Mostrar estado de carga
            this.setFormLoading(form, true);
            window.terminal?.print(`Ejecutando: ${comando}`, 'command');
            
            const response = await fetch('/ejecutar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ comando, args })
            });

            const result = await response.json();
            
            if (response.ok && result.success) {
                window.terminal?.print(result.message || result.salida, 'success');
                window.notificationManager?.success(result.message || 'Operación completada');
                
                // Limpiar formulario si fue exitoso
                if (form) {
                    form.reset();
                    this.setupDateFields(); // Restaurar fechas
                }
                
            } else {
                const message = result.message || result.salida || 'Error desconocido';
                window.terminal?.print(message, 'error', result.details, result.suggestions);
                window.notificationManager?.error(message, result.details, result.suggestions);
            }
            
        } catch (error) {
            const errorMsg = `Error de conexión: ${error.message}`;
            window.terminal?.print(errorMsg, 'error');
            window.notificationManager?.error(errorMsg);
            
        } finally {
            this.setFormLoading(form, false);
        }
    }

    setFormLoading(form, isLoading) {
        if (!form) return;

        const inputs = form.querySelectorAll('input, select, button');
        inputs.forEach(input => {
            input.disabled = isLoading;
            
            if (input.tagName === 'BUTTON' && input.type === 'submit') {
                if (isLoading) {
                    input.classList.add('btn-loading');
                    input.dataset.originalText = input.innerHTML;
                    input.innerHTML = 'Procesando...';
                } else {
                    input.classList.remove('btn-loading');
                    input.innerHTML = input.dataset.originalText || input.innerHTML;
                }
            }
        });
    }

    showResolutionModal(config) {
        const modal = document.getElementById('modal-resolucion');
        const container = document.getElementById('resolucion-form-container');
        
        if (!modal || !container) return;

        // Generar formulario dinámico basado en la configuración
        container.innerHTML = this.generateResolutionForm(config);
        
        // Mostrar modal
        modal.classList.remove('hidden');
        
        // Configurar eventos del modal
        this.setupModalEvents(config);
    }

    generateResolutionForm(config) {
        return `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <label class="block text-sm font-medium mb-2">Título de la Resolución</label>
                    <input type="text" id="res-titulo" value="${config.titulo || ''}" 
                           class="input-field" placeholder="Ej: Presupuesto mensual de enero">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Mes</label>
                    <input type="text" id="res-mes" value="${config.mes_nombre || ''}" 
                           class="input-field" placeholder="Ej: enero">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Mes Anterior</label>
                    <input type="text" id="res-mes-anterior" value="${config.mes_anterior || ''}" 
                           class="input-field" placeholder="Ej: diciembre">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Año</label>
                    <input type="number" id="res-año" value="${config.año || new Date().getFullYear()}" 
                           class="input-field">
                </div>
            </div>
            <div class="mt-6">
                <label class="block text-sm font-medium mb-2">Contenido Adicional</label>
                <textarea id="res-contenido" rows="4" class="input-field" 
                          placeholder="Contenido adicional para la resolución...">${config.contenido || ''}</textarea>
            </div>
        `;
    }

    setupModalEvents(config) {
        const modal = document.getElementById('modal-resolucion');
        const btnCerrar = document.getElementById('btn-cerrar-modal');
        const btnGuardar = document.getElementById('btn-guardar-generar');

        // Cerrar modal
        btnCerrar?.addEventListener('click', () => {
            modal.classList.add('hidden');
        });

        // Guardar y generar
        btnGuardar?.addEventListener('click', () => this.handleSaveAndGenerate());

        // Cerrar con ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
                modal.classList.add('hidden');
            }
        });
    }

    async handleSaveAndGenerate() {
        try {
            const modal = document.getElementById('modal-resolucion');
            const btnGuardar = document.getElementById('btn-guardar-generar');
            
            // Recopilar datos del formulario
            const data = {
                titulo: document.getElementById('res-titulo')?.value || '',
                mes_nombre: document.getElementById('res-mes')?.value || '',
                mes_anterior: document.getElementById('res-mes-anterior')?.value || '',
                año: parseInt(document.getElementById('res-año')?.value) || new Date().getFullYear(),
                contenido: document.getElementById('res-contenido')?.value || ''
            };

            // Validar datos requeridos
            if (!data.titulo || !data.mes_nombre) {
                window.notificationManager?.error('Título y mes son requeridos');
                return;
            }

            // Mostrar estado de carga
            btnGuardar.disabled = true;
            btnGuardar.innerHTML = 'Generando PDF...';

            // Guardar configuración
            await this.saveConfig(data);
            
            // Generar PDF
            await this.generatePDF(data);
            
            // Cerrar modal
            modal.classList.add('hidden');
            
        } catch (error) {
            window.terminal?.print(`Error: ${error.message}`, 'error');
            window.notificationManager?.error('Error generando resolución', 
                { error: error.message });
        } finally {
            const btnGuardar = document.getElementById('btn-guardar-generar');
            btnGuardar.disabled = false;
            btnGuardar.innerHTML = 'Guardar y Generar PDF';
        }
    }

    async saveConfig(data) {
        const response = await fetch('/save-config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || 'Error guardando configuración');
        }
    }

    async generatePDF(data) {
        const response = await fetch('/generar-pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (response.ok && result.success) {
            window.terminal?.print(result.message, 'success');
            window.notificationManager?.success('PDF generado exitosamente');
        } else {
            throw new Error(result.message || 'Error generando PDF');
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.formManager = new FormManager();
});