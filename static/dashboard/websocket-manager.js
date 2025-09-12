/**
 * HERMES Dashboard WebSocket Manager
 * Real-time communication for live dashboard updates
 */

class HermesWebSocketManager {
    constructor(url = null) {
        this.wsUrl = url || this.getWebSocketUrl();
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 1000; // Start with 1 second
        this.heartbeatInterval = null;
        this.heartbeatTimeout = null;
        this.isConnected = false;
        this.subscriptions = new Map();
        this.messageQueue = [];
        
        // Event callbacks
        this.onConnect = null;
        this.onDisconnect = null;
        this.onReconnecting = null;
        this.onError = null;
        
        this.init();
    }
    
    getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        return `${protocol}//${host}/ws/dashboard`;
    }
    
    init() {
        this.connect();
    }
    
    connect() {
        try {
            console.log('Connecting to WebSocket:', this.wsUrl);
            this.ws = new WebSocket(this.wsUrl);
            
            this.ws.onopen = (event) => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.reconnectInterval = 1000;
                
                this.startHeartbeat();
                this.processMessageQueue();
                
                if (this.onConnect) {
                    this.onConnect(event);
                }
                
                this.showConnectionStatus('connected');
            };
            
            this.ws.onmessage = (event) => {
                this.handleMessage(JSON.parse(event.data));
            };
            
            this.ws.onclose = (event) => {
                console.log('WebSocket disconnected:', event.code, event.reason);
                this.isConnected = false;
                this.stopHeartbeat();
                
                if (this.onDisconnect) {
                    this.onDisconnect(event);
                }
                
                this.showConnectionStatus('disconnected');
                
                // Attempt to reconnect unless it was a clean close
                if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.scheduleReconnect();
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                if (this.onError) {
                    this.onError(error);
                }
                this.showConnectionStatus('error');
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.scheduleReconnect();
            }
        }
    }
    
    scheduleReconnect() {
        this.reconnectAttempts++;
        console.log(`Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${this.reconnectInterval}ms`);
        
        if (this.onReconnecting) {
            this.onReconnecting(this.reconnectAttempts);
        }
        
        this.showConnectionStatus('reconnecting', this.reconnectAttempts);
        
        setTimeout(() => {
            this.connect();
        }, this.reconnectInterval);
        
        // Exponential backoff with jitter
        this.reconnectInterval = Math.min(30000, this.reconnectInterval * 2 + Math.random() * 1000);
    }
    
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
                this.send({
                    type: 'ping',
                    timestamp: Date.now()
                });
                
                // Set timeout for pong response
                this.heartbeatTimeout = setTimeout(() => {
                    console.log('Heartbeat timeout - closing connection');
                    this.ws.close();
                }, 5000);
            }
        }, 30000); // Send ping every 30 seconds
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
        if (this.heartbeatTimeout) {
            clearTimeout(this.heartbeatTimeout);
            this.heartbeatTimeout = null;
        }
    }
    
    handleMessage(message) {
        console.log('Received WebSocket message:', message);
        
        switch (message.type) {
            case 'pong':
                if (this.heartbeatTimeout) {
                    clearTimeout(this.heartbeatTimeout);
                    this.heartbeatTimeout = null;
                }
                break;
                
            case 'analytics_update':
                this.handleAnalyticsUpdate(message.data);
                break;
                
            case 'voice_session_update':
                this.handleVoiceSessionUpdate(message.data);
                break;
                
            case 'system_alert':
                this.handleSystemAlert(message.data);
                break;
                
            case 'clio_sync':
                this.handleClioSync(message.data);
                break;
                
            case 'audit_event':
                this.handleAuditEvent(message.data);
                break;
                
            default:
                // Handle subscribed channels
                if (this.subscriptions.has(message.channel)) {
                    const callbacks = this.subscriptions.get(message.channel);
                    callbacks.forEach(callback => callback(message));
                }
                break;
        }
    }
    
    handleAnalyticsUpdate(data) {
        // Update dashboard metrics in real-time
        if (window.dashboardApp && window.dashboardApp.updateMetrics) {
            window.dashboardApp.updateMetrics(data);
        }
        
        // Update specific charts if they exist
        if (data.chartData) {
            this.updateCharts(data.chartData);
        }
        
        // Show notification for significant changes
        if (data.significant_change) {
            this.showNotification('Analytics Update', {
                body: data.summary || 'New analytics data available',
                icon: '/static/assets/icons/analytics-notification.png',
                tag: 'analytics-update'
            });
        }
    }
    
    handleVoiceSessionUpdate(data) {
        // Update active sessions display
        const sessionsList = document.getElementById('activeSessions');
        if (sessionsList && window.dashboardApp) {
            window.dashboardApp.updateActiveSessions(data);
        }
        
        // Update call statistics
        if (data.call_statistics) {
            this.updateCallStatistics(data.call_statistics);
        }
        
        // Show toast for new sessions
        if (data.event === 'session_started') {
            this.showToast('New Voice Session Started', 'info');
        } else if (data.event === 'session_ended') {
            this.showToast('Voice Session Completed', 'success');
        }
    }
    
    handleSystemAlert(data) {
        // Show system alerts with appropriate severity
        const alertType = data.severity || 'info';
        this.showToast(data.message, alertType);
        
        // Add to system alerts panel if it exists
        const alertsPanel = document.getElementById('systemAlerts');
        if (alertsPanel) {
            this.addSystemAlert(data);
        }
        
        // Send push notification for critical alerts
        if (data.severity === 'critical' && 'serviceWorker' in navigator) {
            navigator.serviceWorker.ready.then(registration => {
                registration.showNotification('HERMES System Alert', {
                    body: data.message,
                    icon: '/static/assets/icons/alert-critical.png',
                    badge: '/static/assets/icons/badge-72x72.png',
                    tag: 'system-alert',
                    requireInteraction: true,
                    data: { url: '/dashboard#alerts', severity: data.severity }
                });
            });
        }
    }
    
    handleClioSync(data) {
        // Update Clio sync status
        const syncStatus = document.getElementById('clioSyncStatus');
        if (syncStatus) {
            this.updateClioSyncStatus(data);
        }
        
        // Show sync notifications
        if (data.event === 'sync_completed') {
            this.showToast(`Clio sync completed: ${data.records_synced} records`, 'success');
        } else if (data.event === 'sync_error') {
            this.showToast(`Clio sync error: ${data.error}`, 'error');
        }
    }
    
    handleAuditEvent(data) {
        // Update audit trail in real-time
        const auditTrail = document.getElementById('auditTrail');
        if (auditTrail && window.dashboardApp) {
            window.dashboardApp.addAuditEvent(data);
        }
        
        // Show security alerts
        if (data.security_event && data.risk_level === 'high') {
            this.showToast(`Security Alert: ${data.description}`, 'warning');
        }
    }
    
    send(message) {
        if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(JSON.stringify(message));
                return true;
            } catch (error) {
                console.error('Failed to send WebSocket message:', error);
                this.messageQueue.push(message);
                return false;
            }
        } else {
            // Queue message for later
            this.messageQueue.push(message);
            return false;
        }
    }
    
    processMessageQueue() {
        if (this.messageQueue.length > 0) {
            console.log(`Processing ${this.messageQueue.length} queued messages`);
            const messages = [...this.messageQueue];
            this.messageQueue = [];
            
            messages.forEach(message => {
                this.send(message);
            });
        }
    }
    
    subscribe(channel, callback) {
        if (!this.subscriptions.has(channel)) {
            this.subscriptions.set(channel, []);
        }
        this.subscriptions.get(channel).push(callback);
        
        // Send subscription request
        this.send({
            type: 'subscribe',
            channel: channel,
            timestamp: Date.now()
        });
    }
    
    unsubscribe(channel, callback = null) {
        if (this.subscriptions.has(channel)) {
            if (callback) {
                const callbacks = this.subscriptions.get(channel);
                const index = callbacks.indexOf(callback);
                if (index > -1) {
                    callbacks.splice(index, 1);
                }
                if (callbacks.length === 0) {
                    this.subscriptions.delete(channel);
                }
            } else {
                this.subscriptions.delete(channel);
            }
            
            // Send unsubscription request
            this.send({
                type: 'unsubscribe',
                channel: channel,
                timestamp: Date.now()
            });
        }
    }
    
    // UI Helper Methods
    
    showConnectionStatus(status, attempt = null) {
        const statusElement = document.getElementById('wsConnectionStatus');
        if (!statusElement) return;
        
        const statusIcon = statusElement.querySelector('.status-icon');
        const statusText = statusElement.querySelector('.status-text');
        
        switch (status) {
            case 'connected':
                statusElement.className = 'ws-status connected';
                statusIcon.innerHTML = '🟢';
                statusText.textContent = 'Connected';
                break;
            case 'disconnected':
                statusElement.className = 'ws-status disconnected';
                statusIcon.innerHTML = '🔴';
                statusText.textContent = 'Disconnected';
                break;
            case 'reconnecting':
                statusElement.className = 'ws-status reconnecting';
                statusIcon.innerHTML = '🟡';
                statusText.textContent = `Reconnecting (${attempt}/${this.maxReconnectAttempts})...`;
                break;
            case 'error':
                statusElement.className = 'ws-status error';
                statusIcon.innerHTML = '⚠️';
                statusText.textContent = 'Connection Error';
                break;
        }
    }
    
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-icon">${this.getToastIcon(type)}</div>
                <div class="toast-message">${message}</div>
                <button class="toast-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        const container = document.getElementById('toastContainer');
        if (container) {
            container.appendChild(toast);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 5000);
        }
    }
    
    getToastIcon(type) {
        switch (type) {
            case 'success': return '✅';
            case 'error': return '❌';
            case 'warning': return '⚠️';
            case 'info': 
            default: return 'ℹ️';
        }
    }
    
    showNotification(title, options = {}) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, {
                icon: '/static/assets/icons/icon-192x192.png',
                badge: '/static/assets/icons/badge-72x72.png',
                ...options
            });
        }
    }
    
    updateCharts(chartData) {
        // Update Chart.js charts with new data
        Object.keys(chartData).forEach(chartId => {
            const chart = window.chartInstances?.[chartId];
            if (chart) {
                chart.data = chartData[chartId];
                chart.update('none'); // Update without animation for real-time feel
            }
        });
    }
    
    updateCallStatistics(stats) {
        // Update call statistics displays
        const elements = {
            'totalCalls': stats.total_calls,
            'activeCalls': stats.active_calls,
            'avgResponseTime': stats.avg_response_time,
            'conversionRate': stats.conversion_rate
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }
    
    updateClioSyncStatus(data) {
        const statusElement = document.getElementById('clioSyncStatus');
        if (!statusElement) return;
        
        statusElement.className = `sync-status ${data.status}`;
        statusElement.innerHTML = `
            <span class="sync-icon">${data.status === 'syncing' ? '🔄' : data.status === 'success' ? '✅' : '❌'}</span>
            <span class="sync-text">${data.message}</span>
            <span class="sync-time">${new Date(data.timestamp).toLocaleTimeString()}</span>
        `;
    }
    
    addSystemAlert(alert) {
        const alertsPanel = document.getElementById('systemAlerts');
        if (!alertsPanel) return;
        
        const alertElement = document.createElement('div');
        alertElement.className = `alert alert-${alert.severity}`;
        alertElement.innerHTML = `
            <div class="alert-content">
                <div class="alert-icon">${this.getAlertIcon(alert.severity)}</div>
                <div class="alert-details">
                    <div class="alert-title">${alert.title || 'System Alert'}</div>
                    <div class="alert-message">${alert.message}</div>
                    <div class="alert-time">${new Date(alert.timestamp).toLocaleString()}</div>
                </div>
                <button class="alert-dismiss" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        alertsPanel.insertBefore(alertElement, alertsPanel.firstChild);
        
        // Remove old alerts (keep only latest 10)
        const alerts = alertsPanel.querySelectorAll('.alert');
        if (alerts.length > 10) {
            for (let i = 10; i < alerts.length; i++) {
                alerts[i].remove();
            }
        }
    }
    
    getAlertIcon(severity) {
        switch (severity) {
            case 'critical': return '🚨';
            case 'high': return '⚠️';
            case 'medium': return '⚡';
            case 'low':
            default: return 'ℹ️';
        }
    }
    
    close() {
        this.stopHeartbeat();
        if (this.ws) {
            this.ws.close(1000, 'Client closing connection');
        }
    }
    
    // Static method to initialize global WebSocket manager
    static initialize(url = null) {
        if (!window.hermesWS) {
            window.hermesWS = new HermesWebSocketManager(url);
        }
        return window.hermesWS;
    }
}

// Initialize WebSocket manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Request notification permissions
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
    
    // Initialize WebSocket connection
    window.hermesWS = HermesWebSocketManager.initialize();
    
    // Set up event handlers
    window.hermesWS.onConnect = () => {
        console.log('Dashboard WebSocket connected');
        // Subscribe to relevant channels
        window.hermesWS.subscribe('analytics', (message) => {
            console.log('Analytics channel update:', message);
        });
        window.hermesWS.subscribe('voice_sessions', (message) => {
            console.log('Voice sessions update:', message);
        });
        window.hermesWS.subscribe('system_events', (message) => {
            console.log('System events update:', message);
        });
    };
    
    window.hermesWS.onDisconnect = () => {
        console.log('Dashboard WebSocket disconnected');
    };
    
    window.hermesWS.onReconnecting = (attempt) => {
        console.log(`Reconnecting attempt ${attempt}`);
    };
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (window.hermesWS) {
        window.hermesWS.close();
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HermesWebSocketManager;
}