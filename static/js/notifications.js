/**
 * PECO Panel de Control - Sistema de Notificaciones
 * Maneja las notificaciones toast y alertas del sistema
 */

class NotificationManager {
    constructor() {
        this.notifications = [];
        this.maxNotifications = 5;
    }

    show(message, type = 'info', duration = 5000, details = null, suggestions = null) {
        const notification = this.createNotification(message, type, duration, details, suggestions);
        this.addNotification(notification);
        return notification;
    }

    createNotification(message, type, duration, details, suggestions) {
        const notification = document.createElement('div');
        const icons = {
            success: '✓',
            error: '✗',
            warning: '⚠',
            info: 'ℹ'
        };
        const colors = {
            success: 'bg-emerald-500 border-emerald-600',
            error: 'bg-red-500 border-red-600',
            warning: 'bg-yellow-500 border-yellow-600',
            info: 'bg-blue-500 border-blue-600'
        };

        notification.className = `fixed top-4 right-4 ${colors[type]} text-white px-4 py-3 rounded-lg shadow-lg border-l-4 z-50 max-w-md transform translate-x-full transition-transform duration-300 ease-out`;

        let detailsHtml = '';
        if (details && typeof details === 'object') {
            const detailEntries = Object.entries(details).slice(0, 3);
            if (detailEntries.length > 0) {
                detailsHtml = `
                    <div class="mt-2 text-xs opacity-90 border-t border-white/20 pt-2">
                        ${detailEntries.map(([key, value]) => 
                            `<div><strong>${key}:</strong> ${String(value).substring(0, 50)}${String(value).length > 50 ? '...' : ''}</div>`
                        ).join('')}
                    </div>
                `;
            }
        }

        let suggestionsHtml = '';
        if (suggestions && Array.isArray(suggestions) && suggestions.length > 0) {
            const limitedSuggestions = suggestions.slice(0, 2);
            suggestionsHtml = `
                <div class="mt-2 text-xs opacity-90 border-t border-white/20 pt-2">
                    <div class="font-semibold mb-1">💡 Sugerencias:</div>
                    ${limitedSuggestions.map(suggestion => `<div>• ${suggestion}</div>`).join('')}
                </div>
            `;
        }

        notification.innerHTML = `
            <div class="flex items-start gap-3">
                <span class="text-lg font-bold flex-shrink-0 mt-0.5">${icons[type]}</span>
                <div class="flex-1 min-w-0">
                    <p class="font-medium break-words">${message}</p>
                    ${detailsHtml}
                    ${suggestionsHtml}
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="text-white/80 hover:text-white text-xl leading-none flex-shrink-0">&times;</button>
            </div>
        `;

        return { element: notification, type, duration };
    }

    addNotification(notification) {
        document.body.appendChild(notification.element);

        // Animate in
        setTimeout(() => {
            notification.element.style.transform = 'translateX(0)';
        }, 10);

        // Auto remove
        const adjustedDuration = (notification.type === 'error' && notification.duration > 0) ? 
            Math.max(notification.duration, 10000) : notification.duration;
        
        if (adjustedDuration > 0) {
            setTimeout(() => {
                this.removeNotification(notification.element);
            }, adjustedDuration);
        }

        this.notifications.push(notification);
        this.limitNotifications();
    }

    removeNotification(element) {
        element.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (element.parentNode) {
                element.remove();
            }
        }, 300);
    }

    limitNotifications() {
        if (this.notifications.length > this.maxNotifications) {
            const oldest = this.notifications.shift();
            this.removeNotification(oldest.element);
        }
    }

    success(message, details = null, suggestions = null) {
        return this.show(message, 'success', 5000, details, suggestions);
    }

    error(message, details = null, suggestions = null) {
        return this.show(message, 'error', 10000, details, suggestions);
    }

    warning(message, details = null, suggestions = null) {
        return this.show(message, 'warning', 7000, details, suggestions);
    }

    info(message, details = null, suggestions = null) {
        return this.show(message, 'info', 5000, details, suggestions);
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.notificationManager = new NotificationManager();
});