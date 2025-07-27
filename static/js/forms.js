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
            <div class="space-y-8">
                <!-- General Data Section -->
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h3 class="text-lg font-semibold mb-4 text-gray-800">Datos Generales</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium mb-2">Mes (ISO Format)</label>
                            <input type="month" id="res-mes-iso" value="${config.mes_iso || ''}" 
                                   class="input-field" required>
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-2">Título Base</label>
                            <input type="text" id="res-titulo-base" value="${config.titulo_base || ''}" 
                                   class="input-field" placeholder="Ej: Presupuesto mensual" required>
                        </div>
                    </div>
                </div>

                <!-- VISTO Section -->
                <div class="bg-blue-50 p-4 rounded-lg">
                    <h3 class="text-lg font-semibold mb-4 text-blue-800">VISTO</h3>
                    <div>
                        <label class="block text-sm font-medium mb-2">Contenido del VISTO</label>
                        <textarea id="res-visto" rows="3" class="input-field" 
                                  placeholder="Descripción de la necesidad o situación que motiva la resolución..."
                                  required>${config.visto || ''}</textarea>
                    </div>
                </div>

                <!-- CONSIDERANDO Section -->
                <div class="bg-green-50 p-4 rounded-lg">
                    <h3 class="text-lg font-semibold mb-4 text-green-800">CONSIDERANDO</h3>
                    <div id="considerandos-container">
                        ${this.createListItems(config.considerandos || [], 'considerandos')}
                    </div>
                    <button type="button" onclick="window.formManager.addListItem('considerandos-container', 'considerandos')" 
                            class="mt-3 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors">
                        + Agregar Considerando
                    </button>
                </div>

                <!-- ARTICULOS Section -->
                <div class="bg-yellow-50 p-4 rounded-lg">
                    <h3 class="text-lg font-semibold mb-4 text-yellow-800">ARTÍCULOS</h3>
                    <div id="articulos-container">
                        ${this.createListItems(config.articulos || [], 'articulos')}
                    </div>
                    <button type="button" onclick="window.formManager.addListItem('articulos-container', 'articulos')" 
                            class="mt-3 px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors">
                        + Agregar Artículo
                    </button>
                </div>

                <!-- ANEXO Section -->
                <div class="bg-purple-50 p-4 rounded-lg">
                    <h3 class="text-lg font-semibold mb-4 text-purple-800">ANEXO</h3>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium mb-2">Título del Anexo</label>
                            <input type="text" id="res-anexo-titulo" value="${config.anexo?.titulo || ''}" 
                                   class="input-field" placeholder="Ej: Detalle del presupuesto mensual solicitado">
                        </div>
                        
                        <div>
                            <h4 class="text-md font-medium mb-2 text-purple-700">Items del Anexo</h4>
                            <div id="anexo-items-container">
                                ${this.createAnexoItems(config.anexo?.items || [], 'items')}
                            </div>
                            <button type="button" onclick="window.formManager.addAnexoItem('anexo-items-container', 'items')" 
                                    class="mt-2 px-3 py-1 bg-purple-600 text-white rounded text-sm hover:bg-purple-700 transition-colors">
                                + Agregar Item
                            </button>
                        </div>

                        <div>
                            <h4 class="text-md font-medium mb-2 text-purple-700">Penalizaciones</h4>
                            <div id="anexo-penalizaciones-container">
                                ${this.createAnexoItems(config.anexo?.penalizaciones || [], 'penalizaciones')}
                            </div>
                            <button type="button" onclick="window.formManager.addAnexoItem('anexo-penalizaciones-container', 'penalizaciones')" 
                                    class="mt-2 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700 transition-colors">
                                + Agregar Penalización
                            </button>
                        </div>

                        <div>
                            <label class="block text-sm font-medium mb-2">Nota Final</label>
                            <textarea id="res-anexo-nota" rows="2" class="input-field" 
                                      placeholder="Nota final del anexo...">${config.anexo?.nota_final || ''}</textarea>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    createListItems(items, type) {
        if (!items || items.length === 0) {
            return this.getEmptyListItem(type);
        }

        return items.map((item, index) => {
            if (type === 'considerandos') {
                return this.createConsiderandoItem(item, index);
            } else if (type === 'articulos') {
                return this.createArticuloItem(item, index);
            }
        }).join('');
    }

    createConsiderandoItem(item, index) {
        const isGastoAnterior = item.tipo === 'gasto_anterior';
        return `
            <div class="considerando-item border border-gray-200 p-3 rounded mb-3 bg-white">
                <div class="flex justify-between items-start mb-2">
                    <label class="text-sm font-medium">Considerando ${index + 1}</label>
                    <button type="button" onclick="window.formManager.removeListItem(this)" 
                            class="text-red-600 hover:text-red-800 text-sm">
                        ✕ Eliminar
                    </button>
                </div>
                <div class="mb-2">
                    <select class="considerando-tipo input-field text-sm" onchange="window.formManager.toggleConsiderandoType(this)">
                        <option value="texto" ${!isGastoAnterior ? 'selected' : ''}>Texto</option>
                        <option value="gasto_anterior" ${isGastoAnterior ? 'selected' : ''}>Gasto Anterior</option>
                    </select>
                </div>
                <div class="considerando-content">
                    ${isGastoAnterior ? 
                        `<div class="grid grid-cols-2 gap-2">
                            <input type="text" class="considerando-descripcion input-field text-sm" 
                                   placeholder="Descripción" value="${item.descripcion || ''}" required>
                            <input type="number" class="considerando-monto input-field text-sm" 
                                   placeholder="Monto" value="${item.monto || ''}" required>
                         </div>` :
                        `<textarea class="considerando-contenido input-field text-sm" rows="2" 
                                   placeholder="Contenido del considerando..." required>${item.contenido || ''}</textarea>`
                    }
                </div>
            </div>
        `;
    }

    createArticuloItem(item, index) {
        return `
            <div class="articulo-item border border-gray-200 p-3 rounded mb-3 bg-white">
                <div class="flex justify-between items-start mb-2">
                    <label class="text-sm font-medium">Artículo ${index + 1}</label>
                    <button type="button" onclick="window.formManager.removeListItem(this)" 
                            class="text-red-600 hover:text-red-800 text-sm">
                        ✕ Eliminar
                    </button>
                </div>
                <textarea class="articulo-contenido input-field text-sm" rows="2" 
                          placeholder="Contenido del artículo..." required>${item || ''}</textarea>
            </div>
        `;
    }

    createAnexoItems(items, type) {
        if (!items || items.length === 0) {
            return this.getEmptyAnexoItem(type);
        }

        return items.map((item, index) => this.createAnexoItem(item, index, type)).join('');
    }

    createAnexoItem(item, index, type) {
        const isNegative = type === 'penalizaciones';
        return `
            <div class="anexo-item border border-gray-200 p-3 rounded mb-2 bg-white">
                <div class="flex justify-between items-start mb-2">
                    <label class="text-sm font-medium">${isNegative ? 'Penalización' : 'Item'} ${index + 1}</label>
                    <button type="button" onclick="window.formManager.removeListItem(this)" 
                            class="text-red-600 hover:text-red-800 text-sm">
                        ✕ Eliminar
                    </button>
                </div>
                <div class="grid grid-cols-2 gap-2">
                    <input type="text" class="anexo-categoria input-field text-sm" 
                           placeholder="Categoría" value="${item.categoria || ''}" required>
                    <input type="number" class="anexo-monto input-field text-sm" 
                           placeholder="Monto${isNegative ? ' (será negativo)' : ''}" 
                           value="${Math.abs(parseFloat(item.monto) || 0)}" required>
                </div>
            </div>
        `;
    }

    getEmptyListItem(type) {
        if (type === 'considerandos') {
            return this.createConsiderandoItem({ tipo: 'texto', contenido: '' }, 0);
        } else if (type === 'articulos') {
            return this.createArticuloItem('', 0);
        }
        return '';
    }

    getEmptyAnexoItem(type) {
        return this.createAnexoItem({ categoria: '', monto: '' }, 0, type);
    }

    toggleConsiderandoType(selectElement) {
        const container = selectElement.closest('.considerando-item');
        const contentDiv = container.querySelector('.considerando-content');
        const tipo = selectElement.value;
        
        if (tipo === 'gasto_anterior') {
            contentDiv.innerHTML = `
                <div class="grid grid-cols-2 gap-2">
                    <input type="text" class="considerando-descripcion input-field text-sm" 
                           placeholder="Descripción" required>
                    <input type="number" class="considerando-monto input-field text-sm" 
                           placeholder="Monto" required>
                </div>
            `;
        } else {
            contentDiv.innerHTML = `
                <textarea class="considerando-contenido input-field text-sm" rows="2" 
                          placeholder="Contenido del considerando..." required></textarea>
            `;
        }
    }

    addListItem(containerId, key) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const existingItems = container.querySelectorAll(`.${key.slice(0, -1)}-item`);
        const newIndex = existingItems.length;

        let newItemHtml = '';
        if (key === 'considerandos') {
            newItemHtml = this.createConsiderandoItem({ tipo: 'texto', contenido: '' }, newIndex);
        } else if (key === 'articulos') {
            newItemHtml = this.createArticuloItem('', newIndex);
        }

        if (newItemHtml) {
            container.insertAdjacentHTML('beforeend', newItemHtml);
            this.updateItemNumbers(container, key);
            
            // Focus on the new item's first input
            const newItem = container.lastElementChild;
            const firstInput = newItem.querySelector('input, textarea');
            if (firstInput) {
                firstInput.focus();
            }
        }
    }

    addAnexoItem(containerId, key) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const existingItems = container.querySelectorAll('.anexo-item');
        const newIndex = existingItems.length;
        const newItemHtml = this.createAnexoItem({ categoria: '', monto: '' }, newIndex, key);

        container.insertAdjacentHTML('beforeend', newItemHtml);
        this.updateAnexoItemNumbers(container, key);
        
        // Focus on the new item's first input
        const newItem = container.lastElementChild;
        const firstInput = newItem.querySelector('input');
        if (firstInput) {
            firstInput.focus();
        }
    }

    removeListItem(button) {
        const item = button.closest('.considerando-item, .articulo-item, .anexo-item');
        const container = item.parentElement;
        
        // Don't allow removing the last item
        const items = container.querySelectorAll('.considerando-item, .articulo-item, .anexo-item');
        if (items.length <= 1) {
            window.notificationManager?.warning('Debe mantener al menos un elemento');
            return;
        }

        item.remove();
        
        // Update numbering
        if (container.id.includes('considerandos')) {
            this.updateItemNumbers(container, 'considerandos');
        } else if (container.id.includes('articulos')) {
            this.updateItemNumbers(container, 'articulos');
        } else if (container.id.includes('anexo')) {
            const key = container.id.includes('penalizaciones') ? 'penalizaciones' : 'items';
            this.updateAnexoItemNumbers(container, key);
        }
    }

    updateItemNumbers(container, key) {
        const items = container.querySelectorAll(`.${key.slice(0, -1)}-item`);
        items.forEach((item, index) => {
            const label = item.querySelector('label');
            if (label) {
                const itemType = key === 'considerandos' ? 'Considerando' : 'Artículo';
                label.textContent = `${itemType} ${index + 1}`;
            }
        });
    }

    updateAnexoItemNumbers(container, key) {
        const items = container.querySelectorAll('.anexo-item');
        items.forEach((item, index) => {
            const label = item.querySelector('label');
            if (label) {
                const itemType = key === 'penalizaciones' ? 'Penalización' : 'Item';
                label.textContent = `${itemType} ${index + 1}`;
            }
        });
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
            
            // Recopilar datos del formulario con nueva estructura
            const data = this.collectFormData();

            // Validar datos del formulario
            const validation = this.validateResolutionData(data);
            if (!validation.isValid) {
                window.notificationManager?.error('Errores en el formulario', 
                    { errores: validation.errors.join(', ') });
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

    collectFormData() {
        // Datos generales
        const mesIso = document.getElementById('res-mes-iso')?.value || '';
        const tituloBase = document.getElementById('res-titulo-base')?.value || '';
        const visto = document.getElementById('res-visto')?.value || '';

        // Recopilar considerandos
        const considerandos = this.collectConsiderandos();

        // Recopilar artículos
        const articulos = this.collectArticulos();

        // Recopilar anexo
        const anexo = this.collectAnexo();

        return {
            mes_iso: mesIso,
            titulo_base: tituloBase,
            visto: visto,
            considerandos: considerandos,
            articulos: articulos,
            anexo: anexo
        };
    }

    collectConsiderandos() {
        const considerandos = [];
        const items = document.querySelectorAll('#considerandos-container .considerando-item');
        
        items.forEach(item => {
            const tipo = item.querySelector('.considerando-tipo')?.value || 'texto';
            
            if (tipo === 'gasto_anterior') {
                const descripcion = item.querySelector('.considerando-descripcion')?.value || '';
                const monto = item.querySelector('.considerando-monto')?.value || '';
                
                if (descripcion.trim() && monto.trim()) {
                    considerandos.push({
                        tipo: 'gasto_anterior',
                        descripcion: descripcion.trim(),
                        monto: monto.trim()
                    });
                }
            } else {
                const contenido = item.querySelector('.considerando-contenido')?.value || '';
                
                if (contenido.trim()) {
                    considerandos.push({
                        tipo: 'texto',
                        contenido: contenido.trim()
                    });
                }
            }
        });
        
        return considerandos;
    }

    collectArticulos() {
        const articulos = [];
        const items = document.querySelectorAll('#articulos-container .articulo-item');
        
        items.forEach(item => {
            const contenido = item.querySelector('.articulo-contenido')?.value || '';
            
            if (contenido.trim()) {
                articulos.push(contenido.trim());
            }
        });
        
        return articulos;
    }

    collectAnexo() {
        const anexoTitulo = document.getElementById('res-anexo-titulo')?.value || '';
        const anexoNota = document.getElementById('res-anexo-nota')?.value || '';

        // Recopilar items del anexo
        const items = [];
        const itemElements = document.querySelectorAll('#anexo-items-container .anexo-item');
        
        itemElements.forEach(item => {
            const categoria = item.querySelector('.anexo-categoria')?.value || '';
            const monto = item.querySelector('.anexo-monto')?.value || '';
            
            if (categoria.trim() && monto.trim()) {
                items.push({
                    categoria: categoria.trim(),
                    monto: monto.trim()
                });
            }
        });

        // Recopilar penalizaciones
        const penalizaciones = [];
        const penalizacionElements = document.querySelectorAll('#anexo-penalizaciones-container .anexo-item');
        
        penalizacionElements.forEach(item => {
            const categoria = item.querySelector('.anexo-categoria')?.value || '';
            const monto = item.querySelector('.anexo-monto')?.value || '';
            
            if (categoria.trim() && monto.trim()) {
                // Ensure penalizaciones are negative
                const montoValue = parseFloat(monto);
                const finalMonto = montoValue > 0 ? `-${monto}` : monto;
                
                penalizaciones.push({
                    categoria: categoria.trim(),
                    monto: finalMonto
                });
            }
        });

        return {
            titulo: anexoTitulo.trim(),
            items: items,
            penalizaciones: penalizaciones,
            nota_final: anexoNota.trim()
        };
    }

    validateResolutionData(data) {
        const errors = [];

        // Validar mes ISO
        if (!data.mes_iso || data.mes_iso.trim() === '') {
            errors.push('El mes en formato ISO es requerido');
        } else {
            // Validar formato ISO (YYYY-MM)
            const isoRegex = /^\d{4}-\d{2}$/;
            if (!isoRegex.test(data.mes_iso)) {
                errors.push('El mes debe estar en formato ISO (YYYY-MM)');
            }
        }

        if (!data.titulo_base || data.titulo_base.trim() === '') {
            errors.push('El título base es requerido');
        }

        if (!data.visto || data.visto.trim() === '') {
            errors.push('El contenido del VISTO es requerido');
        }

        // Validar considerandos
        if (!data.considerandos || data.considerandos.length === 0) {
            errors.push('Debe incluir al menos un considerando');
        } else {
            data.considerandos.forEach((considerando, index) => {
                if (considerando.tipo === 'gasto_anterior') {
                    if (!considerando.descripcion || considerando.descripcion.trim() === '') {
                        errors.push(`Considerando ${index + 1}: La descripción es requerida`);
                    }
                    if (!considerando.monto || isNaN(parseFloat(considerando.monto)) || parseFloat(considerando.monto) <= 0) {
                        errors.push(`Considerando ${index + 1}: El monto debe ser un número mayor a 0`);
                    }
                } else {
                    if (!considerando.contenido || considerando.contenido.trim() === '') {
                        errors.push(`Considerando ${index + 1}: El contenido es requerido`);
                    }
                }
            });
        }

        // Validar artículos
        if (!data.articulos || data.articulos.length === 0) {
            errors.push('Debe incluir al menos un artículo');
        }

        // Validar anexo items (montos numéricos)
        if (data.anexo && data.anexo.items) {
            data.anexo.items.forEach((item, index) => {
                if (item.monto && (isNaN(parseFloat(item.monto)) || parseFloat(item.monto) <= 0)) {
                    errors.push(`Item del anexo ${index + 1}: El monto debe ser un número mayor a 0`);
                }
            });
        }

        // Validar penalizaciones (montos numéricos)
        if (data.anexo && data.anexo.penalizaciones) {
            data.anexo.penalizaciones.forEach((penalizacion, index) => {
                if (penalizacion.monto && isNaN(parseFloat(penalizacion.monto))) {
                    errors.push(`Penalización ${index + 1}: El monto debe ser un número válido`);
                }
            });
        }

        return {
            isValid: errors.length === 0,
            errors: errors
        };
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