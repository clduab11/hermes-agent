/**
 * HERMES Legal AI Dashboard - Main Application
 * Handles navigation, authentication, and core dashboard functionality
 */

class HermesApp {
    constructor() {
        this.currentUser = null;
        this.websocketConnection = null;
        this.authToken = localStorage.getItem('hermes_auth_token');
        this.refreshToken = localStorage.getItem('hermes_refresh_token');
        
        this.init();
    }

    async init() {
        try {
            // Show loading overlay
            this.showLoading();
            
            // Initialize authentication
            await this.initAuth();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Initialize dashboard
            await this.initDashboard();
            
            // Setup real-time updates
            this.initWebSocket();
            
            // Setup periodic updates
            this.startPeriodicUpdates();
            
            // Hide loading overlay
            this.hideLoading();
            
        } catch (error) {
            console.error('Failed to initialize HERMES app:', error);
            this.showError('Failed to initialize application. Please refresh the page.');
        }
    }

    // Authentication Management
    async initAuth() {
        if (!this.authToken) {
            this.redirectToLogin();
            return;
        }

        try {
            // Verify token and get user info
            const response = await this.apiCall('/auth/me', 'GET');
            this.currentUser = response;
            this.updateUserDisplay();
            
        } catch (error) {
            if (error.status === 401) {
                // Try to refresh token
                await this.refreshAuthToken();
            } else {
                throw error;
            }
        }
    }

    async refreshAuthToken() {
        if (!this.refreshToken) {
            this.redirectToLogin();
            return;
        }

        try {
            const response = await fetch('/auth/refresh', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh_token: this.refreshToken })
            });

            if (!response.ok) {
                throw new Error('Token refresh failed');
            }

            const tokens = await response.json();
            this.authToken = tokens.access_token;
            this.refreshToken = tokens.refresh_token;
            
            localStorage.setItem('hermes_auth_token', this.authToken);
            localStorage.setItem('hermes_refresh_token', this.refreshToken);
            
            // Retry getting user info
            await this.initAuth();
            
        } catch (error) {
            console.error('Token refresh failed:', error);
            this.redirectToLogin();
        }
    }

    redirectToLogin() {
        window.location.href = '/login';
    }

    updateUserDisplay() {
        const userNameElement = document.getElementById('current-user-name');
        if (userNameElement && this.currentUser) {
            userNameElement.textContent = this.currentUser.full_name || 'User';
        }
    }

    // API Communication
    async apiCall(endpoint, method = 'GET', body = null) {
        const headers = {
            'Content-Type': 'application/json',
        };

        if (this.authToken) {
            headers['Authorization'] = `Bearer ${this.authToken}`;
        }

        const response = await fetch(endpoint, {
            method,
            headers,
            body: body ? JSON.stringify(body) : null
        });

        if (!response.ok) {
            if (response.status === 401) {
                // Token expired, try refresh
                await this.refreshAuthToken();
                return this.apiCall(endpoint, method, body);
            }
            throw new Error(`API call failed: ${response.status} ${response.statusText}`);
        }

        return response.json();
    }

    // Dashboard Initialization
    async initDashboard() {
        await Promise.all([
            this.loadMetrics(),
            this.loadRecentActivity(),
            this.updateSystemStatus()
        ]);
    }

    async loadMetrics() {
        try {
            // Load dashboard metrics
            const metrics = await this.apiCall('/api/dashboard/metrics');
            this.updateMetricsDisplay(metrics);
        } catch (error) {
            console.error('Failed to load metrics:', error);
        }
    }

    updateMetricsDisplay(metrics) {
        const elements = {
            'total-calls': metrics.totalCalls || 0,
            'avg-response': `${metrics.avgResponseTime || 0}ms`,
            'satisfaction': `${metrics.clientSatisfaction || 0}%`,
            'new-matters': metrics.newMatters || 0
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }

    async loadRecentActivity() {
        try {
            const activity = await this.apiCall('/api/dashboard/activity');
            this.renderRecentActivity(activity);
        } catch (error) {
            console.error('Failed to load recent activity:', error);
        }
    }

    renderRecentActivity(activities) {
        const container = document.getElementById('recent-activity');
        if (!container) return;

        if (!activities || activities.length === 0) {
            container.innerHTML = '<p class="no-activity">No recent activity</p>';
            return;
        }

        const activityHtml = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon">
                    <i class="fas fa-${this.getActivityIcon(activity.type)}" aria-hidden="true"></i>
                </div>
                <div class="activity-content">
                    <h4>${activity.title}</h4>
                    <p>${activity.description}</p>
                    <time>${this.formatDate(activity.timestamp)}</time>
                </div>
            </div>
        `).join('');

        container.innerHTML = activityHtml;
    }

    getActivityIcon(type) {
        const icons = {
            'call': 'phone',
            'matter': 'briefcase',
            'client': 'user',
            'document': 'file-alt',
            'workflow': 'sitemap'
        };
        return icons[type] || 'info-circle';
    }

    async updateSystemStatus() {
        try {
            const status = await this.apiCall('/api/system/status');
            this.updateStatusDisplay(status);
        } catch (error) {
            console.error('Failed to update system status:', error);
            this.updateStatusDisplay({
                systemStatus: 'offline',
                voiceStatus: 'offline',
                activeSessions: 0,
                dailyCalls: 0
            });
        }
    }

    updateStatusDisplay(status) {
        const elements = {
            'system-status': { value: status.systemStatus || 'offline', className: status.systemStatus || 'offline' },
            'voice-status': { value: status.voiceStatus || 'offline', className: status.voiceStatus || 'offline' },
            'active-sessions': status.activeSessions || 0,
            'daily-calls': status.dailyCalls || 0
        };

        Object.entries(elements).forEach(([id, config]) => {
            const element = document.getElementById(id);
            if (element) {
                if (typeof config === 'object') {
                    element.textContent = config.value;
                    element.className = `status-value ${config.className}`;
                } else {
                    element.textContent = config;
                }
            }
        });
    }

    // Event Handlers
    setupEventListeners() {
        // Navigation
        this.setupNavigation();
        
        // User menu
        this.setupUserMenu();
        
        // Mobile menu
        this.setupMobileMenu();
        
        // Quick actions
        this.setupQuickActions();
        
        // Window events
        window.addEventListener('online', () => this.handleConnectivityChange(true));
        window.addEventListener('offline', () => this.handleConnectivityChange(false));
        window.addEventListener('beforeunload', () => this.cleanup());
    }

    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const target = link.getAttribute('href').substring(1);
                this.navigateToPage(target);
            });
        });
    }

    navigateToPage(pageId) {
        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        document.querySelector(`[href="#${pageId}"]`)?.classList.add('active');
        
        // Show target page
        document.querySelectorAll('.page-section').forEach(section => {
            section.classList.remove('active');
        });
        
        const targetPage = document.getElementById(`${pageId}-page`);
        if (targetPage) {
            targetPage.classList.add('active');
            this.loadPageData(pageId);
        }
    }

    async loadPageData(pageId) {
        switch (pageId) {
            case 'voice-interface':
                if (window.VoiceInterface) {
                    window.VoiceInterface.init();
                }
                break;
            case 'analytics':
                if (window.Analytics) {
                    window.Analytics.init();
                }
                break;
            // Add other page loaders
        }
    }

    setupUserMenu() {
        const userButton = document.querySelector('.user-button');
        const userDropdown = document.querySelector('.user-dropdown');
        
        if (userButton && userDropdown) {
            userButton.addEventListener('click', () => {
                const isExpanded = userButton.getAttribute('aria-expanded') === 'true';
                userButton.setAttribute('aria-expanded', !isExpanded);
                userDropdown.style.display = isExpanded ? 'none' : 'block';
            });
            
            // Close dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!userButton.contains(e.target) && !userDropdown.contains(e.target)) {
                    userButton.setAttribute('aria-expanded', 'false');
                    userDropdown.style.display = 'none';
                }
            });
        }
    }

    setupMobileMenu() {
        const menuToggle = document.querySelector('.mobile-menu-toggle');
        const nav = document.querySelector('.main-nav');
        
        if (menuToggle && nav) {
            menuToggle.addEventListener('click', () => {
                nav.classList.toggle('mobile-open');
            });
        }
    }

    setupQuickActions() {
        // These will be implemented as the system grows
        window.startVoiceSession = () => this.startVoiceSession();
        window.createMatter = () => this.createMatter();
        window.scheduleCall = () => this.scheduleCall();
        window.generateReport = () => this.generateReport();
    }

    // Quick Action Handlers
    async startVoiceSession() {
        try {
            this.navigateToPage('voice-interface');
            if (window.VoiceInterface) {
                await window.VoiceInterface.startSession();
            }
        } catch (error) {
            console.error('Failed to start voice session:', error);
            this.showError('Failed to start voice session');
        }
    }

    createMatter() {
        // Navigate to matter creation or show modal
        this.showToast('Matter creation feature coming soon', 'info');
    }

    scheduleCall() {
        // Navigate to scheduling or show modal
        this.showToast('Call scheduling feature coming soon', 'info');
    }

    generateReport() {
        // Navigate to reports or show modal
        this.showToast('Report generation feature coming soon', 'info');
    }

    // WebSocket Connection
    initWebSocket() {
        if (!this.authToken) return;

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/dashboard?token=${this.authToken}`;
        
        this.websocketConnection = new WebSocket(wsUrl);
        
        this.websocketConnection.onopen = () => {
            console.log('WebSocket connected');
            this.updateConnectionStatus('online');
        };
        
        this.websocketConnection.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.websocketConnection.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus('offline');
            // Attempt to reconnect after delay
            setTimeout(() => this.initWebSocket(), 5000);
        };
        
        this.websocketConnection.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'status_update':
                this.updateStatusDisplay(data.payload);
                break;
            case 'new_activity':
                this.addActivityItem(data.payload);
                break;
            case 'metrics_update':
                this.updateMetricsDisplay(data.payload);
                break;
            case 'notification':
                this.showToast(data.payload.message, data.payload.type || 'info');
                break;
        }
    }

    updateConnectionStatus(status) {
        const systemStatusElement = document.getElementById('system-status');
        if (systemStatusElement) {
            systemStatusElement.textContent = status;
            systemStatusElement.className = `status-value ${status}`;
        }
    }

    // Periodic Updates
    startPeriodicUpdates() {
        // Update metrics every 30 seconds
        this.metricsInterval = setInterval(() => {
            this.loadMetrics();
        }, 30000);
        
        // Update system status every 10 seconds
        this.statusInterval = setInterval(() => {
            this.updateSystemStatus();
        }, 10000);
    }

    // Utility Methods
    showLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.remove('hidden');
        }
    }

    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.add('hidden');
        }
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <p>${message}</p>
                <button class="toast-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        container.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return date.toLocaleDateString();
    }

    handleConnectivityChange(isOnline) {
        if (isOnline) {
            this.showToast('Connection restored', 'success');
            this.initDashboard();
            if (!this.websocketConnection || this.websocketConnection.readyState !== WebSocket.OPEN) {
                this.initWebSocket();
            }
        } else {
            this.showToast('Connection lost. Some features may be unavailable.', 'warning');
        }
    }

    addActivityItem(activity) {
        const container = document.getElementById('recent-activity');
        if (!container) return;

        const activityHtml = `
            <div class="activity-item new">
                <div class="activity-icon">
                    <i class="fas fa-${this.getActivityIcon(activity.type)}" aria-hidden="true"></i>
                </div>
                <div class="activity-content">
                    <h4>${activity.title}</h4>
                    <p>${activity.description}</p>
                    <time>${this.formatDate(activity.timestamp)}</time>
                </div>
            </div>
        `;

        container.insertAdjacentHTML('afterbegin', activityHtml);
        
        // Remove old items if too many
        const items = container.querySelectorAll('.activity-item');
        if (items.length > 10) {
            items[items.length - 1].remove();
        }
    }

    // Cleanup
    cleanup() {
        if (this.websocketConnection) {
            this.websocketConnection.close();
        }
        
        if (this.metricsInterval) {
            clearInterval(this.metricsInterval);
        }
        
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.HermesApp = new HermesApp();
});

// Make app globally available for debugging
window.hermes = {
    app: () => window.HermesApp
};