/**
 * PECO Panel de Control - Terminal de Salida
 * Maneja la visualización de mensajes en la terminal
 */

class Terminal {
    constructor() {
        this.output = null;
        this.init();
    }

    init() {
        this.output = document.getElementById('terminal-output');
        this.setupClearButton();
        this.welcome();
    }

    welcome() {
        this.print('Bienvenido al panel de control de PECO.');
        this.print('Servidor local conectado. Esperando acciones...');
    }

    print(text, type = 'info', details = null, suggestions = null) {
        if (!this.output) return;

        const lines = String(text).split('\n');
        lines.forEach(line => {
            if (line.trim() === '') return;
            
            const p = document.createElement('p');
            p.style.opacity = 0;
            
            let prefix = '>';
            let textColor = 'dark:text-slate-300 text-slate-600';
            let bgColor = '';

            switch (type) {
                case 'command':
                    prefix = '$';
                    textColor = 'dark:text-cyan-400 text-cyan-600';
                    break;
                case 'success':
                    prefix = '[OK]';
                    textColor = 'dark:text-emerald-400 text-emerald-600';
                    bgColor = 'bg-emerald-50 dark:bg-emerald-900/20 border-l-2 border-emerald-500 pl-2';
                    break;
                case 'error':
                    prefix = '[ERROR]';
                    textColor = 'dark:text-red-400 text-red-500';
                    bgColor = 'bg-red-50 dark:bg-red-900/20 border-l-2 border-red-500 pl-2';
                    break;
                case 'warning':
                    prefix = '[WARN]';
                    textColor = 'dark:text-yellow-400 text-yellow-600';
                    bgColor = 'bg-yellow-50 dark:bg-yellow-900/20 border-l-2 border-yellow-500 pl-2';
                    break;
            }

            p.innerHTML = `<span class="dark:text-green-400 text-green-600 flex-shrink-0">${prefix}&nbsp;</span> <span class="${textColor}">${this.escapeHtml(line)}</span>`;
            p.className = `flex ${bgColor} py-1 rounded`;
            
            this.output.appendChild(p);
            setTimeout(() => p.style.opacity = 1, 10);
        });

        // Add details if provided
        if (details && (type === 'error' || type === 'warning')) {
            this.printDetails(details);
        }

        // Add suggestions if provided
        if (suggestions && Array.isArray(suggestions) && suggestions.length > 0) {
            this.printSuggestions(suggestions);
        }

        this.scrollToBottom();
    }

    printDetails(details) {
        const detailsContainer = document.createElement('div');
        detailsContainer.className = 'ml-4 mt-1 p-2 bg-slate-100 dark:bg-slate-800 rounded text-xs border-l-2 border-slate-300 dark:border-slate-600';
        detailsContainer.style.opacity = 0;

        const detailsTitle = document.createElement('div');
        detailsTitle.className = 'font-semibold text-slate-600 dark:text-slate-400 mb-1';
        detailsTitle.textContent = 'Detalles del error:';
        detailsContainer.appendChild(detailsTitle);

        if (typeof details === 'object') {
            Object.entries(details).forEach(([key, value]) => {
                const detailLine = document.createElement('div');
                detailLine.className = 'text-slate-500 dark:text-slate-400';
                detailLine.innerHTML = `<strong>${key}:</strong> ${this.escapeHtml(String(value))}`;
                detailsContainer.appendChild(detailLine);
            });
        } else {
            const detailLine = document.createElement('div');
            detailLine.className = 'text-slate-500 dark:text-slate-400';
            detailLine.textContent = String(details);
            detailsContainer.appendChild(detailLine);
        }

        this.output.appendChild(detailsContainer);
        setTimeout(() => detailsContainer.style.opacity = 1, 20);
    }

    printSuggestions(suggestions) {
        const suggestionsContainer = document.createElement('div');
        suggestionsContainer.className = 'ml-4 mt-1 p-2 bg-blue-50 dark:bg-blue-900/20 rounded text-xs border-l-2 border-blue-400';
        suggestionsContainer.style.opacity = 0;

        const suggestionsTitle = document.createElement('div');
        suggestionsTitle.className = 'font-semibold text-blue-600 dark:text-blue-400 mb-1 flex items-center gap-1';
        suggestionsTitle.innerHTML = '💡 Sugerencias:';
        suggestionsContainer.appendChild(suggestionsTitle);

        suggestions.forEach(suggestion => {
            const suggestionLine = document.createElement('div');
            suggestionLine.className = 'text-blue-600 dark:text-blue-300 flex items-start gap-2 mt-1';
            suggestionLine.innerHTML = `<span class="text-blue-400">•</span> <span>${this.escapeHtml(suggestion)}</span>`;
            suggestionsContainer.appendChild(suggestionLine);
        });

        this.output.appendChild(suggestionsContainer);
        setTimeout(() => suggestionsContainer.style.opacity = 1, 30);
    }

    escapeHtml(text) {
        return text.replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    scrollToBottom() {
        if (this.output) {
            this.output.scrollTo({ top: this.output.scrollHeight, behavior: 'smooth' });
        }
    }

    clear() {
        if (this.output) {
            this.output.innerHTML = '';
            this.welcome();
        }
    }

    setupClearButton() {
        const clearBtn = document.getElementById('btn-clear');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clear());
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.terminal = new Terminal();
});