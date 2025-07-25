/**
 * PECO Panel de Control - Aplicación Principal
 * Inicializa y coordina todos los módulos de la aplicación
 */

class PECOApp {
    constructor() {
        this.isInitialized = false;
        this.modules = {};
        this.init();
    }

    async init() {
        try {
            // Mostrar contenido principal con animación
            this.showMainContent();
            
            // Esperar a que los módulos se inicialicen
            await this.waitForModules();
            
            // Configurar eventos globales
            this.setupGlobalEvents();
            
            // Verificar estado del sistema
            await this.checkSystemStatus();
            
            this.isInitialized = true;
            console.log('PECO App initialized successfully');
            
        } catch (error) {
            console.error('Error initializing PECO App:', error);
            this.handleInitializationError(error);
        }
    }

    showMainContent() {
        const mainContent = document.getElementById('main-content');
        if (mainContent) {
            mainContent.classList.add('visible');
        }
    }

    async waitForModules() {
        // Esperar a que los módulos estén disponibles
        const maxWait = 5000; // 5 segundos máximo
        const startTime = Date.now();
        
        while (Date.now() - startTime < maxWait) {
            this.modules = {
                theme: window.themeManager,
                notifications: window.notificationManager,
                terminal: window.terminal,
                forms: window.formManager
            };
            
            // Verificar si todos los módulos están cargados
            const allLoaded = Object.values(this.modules).every(module => module !== undefined);
            if (allLoaded) {
                console.log('All modules loaded successfully');
                return;
            }
            
            // Esperar un poco antes de verificar de nuevo
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        console.warn('Some modules may not have loaded properly:', this.modules);
    }

    setupGlobalEvents() {
        // Manejar errores globales
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            if (this.modules.notifications) {
                this.modules.notifications.error('Error inesperado en la aplicación', 
                    { error: event.error?.message });
            }
        });

        // Manejar errores de promesas no capturadas
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            if (this.modules.notifications) {
                this.modules.notifications.error('Error de conexión o procesamiento', 
                    { error: event.reason?.message });
            }
        });

        // Manejar cambios de conectividad
        window.addEventListener('online', () => {
            if (this.modules.notifications) {
                this.modules.notifications.success('Conexión restaurada');
            }
        });

        window.addEventListener('offline', () => {
            if (this.modules.notifications) {
                this.modules.notifications.warning('Sin conexión a internet');
            }
        });
    }

    async checkSystemStatus() {
        try {
            if (this.modules.terminal) {
                this.modules.terminal.print('Verificando estado del sistema...', 'info');
            }
            
            const response = await fetch('/validar-sistema');
            const data = await response.json();

            if (response.ok && data.success) {
                const systemData = data.data;

                if (systemData.system_status === 'ok') {
                    this.modules.terminal?.print('✓ Sistema validado correctamente', 'success');
                } else if (systemData.system_status === 'warning') {
                    this.modules.terminal?.print('⚠ Sistema funcional con advertencias', 'warning');
                    if (systemData.issues) {
                        systemData.issues.forEach(issue => {
                            this.modules.terminal?.print(`  - ${issue}`, 'warning');
                        });
                    }
                }

                // Mostrar capacidades del sistema
                if (systemData.latex_available) {
                    this.modules.terminal?.print('✓ LaTeX disponible para generación de PDFs', 'info');
                } else {
                    this.modules.terminal?.print('✗ LaTeX no disponible - PDFs no se pueden generar', 'warning',
                        null,
                        ['Instale MiKTeX o TeX Live para habilitar generación de PDFs']
                    );
                }

                if (systemData.data_integrity && systemData.data_integrity.success) {
                    this.modules.terminal?.print('✓ Integridad de datos verificada', 'info');
                } else if (systemData.data_integrity) {
                    this.modules.terminal?.print(`⚠ Problemas de integridad: ${systemData.data_integrity.message}`, 'warning');
                }

            } else {
                const message = data.message || 'Error validando sistema';
                const errorCode = data.error_code ? ` (${data.error_code})` : '';
                this.modules.terminal?.print(message + errorCode, 'error', data.details, data.suggestions);
            }

        } catch (error) {
            this.modules.terminal?.print('Error verificando estado del sistema', 'warning',
                { error: error.message },
                ['El sistema puede funcionar con limitaciones', 'Algunas funciones pueden no estar disponibles']
            );
        }
    }

    handleInitializationError(error) {
        console.error('Failed to initialize PECO App:', error);
        
        // Mostrar error básico si los módulos no están disponibles
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-3 rounded-lg shadow-lg z-50';
        errorDiv.innerHTML = `
            <div class="flex items-center gap-2">
                <span>⚠</span>
                <span>Error inicializando la aplicación</span>
            </div>
        `;
        document.body.appendChild(errorDiv);
        
        setTimeout(() => errorDiv.remove(), 10000);
    }

    // Métodos públicos para interactuar con la aplicación
    getModule(name) {
        return this.modules[name];
    }

    isReady() {
        return this.isInitialized;
    }

    async restart() {
        console.log('Restarting PECO App...');
        this.isInitialized = false;
        await this.init();
    }
}

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.pecoApp = new PECOApp();
});

// Exponer la aplicación globalmente para debugging
window.PECO = {
    app: () => window.pecoApp,
    modules: () => window.pecoApp?.modules || {},
    restart: () => window.pecoApp?.restart()
};