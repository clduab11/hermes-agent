/**
 * HERMES Legal AI Dashboard - Simplified Demo App
 * Handles navigation and dashboard functionality for demo
 */

class HermesApp {
    constructor() {
        this.currentUser = null;
        this.init();
    }

    async init() {
        try {
            // Show loading overlay
            this.showLoading();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Initialize dashboard
            await this.initDashboard();
            
            // Load demo user data
            await this.loadUserData();
            
            // Start periodic updates
            this.startPeriodicUpdates();
            
            // Hide loading overlay
            this.hideLoading();
            
        } catch (error) {
            console.error('Failed to initialize HERMES app:', error);
            this.showError('Failed to initialize application. Please refresh the page.');
        }
    }

    async loadUserData() {
        try {
            const response = await fetch('/api/auth/user');
            this.currentUser = await response.json();
            this.updateUserDisplay();
        } catch (error) {
            console.error('Failed to load user data:', error);
            // Use default user for demo
            this.currentUser = {
                name: "Demo Attorney",
                role: "Senior Attorney",
                email: "demo@hermes-ai.com"
            };
            this.updateUserDisplay();
        }
    }

    setupEventListeners() {
        // Sidebar toggle for mobile
        const sidebarToggle = document.getElementById('sidebarToggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', this.toggleSidebar.bind(this));
        }

        // Navigation links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const href = link.getAttribute('href');
                this.navigateTo(href.substring(1)); // Remove #
            });
        });

        // Voice record button
        const voiceRecordBtn = document.getElementById('voiceRecordBtn');
        if (voiceRecordBtn) {
            voiceRecordBtn.addEventListener('click', this.toggleVoiceRecording.bind(this));
        }

        // Global search
        const globalSearch = document.getElementById('globalSearch');
        if (globalSearch) {
            globalSearch.addEventListener('input', this.handleSearch.bind(this));
        }
    }

    async initDashboard() {
        // Load dashboard data
        await this.loadDashboardMetrics();
        await this.loadCharts();
        await this.loadRecentActivity();
        
        // Initialize voice status
        await this.updateVoiceStatus();
        
        // Show dashboard section by default
        this.showSection('dashboard');
    }

    async loadDashboardMetrics() {
        try {
            const response = await fetch('/api/analytics/dashboard/overview');
            const result = await response.json();
            
            if (result.status === 'success') {
                const data = result.data;
                
                // Update metric displays
                this.updateElement('totalCalls', data.total_calls);
                this.updateElement('callsTrend', data.calls_trend);
                this.updateElement('conversionRate', data.conversion_rate + '%');
                this.updateElement('conversionTrend', data.conversion_trend);
                this.updateElement('responseTime', data.response_time + 'ms');
                this.updateElement('responseTrend', data.response_trend);
                this.updateElement('satisfaction', data.satisfaction.toFixed(1));
                this.updateElement('satisfactionTrend', data.satisfaction_trend);
            }
        } catch (error) {
            console.error('Failed to load metrics:', error);
        }
    }

    async loadCharts() {
        try {
            // Load call volume chart
            const callVolumeResponse = await fetch('/api/analytics/dashboard/charts/call-volume');
            const callVolumeResult = await callVolumeResponse.json();
            
            if (callVolumeResult.status === 'success') {
                this.createChart('callVolumeChart', callVolumeResult.data, 'line');
            }
            
            // Load revenue chart  
            const revenueResponse = await fetch('/api/analytics/dashboard/charts/revenue');
            const revenueResult = await revenueResponse.json();
            
            if (revenueResult.status === 'success') {
                this.createChart('revenueChart', revenueResult.data, 'bar');
            }
            
        } catch (error) {
            console.error('Failed to load charts:', error);
        }
    }

    async loadRecentActivity() {
        try {
            const response = await fetch('/api/analytics/dashboard/recent-activity');
            const result = await response.json();
            
            if (result.status === 'success') {
                const activities = result.data;
                const activityContainer = document.getElementById('recentActivity');
                
                if (activityContainer) {
                    activityContainer.innerHTML = activities.map(activity => `
                        <div class="flex items-center p-4 border-b border-gray-100 hover:bg-gray-50">
                            <div class="flex-shrink-0 mr-4">
                                <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                                    <i class="fas ${this.getActivityIcon(activity.type)} text-blue-600 text-sm"></i>
                                </div>
                            </div>
                            <div class="flex-1">
                                <p class="text-sm font-medium text-gray-900">${activity.description}</p>
                                <p class="text-xs text-gray-500">${this.formatTimestamp(activity.timestamp)} • ${activity.user}</p>
                            </div>
                        </div>
                    `).join('');
                }
            }
        } catch (error) {
            console.error('Failed to load recent activity:', error);
        }
    }

    async updateVoiceStatus() {
        try {
            const response = await fetch('/api/analytics/voice/status');
            const result = await response.json();
            
            if (result.status === 'success') {
                const status = result.data;
                const indicator = document.getElementById('voiceIndicator');
                const statusText = document.querySelector('#voiceStatus span');
                
                if (indicator) {
                    indicator.className = `w-3 h-3 rounded-full ${this.getStatusColor(status.indicator_color)}`;
                }
                
                if (statusText) {
                    statusText.textContent = status.status_text;
                }
            }
        } catch (error) {
            console.error('Failed to update voice status:', error);
        }
    }

    createChart(canvasId, data, type) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || !window.Chart) return;
        
        // Destroy existing chart if it exists
        if (canvas.chart) {
            canvas.chart.destroy();
        }
        
        const ctx = canvas.getContext('2d');
        canvas.chart = new Chart(ctx, {
            type: type,
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    navigateTo(section) {
        // Hide all sections
        document.querySelectorAll('section[id$="Section"]').forEach(s => {
            s.classList.add('hidden');
        });
        
        // Show target section
        this.showSection(section);
        
        // Update page title
        const titles = {
            'dashboard': 'Dashboard',
            'voice': 'Voice AI',
            'clients': 'Clients & Matters',
            'analytics': 'Analytics',
            'integrations': 'Integrations',
            'audit': 'Audit Trail',
            'settings': 'Settings'
        };
        
        const pageTitle = document.getElementById('pageTitle');
        if (pageTitle) {
            pageTitle.textContent = titles[section] || 'Dashboard';
        }
        
        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('bg-blue-700');
        });
        
        const activeLink = document.querySelector(`[href="#${section}"]`);
        if (activeLink) {
            activeLink.classList.add('bg-blue-700');
        }
    }

    showSection(sectionName) {
        const section = document.getElementById(`${sectionName}Section`);
        if (section) {
            section.classList.remove('hidden');
        }
    }

    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.toggle('mobile-open');
        }
    }

    toggleVoiceRecording() {
        const btn = document.getElementById('voiceRecordBtn');
        const transcript = document.getElementById('voiceTranscript');
        
        if (btn.classList.contains('voice-recording')) {
            // Stop recording
            btn.classList.remove('voice-recording', 'bg-red-600');
            btn.classList.add('bg-blue-600');
            btn.innerHTML = '<i class="fas fa-microphone text-2xl"></i>';
            
            if (transcript) {
                transcript.textContent = 'Recording stopped. Processing...';
                
                // Simulate processing
                setTimeout(() => {
                    transcript.textContent = 'Thank you for your call. How may I assist you with your legal matter today?';
                }, 2000);
            }
        } else {
            // Start recording
            btn.classList.add('voice-recording', 'bg-red-600');
            btn.classList.remove('bg-blue-600');
            btn.innerHTML = '<i class="fas fa-stop text-2xl"></i>';
            
            if (transcript) {
                transcript.textContent = 'Listening... Speak clearly.';
            }
        }
    }

    handleSearch(event) {
        const query = event.target.value;
        console.log('Searching for:', query);
        // Implement search functionality
    }

    updateUserDisplay() {
        if (!this.currentUser) return;
        
        this.updateElement('userName', this.currentUser.name);
        this.updateElement('userRole', this.currentUser.role);
        
        const avatar = document.getElementById('userAvatar');
        if (avatar && this.currentUser.avatar_url) {
            avatar.src = this.currentUser.avatar_url;
        }
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    getActivityIcon(type) {
        const icons = {
            'voice_call': 'fa-phone',
            'client_update': 'fa-user-plus',
            'system_alert': 'fa-exclamation-triangle',
            'integration': 'fa-sync'
        };
        return icons[type] || 'fa-circle';
    }

    getStatusColor(color) {
        const colors = {
            'green': 'bg-green-400',
            'yellow': 'bg-yellow-400',
            'red': 'bg-red-400',
            'gray': 'bg-gray-400'
        };
        return colors[color] || 'bg-gray-400';
    }

    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        return date.toLocaleDateString();
    }

    startPeriodicUpdates() {
        // Update metrics every 30 seconds
        setInterval(() => {
            this.loadDashboardMetrics();
            this.updateVoiceStatus();
        }, 30000);
        
        // Update activity every 60 seconds
        setInterval(() => {
            this.loadRecentActivity();
        }, 60000);
    }

    showLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.remove('hidden');
        }
    }

    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.add('hidden');
        }
    }

    showError(message) {
        // Create toast notification
        this.showToast(message, 'error');
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        if (!container) return;
        
        const toast = document.createElement('div');
        toast.className = `
            max-w-sm mx-auto bg-white shadow-lg rounded-lg pointer-events-auto
            ring-1 ring-black ring-opacity-5 overflow-hidden mb-4
        `;
        
        const bgColor = type === 'error' ? 'bg-red-50' : 'bg-blue-50';
        const iconColor = type === 'error' ? 'text-red-400' : 'text-blue-400';
        const icon = type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle';
        
        toast.innerHTML = `
            <div class="p-4">
                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        <i class="fas ${icon} ${iconColor}"></i>
                    </div>
                    <div class="ml-3 w-0 flex-1 pt-0.5">
                        <p class="text-sm font-medium text-gray-900">${message}</p>
                    </div>
                    <div class="ml-4 flex-shrink-0 flex">
                        <button class="toast-close bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
        
        // Manual close
        const closeBtn = toast.querySelector('.toast-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            });
        }
    }
}

// Initialize app when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.hermesApp = new HermesApp();
});