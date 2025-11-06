/**
 * HERMES Analytics Dashboard Component
 * Performance insights and business intelligence for legal AI
 */

class Analytics {
    constructor() {
        this.charts = {};
        this.isInitialized = false;
        this.updateInterval = null;
        this.dateRange = 'week'; // week, month, quarter, year
    }

    async init() {
        if (!this.isInitialized) {
            this.createAnalyticsDashboard();
            this.setupEventListeners();
            await this.loadAnalyticsData();
            this.startPeriodicUpdates();
            this.isInitialized = true;
        }
    }

    createAnalyticsDashboard() {
        const container = document.getElementById('analytics-container');
        if (!container) return;

        container.innerHTML = `
            <div class="analytics-dashboard">
                <!-- Analytics Header -->
                <div class="analytics-header">
                    <div class="analytics-title">
                        <h2>Performance Analytics</h2>
                        <p>Real-time insights and business intelligence</p>
                    </div>
                    <div class="analytics-controls">
                        <select id="date-range-selector" class="date-range-select">
                            <option value="week">Last 7 Days</option>
                            <option value="month">Last 30 Days</option>
                            <option value="quarter">Last 3 Months</option>
                            <option value="year">Last Year</option>
                        </select>
                        <button id="export-analytics" class="control-btn secondary">
                            <i class="fas fa-download"></i>
                            Export Report
                        </button>
                        <button id="refresh-analytics" class="control-btn primary">
                            <i class="fas fa-sync-alt"></i>
                            Refresh Data
                        </button>
                    </div>
                </div>

                <!-- Key Performance Indicators -->
                <div class="kpi-section">
                    <div class="kpi-grid">
                        <div class="kpi-card">
                            <div class="kpi-icon">
                                <i class="fas fa-phone-volume"></i>
                            </div>
                            <div class="kpi-content">
                                <h3>Total Interactions</h3>
                                <div class="kpi-value" id="total-interactions">0</div>
                                <div class="kpi-change positive" id="interactions-change">+0%</div>
                            </div>
                            <div class="kpi-chart">
                                <canvas id="interactions-trend" width="80" height="40"></canvas>
                            </div>
                        </div>

                        <div class="kpi-card">
                            <div class="kpi-icon">
                                <i class="fas fa-stopwatch"></i>
                            </div>
                            <div class="kpi-content">
                                <h3>Avg Response Time</h3>
                                <div class="kpi-value" id="avg-response-time">0ms</div>
                                <div class="kpi-change negative" id="response-time-change">-0%</div>
                            </div>
                            <div class="kpi-chart">
                                <canvas id="response-time-trend" width="80" height="40"></canvas>
                            </div>
                        </div>

                        <div class="kpi-card">
                            <div class="kpi-icon">
                                <i class="fas fa-heart"></i>
                            </div>
                            <div class="kpi-content">
                                <h3>Satisfaction Rate</h3>
                                <div class="kpi-value" id="satisfaction-rate">0%</div>
                                <div class="kpi-change positive" id="satisfaction-change">+0%</div>
                            </div>
                            <div class="kpi-chart">
                                <canvas id="satisfaction-trend" width="80" height="40"></canvas>
                            </div>
                        </div>

                        <div class="kpi-card">
                            <div class="kpi-icon">
                                <i class="fas fa-dollar-sign"></i>
                            </div>
                            <div class="kpi-content">
                                <h3>Revenue Impact</h3>
                                <div class="kpi-value" id="revenue-impact">$0</div>
                                <div class="kpi-change positive" id="revenue-change">+0%</div>
                            </div>
                            <div class="kpi-chart">
                                <canvas id="revenue-trend" width="80" height="40"></canvas>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Main Charts Section -->
                <div class="charts-section">
                    <div class="charts-grid">
                        <!-- Interaction Volume Chart -->
                        <div class="chart-container">
                            <div class="chart-header">
                                <h3>Interaction Volume</h3>
                                <div class="chart-controls">
                                    <button class="chart-type-btn active" data-type="line">
                                        <i class="fas fa-chart-line"></i>
                                    </button>
                                    <button class="chart-type-btn" data-type="bar">
                                        <i class="fas fa-chart-bar"></i>
                                    </button>
                                </div>
                            </div>
                            <div class="chart-wrapper">
                                <canvas id="interaction-volume-chart"></canvas>
                            </div>
                        </div>

                        <!-- Response Time Distribution -->
                        <div class="chart-container">
                            <div class="chart-header">
                                <h3>Response Time Distribution</h3>
                            </div>
                            <div class="chart-wrapper">
                                <canvas id="response-time-chart"></canvas>
                            </div>
                        </div>

                        <!-- Client Satisfaction Breakdown -->
                        <div class="chart-container">
                            <div class="chart-header">
                                <h3>Client Satisfaction</h3>
                            </div>
                            <div class="chart-wrapper">
                                <canvas id="satisfaction-chart"></canvas>
                            </div>
                        </div>

                        <!-- Matter Types Distribution -->
                        <div class="chart-container">
                            <div class="chart-header">
                                <h3>Matter Types</h3>
                            </div>
                            <div class="chart-wrapper">
                                <canvas id="matter-types-chart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Insights Section -->
                <div class="insights-section">
                    <div class="insights-header">
                        <h3>AI-Powered Insights</h3>
                        <button id="generate-insights" class="control-btn secondary">
                            <i class="fas fa-magic"></i>
                            Generate Insights
                        </button>
                    </div>
                    <div class="insights-grid" id="insights-grid">
                        <!-- Insights will be loaded here -->
                    </div>
                </div>

                <!-- Performance Metrics Table -->
                <div class="metrics-table-section">
                    <div class="table-header">
                        <h3>Detailed Metrics</h3>
                        <div class="table-controls">
                            <input type="search" id="metrics-search" placeholder="Search metrics..." class="search-input">
                            <select id="metrics-filter" class="filter-select">
                                <option value="all">All Metrics</option>
                                <option value="performance">Performance</option>
                                <option value="satisfaction">Satisfaction</option>
                                <option value="business">Business</option>
                            </select>
                        </div>
                    </div>
                    <div class="table-wrapper">
                        <table id="metrics-table" class="analytics-table">
                            <thead>
                                <tr>
                                    <th>Metric</th>
                                    <th>Current</th>
                                    <th>Previous Period</th>
                                    <th>Change</th>
                                    <th>Trend</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody id="metrics-table-body">
                                <!-- Metrics will be loaded here -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Analytics Styles -->
            <style>
                .analytics-dashboard {
                    display: flex;
                    flex-direction: column;
                    gap: 2rem;
                }

                /* Header */
                .analytics-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    background: white;
                    padding: 2rem;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                }

                .analytics-title h2 {
                    font-family: 'Crimson Text', serif;
                    font-size: 2rem;
                    color: #1a365d;
                    margin-bottom: 0.5rem;
                }

                .analytics-title p {
                    color: #4a5568;
                    font-size: 1.1rem;
                }

                .analytics-controls {
                    display: flex;
                    gap: 1rem;
                    align-items: center;
                }

                .date-range-select, .filter-select {
                    padding: 0.75rem 1rem;
                    border: 2px solid #e2e8f0;
                    border-radius: 8px;
                    background: white;
                    color: #4a5568;
                    font-weight: 500;
                }

                /* KPI Section */
                .kpi-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                    gap: 1.5rem;
                }

                .kpi-card {
                    background: white;
                    border-radius: 12px;
                    padding: 2rem;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                    border-left: 4px solid #d69e2e;
                    display: flex;
                    align-items: center;
                    gap: 1.5rem;
                    transition: transform 0.3s ease;
                }

                .kpi-card:hover {
                    transform: translateY(-2px);
                }

                .kpi-icon {
                    width: 60px;
                    height: 60px;
                    background: linear-gradient(135deg, #1a365d, #2d5a87);
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 1.5rem;
                }

                .kpi-content {
                    flex: 1;
                }

                .kpi-content h3 {
                    font-size: 0.9rem;
                    color: #4a5568;
                    font-weight: 600;
                    margin-bottom: 0.5rem;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }

                .kpi-value {
                    font-size: 2rem;
                    font-weight: 700;
                    color: #1a365d;
                    line-height: 1;
                    margin-bottom: 0.5rem;
                }

                .kpi-change {
                    font-size: 0.875rem;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 0.25rem;
                }

                .kpi-change.positive {
                    color: #38a169;
                }

                .kpi-change.negative {
                    color: #e53e3e;
                }

                .kpi-chart {
                    width: 80px;
                    height: 40px;
                }

                /* Charts Section */
                .charts-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                    gap: 2rem;
                }

                .chart-container {
                    background: white;
                    border-radius: 12px;
                    padding: 2rem;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                }

                .chart-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 2rem;
                }

                .chart-header h3 {
                    font-family: 'Crimson Text', serif;
                    font-size: 1.5rem;
                    color: #1a365d;
                }

                .chart-controls {
                    display: flex;
                    gap: 0.5rem;
                }

                .chart-type-btn {
                    padding: 0.5rem;
                    border: 2px solid #e2e8f0;
                    background: white;
                    border-radius: 6px;
                    cursor: pointer;
                    color: #4a5568;
                    transition: all 0.3s ease;
                }

                .chart-type-btn.active,
                .chart-type-btn:hover {
                    border-color: #d69e2e;
                    color: #d69e2e;
                    background: #fef5e7;
                }

                .chart-wrapper {
                    position: relative;
                    height: 300px;
                }

                /* Insights Section */
                .insights-section {
                    background: white;
                    border-radius: 12px;
                    padding: 2rem;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                }

                .insights-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 2rem;
                }

                .insights-header h3 {
                    font-family: 'Crimson Text', serif;
                    font-size: 1.5rem;
                    color: #1a365d;
                }

                .insights-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 1.5rem;
                }

                .insight-card {
                    padding: 1.5rem;
                    border-radius: 8px;
                    border-left: 4px solid #3182ce;
                    background: #f7fafc;
                    transition: transform 0.3s ease;
                }

                .insight-card:hover {
                    transform: translateY(-2px);
                }

                .insight-card.success {
                    border-left-color: #38a169;
                }

                .insight-card.warning {
                    border-left-color: #d69e2e;
                }

                .insight-card.error {
                    border-left-color: #e53e3e;
                }

                .insight-title {
                    font-weight: 600;
                    color: #1a365d;
                    margin-bottom: 0.5rem;
                }

                .insight-description {
                    color: #4a5568;
                    line-height: 1.6;
                    margin-bottom: 1rem;
                }

                .insight-action {
                    font-size: 0.875rem;
                    color: #3182ce;
                    font-weight: 600;
                    text-decoration: none;
                    display: inline-flex;
                    align-items: center;
                    gap: 0.25rem;
                }

                /* Metrics Table */
                .metrics-table-section {
                    background: white;
                    border-radius: 12px;
                    padding: 2rem;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                }

                .table-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 2rem;
                }

                .table-header h3 {
                    font-family: 'Crimson Text', serif;
                    font-size: 1.5rem;
                    color: #1a365d;
                }

                .table-controls {
                    display: flex;
                    gap: 1rem;
                    align-items: center;
                }

                .search-input {
                    padding: 0.75rem 1rem;
                    border: 2px solid #e2e8f0;
                    border-radius: 8px;
                    width: 250px;
                }

                .table-wrapper {
                    overflow-x: auto;
                }

                .analytics-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 0.9rem;
                }

                .analytics-table th,
                .analytics-table td {
                    padding: 1rem;
                    text-align: left;
                    border-bottom: 1px solid #e2e8f0;
                }

                .analytics-table th {
                    background: #f7fafc;
                    font-weight: 600;
                    color: #1a365d;
                    position: sticky;
                    top: 0;
                }

                .analytics-table tbody tr:hover {
                    background: #f7fafc;
                }

                .metric-trend {
                    width: 60px;
                    height: 20px;
                }

                .status-badge {
                    padding: 0.25rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.8rem;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }

                .status-badge.excellent {
                    background: #c6f6d5;
                    color: #22543d;
                }

                .status-badge.good {
                    background: #fed7d7;
                    color: #742a2a;
                }

                .status-badge.needs-improvement {
                    background: #feebc8;
                    color: #7b341e;
                }

                /* Responsive Design */
                @media (max-width: 768px) {
                    .analytics-header {
                        flex-direction: column;
                        gap: 1rem;
                        align-items: stretch;
                    }

                    .analytics-controls {
                        justify-content: space-between;
                    }

                    .kpi-grid {
                        grid-template-columns: 1fr;
                    }

                    .charts-grid {
                        grid-template-columns: 1fr;
                    }

                    .table-controls {
                        flex-direction: column;
                        align-items: stretch;
                    }

                    .search-input {
                        width: 100%;
                    }
                }
            </style>
        `;
    }

    setupEventListeners() {
        // Date range selector
        document.getElementById('date-range-selector')?.addEventListener('change', (e) => {
            this.dateRange = e.target.value;
            this.loadAnalyticsData();
        });

        // Refresh button
        document.getElementById('refresh-analytics')?.addEventListener('click', () => {
            this.loadAnalyticsData();
        });

        // Export button
        document.getElementById('export-analytics')?.addEventListener('click', () => {
            this.exportAnalytics();
        });

        // Generate insights button
        document.getElementById('generate-insights')?.addEventListener('click', () => {
            this.generateInsights();
        });

        // Chart type buttons
        document.querySelectorAll('.chart-type-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const container = e.target.closest('.chart-container');
                const buttons = container.querySelectorAll('.chart-type-btn');
                buttons.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                
                const chartType = e.target.dataset.type;
                this.updateChartType(container.querySelector('canvas').id, chartType);
            });
        });

        // Search and filter
        document.getElementById('metrics-search')?.addEventListener('input', (e) => {
            this.filterMetricsTable(e.target.value);
        });

        document.getElementById('metrics-filter')?.addEventListener('change', (e) => {
            this.filterMetricsTable(null, e.target.value);
        });
    }

    async loadAnalyticsData() {
        try {
            const response = await this.apiCall(`/api/analytics?range=${this.dateRange}`);
            
            this.updateKPIs(response.kpis);
            this.renderCharts(response.charts);
            this.renderMetricsTable(response.metrics);
            this.renderInsights(response.insights);
            
        } catch (error) {
            console.error('Failed to load analytics data:', error);
            this.showError('Failed to load analytics data');
        }
    }

    updateKPIs(kpis) {
        const kpiElements = {
            'total-interactions': kpis.totalInteractions || 0,
            'avg-response-time': `${kpis.avgResponseTime || 0}ms`,
            'satisfaction-rate': `${kpis.satisfactionRate || 0}%`,
            'revenue-impact': `$${this.formatNumber(kpis.revenueImpact || 0)}`
        };

        const changeElements = {
            'interactions-change': kpis.interactionsChange || 0,
            'response-time-change': kpis.responseTimeChange || 0,
            'satisfaction-change': kpis.satisfactionChange || 0,
            'revenue-change': kpis.revenueChange || 0
        };

        // Update KPI values
        Object.entries(kpiElements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });

        // Update KPI changes
        Object.entries(changeElements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                const sign = value >= 0 ? '+' : '';
                element.textContent = `${sign}${value}%`;
                element.className = `kpi-change ${value >= 0 ? 'positive' : 'negative'}`;
            }
        });

        // Render mini trend charts
        this.renderTrendCharts(kpis.trends);
    }

    renderTrendCharts(trends) {
        const trendCharts = {
            'interactions-trend': trends.interactions || [],
            'response-time-trend': trends.responseTime || [],
            'satisfaction-trend': trends.satisfaction || [],
            'revenue-trend': trends.revenue || []
        };

        Object.entries(trendCharts).forEach(([canvasId, data]) => {
            const canvas = document.getElementById(canvasId);
            if (canvas && data.length > 0) {
                this.renderMiniChart(canvas, data);
            }
        });
    }

    renderMiniChart(canvas, data) {
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        ctx.clearRect(0, 0, width, height);
        
        const max = Math.max(...data);
        const min = Math.min(...data);
        const range = max - min || 1;
        
        ctx.strokeStyle = '#d69e2e';
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        data.forEach((value, index) => {
            const x = (index / (data.length - 1)) * width;
            const y = height - ((value - min) / range) * height;
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        
        ctx.stroke();
    }

    renderCharts(chartData) {
        // Since we don't have Chart.js loaded, we'll create simple canvas visualizations
        this.renderInteractionVolumeChart(chartData.interactionVolume);
        this.renderResponseTimeChart(chartData.responseTime);
        this.renderSatisfactionChart(chartData.satisfaction);
        this.renderMatterTypesChart(chartData.matterTypes);
    }

    renderInteractionVolumeChart(data) {
        const canvas = document.getElementById('interaction-volume-chart');
        if (!canvas || !data) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width = canvas.offsetWidth;
        const height = canvas.height = 300;
        
        ctx.clearRect(0, 0, width, height);
        
        // Simple bar chart implementation
        const barWidth = width / data.length * 0.8;
        const maxValue = Math.max(...data.map(d => d.value));
        
        data.forEach((item, index) => {
            const barHeight = (item.value / maxValue) * (height - 60);
            const x = (index + 0.5) * (width / data.length) - barWidth / 2;
            const y = height - barHeight - 30;
            
            ctx.fillStyle = '#3182ce';
            ctx.fillRect(x, y, barWidth, barHeight);
            
            // Labels
            ctx.fillStyle = '#4a5568';
            ctx.font = '12px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(item.label, x + barWidth / 2, height - 10);
            ctx.fillText(item.value.toString(), x + barWidth / 2, y - 5);
        });
    }

    renderResponseTimeChart(data) {
        const canvas = document.getElementById('response-time-chart');
        if (!canvas || !data) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width = canvas.offsetWidth;
        const height = canvas.height = 300;
        
        ctx.clearRect(0, 0, width, height);
        
        // Simple line chart for response times
        this.drawLineChart(ctx, data, width, height, '#e53e3e');
    }

    renderSatisfactionChart(data) {
        const canvas = document.getElementById('satisfaction-chart');
        if (!canvas || !data) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width = canvas.offsetWidth;
        const height = canvas.height = 300;
        
        ctx.clearRect(0, 0, width, height);
        
        // Simple pie chart for satisfaction
        this.drawPieChart(ctx, data, width, height);
    }

    renderMatterTypesChart(data) {
        const canvas = document.getElementById('matter-types-chart');
        if (!canvas || !data) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width = canvas.offsetWidth;
        const height = canvas.height = 300;
        
        ctx.clearRect(0, 0, width, height);
        
        // Horizontal bar chart for matter types
        this.drawHorizontalBarChart(ctx, data, width, height);
    }

    drawLineChart(ctx, data, width, height, color) {
        if (!data.length) return;
        
        const padding = 40;
        const chartWidth = width - padding * 2;
        const chartHeight = height - padding * 2;
        
        const maxValue = Math.max(...data.map(d => d.value));
        const minValue = Math.min(...data.map(d => d.value));
        const range = maxValue - minValue || 1;
        
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.beginPath();
        
        data.forEach((point, index) => {
            const x = padding + (index / (data.length - 1)) * chartWidth;
            const y = padding + chartHeight - ((point.value - minValue) / range) * chartHeight;
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        
        ctx.stroke();
        
        // Draw points
        ctx.fillStyle = color;
        data.forEach((point, index) => {
            const x = padding + (index / (data.length - 1)) * chartWidth;
            const y = padding + chartHeight - ((point.value - minValue) / range) * chartHeight;
            
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();
        });
    }

    drawPieChart(ctx, data, width, height) {
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = Math.min(width, height) / 2 - 40;
        
        const total = data.reduce((sum, item) => sum + item.value, 0);
        const colors = ['#38a169', '#3182ce', '#d69e2e', '#e53e3e', '#805ad5'];
        
        let currentAngle = -Math.PI / 2;
        
        data.forEach((item, index) => {
            const sliceAngle = (item.value / total) * Math.PI * 2;
            
            ctx.fillStyle = colors[index % colors.length];
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
            ctx.closePath();
            ctx.fill();
            
            // Labels
            const labelAngle = currentAngle + sliceAngle / 2;
            const labelX = centerX + Math.cos(labelAngle) * (radius + 20);
            const labelY = centerY + Math.sin(labelAngle) * (radius + 20);
            
            ctx.fillStyle = '#4a5568';
            ctx.font = '12px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(item.label, labelX, labelY);
            
            currentAngle += sliceAngle;
        });
    }

    drawHorizontalBarChart(ctx, data, width, height) {
        const padding = 40;
        const barHeight = (height - padding * 2) / data.length * 0.8;
        const maxValue = Math.max(...data.map(d => d.value));
        
        data.forEach((item, index) => {
            const barWidth = (item.value / maxValue) * (width - padding * 2 - 100);
            const x = padding + 100;
            const y = padding + index * (height - padding * 2) / data.length;
            
            ctx.fillStyle = '#3182ce';
            ctx.fillRect(x, y, barWidth, barHeight);
            
            // Labels
            ctx.fillStyle = '#4a5568';
            ctx.font = '12px sans-serif';
            ctx.textAlign = 'right';
            ctx.fillText(item.label, x - 10, y + barHeight / 2 + 4);
            
            ctx.textAlign = 'left';
            ctx.fillText(item.value.toString(), x + barWidth + 5, y + barHeight / 2 + 4);
        });
    }

    renderMetricsTable(metrics) {
        const tbody = document.getElementById('metrics-table-body');
        if (!tbody || !metrics) return;

        tbody.innerHTML = metrics.map(metric => `
            <tr>
                <td>${metric.name}</td>
                <td>${metric.current}</td>
                <td>${metric.previous}</td>
                <td class="${metric.change >= 0 ? 'positive' : 'negative'}">
                    ${metric.change >= 0 ? '+' : ''}${metric.change}%
                </td>
                <td>
                    <canvas class="metric-trend" width="60" height="20" data-trend='${JSON.stringify(metric.trend)}'></canvas>
                </td>
                <td>
                    <span class="status-badge ${metric.status}">${metric.status}</span>
                </td>
            </tr>
        `).join('');

        // Render trend sparklines
        tbody.querySelectorAll('.metric-trend').forEach(canvas => {
            const trend = JSON.parse(canvas.dataset.trend);
            this.renderMiniChart(canvas, trend);
        });
    }

    renderInsights(insights) {
        const container = document.getElementById('insights-grid');
        if (!container || !insights) return;

        container.innerHTML = insights.map(insight => `
            <div class="insight-card ${insight.type}">
                <div class="insight-title">${insight.title}</div>
                <div class="insight-description">${insight.description}</div>
                <a href="#" class="insight-action">
                    ${insight.action} <i class="fas fa-arrow-right"></i>
                </a>
            </div>
        `).join('');
    }

    async generateInsights() {
        try {
            const button = document.getElementById('generate-insights');
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
            button.disabled = true;

            const response = await this.apiCall('/api/analytics/generate-insights', 'POST');
            this.renderInsights(response.insights);
            
            button.innerHTML = '<i class="fas fa-magic"></i> Generate Insights';
            button.disabled = false;
            
            this.showSuccess('AI insights generated successfully');
        } catch (error) {
            console.error('Failed to generate insights:', error);
            this.showError('Failed to generate insights');
        }
    }

    filterMetricsTable(searchTerm, category = 'all') {
        const rows = document.querySelectorAll('#metrics-table-body tr');
        
        rows.forEach(row => {
            const metric = row.cells[0].textContent.toLowerCase();
            const status = row.cells[5].textContent.toLowerCase();
            
            const matchesSearch = !searchTerm || metric.includes(searchTerm.toLowerCase());
            const matchesCategory = category === 'all' || status.includes(category);
            
            row.style.display = matchesSearch && matchesCategory ? '' : 'none';
        });
    }

    updateChartType(chartId, type) {
        // Implementation for changing chart types
        console.log(`Updating chart ${chartId} to type ${type}`);
        // This would update the chart rendering based on the selected type
    }

    exportAnalytics() {
        // Create comprehensive analytics report
        const reportData = {
            generatedAt: new Date().toISOString(),
            dateRange: this.dateRange,
            // Include all analytics data
        };

        const blob = new Blob([JSON.stringify(reportData, null, 2)], { 
            type: 'application/json' 
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `hermes-analytics-${Date.now()}.json`;
        a.click();
        
        URL.revokeObjectURL(url);
        this.showSuccess('Analytics report exported successfully');
    }

    startPeriodicUpdates() {
        // Update analytics every 5 minutes
        this.updateInterval = setInterval(() => {
            this.loadAnalyticsData();
        }, 300000);
    }

    stopPeriodicUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    async apiCall(endpoint, method = 'GET', body = null) {
        // Use the main app's API call method if available
        if (window.HermesApp) {
            return window.HermesApp.apiCall(endpoint, method, body);
        }
        
        // Fallback implementation
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        // Only include body for non-GET requests
        if (body && method !== 'GET') {
            options.body = JSON.stringify(body);
        }
        
        const response = await fetch(endpoint, options);
        
        if (!response.ok) {
            throw new Error(`API call failed: ${response.status}`);
        }
        
        return response.json();
    }

    showError(message) {
        if (window.HermesApp) {
            window.HermesApp.showToast(message, 'error');
        }
    }

    showSuccess(message) {
        if (window.HermesApp) {
            window.HermesApp.showToast(message, 'success');
        }
    }
}

// Initialize when script loads
window.Analytics = new Analytics();