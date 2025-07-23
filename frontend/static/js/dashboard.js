// Agentic CRM - Dashboard Module

/**
 * Dashboard controller for managing the main dashboard view
 */
class Dashboard {
    constructor() {
        this.container = null;
        this.refreshInterval = null;
        this.isLoading = false;
        this.data = {};
    }

    /**
     * Initialize dashboard
     */
    async init(container) {
        this.container = container;
        await this.render();
        await this.loadData();
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    /**
     * Render dashboard HTML structure
     */
    async render() {
        if (!this.container) return;

        this.container.innerHTML = `
            <div class="dashboard-container">
                <!-- Dashboard Header -->
                <div class="dashboard-header">
                    <div class="welcome-section">
                        <h1>Welcome back, <span id="dashboard-user-name">Loading...</span>!</h1>
                        <p class="dashboard-subtitle">Here's what's happening with your business today.</p>
                    </div>
                    <div class="dashboard-actions">
                        <button class="btn btn-primary" id="refresh-dashboard">
                            <i class="fas fa-sync-alt"></i>
                            Refresh
                        </button>
                    </div>
                </div>

                <!-- Key Metrics Grid -->
                <div class="dashboard-grid" id="metrics-grid">
                    <!-- Metrics will be loaded here -->
                </div>

                <!-- Main Content Grid -->
                <div class="dashboard-content-grid">
                    <!-- Recent Activities -->
                    <div class="dashboard-card">
                        <div class="card-header">
                            <h3 class="card-title">Recent Activities</h3>
                            <a href="#activities" class="card-action">View All</a>
                        </div>
                        <div class="card-content">
                            <div class="activity-feed" id="recent-activities">
                                <div class="loading">Loading activities...</div>
                            </div>
                        </div>
                    </div>

                    <!-- Upcoming Tasks -->
                    <div class="dashboard-card">
                        <div class="card-header">
                            <h3 class="card-title">Upcoming Tasks</h3>
                            <a href="#tasks" class="card-action">View All</a>
                        </div>
                        <div class="card-content">
                            <div class="task-list" id="upcoming-tasks">
                                <div class="loading">Loading tasks...</div>
                            </div>
                        </div>
                    </div>

                    <!-- Deal Pipeline -->
                    <div class="dashboard-card full-width">
                        <div class="card-header">
                            <h3 class="card-title">Deal Pipeline</h3>
                            <a href="#deals" class="card-action">View All Deals</a>
                        </div>
                        <div class="card-content">
                            <div class="pipeline-container" id="deal-pipeline">
                                <div class="loading">Loading pipeline...</div>
                            </div>
                        </div>
                    </div>

                    <!-- Hot Leads -->
                    <div class="dashboard-card">
                        <div class="card-header">
                            <h3 class="card-title">Hot Leads</h3>
                            <a href="#contacts" class="card-action">View All Contacts</a>
                        </div>
                        <div class="card-content">
                            <div class="leads-list" id="hot-leads">
                                <div class="loading">Loading leads...</div>
                            </div>
                        </div>
                    </div>

                    <!-- AI Insights -->
                    <div class="dashboard-card">
                        <div class="card-header">
                            <h3 class="card-title">AI Insights</h3>
                            <a href="#ai-insights" class="card-action">View All</a>
                        </div>
                        <div class="card-content">
                            <div class="insights-list" id="ai-insights">
                                <div class="loading">Loading insights...</div>
                            </div>
                        </div>
                    </div>

                    <!-- Notifications -->
                    <div class="dashboard-card">
                        <div class="card-header">
                            <h3 class="card-title">Notifications</h3>
                            <button class="card-action" id="mark-all-read">Mark All Read</button>
                        </div>
                        <div class="card-content">
                            <div class="notifications-list" id="dashboard-notifications">
                                <div class="loading">Loading notifications...</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Update user name
        const user = auth.getCurrentUser();
        const userNameElement = document.getElementById('dashboard-user-name');
        if (userNameElement && user) {
            userNameElement.textContent = user.first_name || user.username || 'User';
        }
    }

    /**
     * Load all dashboard data
     */
    async loadData() {
        if (this.isLoading) return;
        this.isLoading = true;

        try {
            // Load data in parallel
            const [
                stats,
                activities,
                tasks,
                pipeline,
                leads,
                insights,
                notifications
            ] = await Promise.allSettled([
                api.getDashboardStats(),
                api.getRecentActivities(5),
                api.getUpcomingTasks(5),
                api.getPipelineOverview(),
                api.getHotLeads(5),
                api.getAIInsights(),
                api.getNotifications()
            ]);

            // Process results
            this.data = {
                stats: stats.status === 'fulfilled' ? stats.value : null,
                activities: activities.status === 'fulfilled' ? activities.value : [],
                tasks: tasks.status === 'fulfilled' ? tasks.value : [],
                pipeline: pipeline.status === 'fulfilled' ? pipeline.value : null,
                leads: leads.status === 'fulfilled' ? leads.value : [],
                insights: insights.status === 'fulfilled' ? insights.value : [],
                notifications: notifications.status === 'fulfilled' ? notifications.value : []
            };

            // Render components
            this.renderMetrics();
            this.renderActivities();
            this.renderTasks();
            this.renderPipeline();
            this.renderLeads();
            this.renderInsights();
            this.renderNotifications();

        } catch (error) {
            console.error('Dashboard data loading error:', error);
            notifications.error('Failed to load dashboard data');
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Render key metrics
     */
    renderMetrics() {
        const metricsGrid = document.getElementById('metrics-grid');
        if (!metricsGrid || !this.data.stats) return;

        const stats = this.data.stats;
        
        metricsGrid.innerHTML = `
            <div class="dashboard-card metric-card">
                <div class="card-header">
                    <div class="card-icon primary">
                        <i class="fas fa-users"></i>
                    </div>
                </div>
                <div class="card-content">
                    <div class="metric-value">${stats.total_contacts || 0}</div>
                    <div class="metric-label">Total Contacts</div>
                    <div class="metric-change ${stats.contacts_change >= 0 ? 'positive' : 'negative'}">
                        <i class="fas fa-arrow-${stats.contacts_change >= 0 ? 'up' : 'down'}"></i>
                        ${Math.abs(stats.contacts_change || 0)}% this month
                    </div>
                </div>
            </div>

            <div class="dashboard-card metric-card">
                <div class="card-header">
                    <div class="card-icon success">
                        <i class="fas fa-handshake"></i>
                    </div>
                </div>
                <div class="card-content">
                    <div class="metric-value">${stats.active_deals || 0}</div>
                    <div class="metric-label">Active Deals</div>
                    <div class="metric-change ${stats.deals_change >= 0 ? 'positive' : 'negative'}">
                        <i class="fas fa-arrow-${stats.deals_change >= 0 ? 'up' : 'down'}"></i>
                        ${Math.abs(stats.deals_change || 0)}% this month
                    </div>
                </div>
            </div>

            <div class="dashboard-card metric-card">
                <div class="card-header">
                    <div class="card-icon warning">
                        <i class="fas fa-dollar-sign"></i>
                    </div>
                </div>
                <div class="card-content">
                    <div class="metric-value">${Utils.formatCurrency(stats.pipeline_value || 0)}</div>
                    <div class="metric-label">Pipeline Value</div>
                    <div class="metric-change ${stats.pipeline_change >= 0 ? 'positive' : 'negative'}">
                        <i class="fas fa-arrow-${stats.pipeline_change >= 0 ? 'up' : 'down'}"></i>
                        ${Math.abs(stats.pipeline_change || 0)}% this month
                    </div>
                </div>
            </div>

            <div class="dashboard-card metric-card">
                <div class="card-header">
                    <div class="card-icon error">
                        <i class="fas fa-tasks"></i>
                    </div>
                </div>
                <div class="card-content">
                    <div class="metric-value">${stats.overdue_tasks || 0}</div>
                    <div class="metric-label">Overdue Tasks</div>
                    <div class="progress-bar">
                        <div class="progress-fill error" style="width: ${Math.min((stats.overdue_tasks / (stats.total_tasks || 1)) * 100, 100)}%"></div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render recent activities
     */
    renderActivities() {
        const activitiesContainer = document.getElementById('recent-activities');
        if (!activitiesContainer) return;

        const activities = this.data.activities || [];

        if (activities.length === 0) {
            activitiesContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-calendar-alt"></i>
                    <p>No recent activities</p>
                </div>
            `;
            return;
        }

        activitiesContainer.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon ${activity.type}">
                    <i class="fas fa-${this.getActivityIcon(activity.type)}"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-title">${activity.title}</div>
                    <div class="activity-description">${activity.description || ''}</div>
                    <div class="activity-time">${Utils.formatRelativeTime(activity.created_at)}</div>
                </div>
            </div>
        `).join('');
    }

    /**
     * Render upcoming tasks
     */
    renderTasks() {
        const tasksContainer = document.getElementById('upcoming-tasks');
        if (!tasksContainer) return;

        const tasks = this.data.tasks || [];

        if (tasks.length === 0) {
            tasksContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-check-circle"></i>
                    <p>No upcoming tasks</p>
                </div>
            `;
            return;
        }

        tasksContainer.innerHTML = tasks.map(task => `
            <div class="task-item">
                <div class="task-checkbox ${task.status === 'completed' ? 'checked' : ''}" 
                     onclick="dashboard.toggleTask(${task.id})">
                    ${task.status === 'completed' ? '<i class="fas fa-check"></i>' : ''}
                </div>
                <div class="task-content">
                    <div class="task-title ${task.status === 'completed' ? 'completed' : ''}">${task.title}</div>
                    <div class="task-meta">
                        <span class="task-priority ${task.priority}">${Utils.capitalize(task.priority)}</span>
                        <span class="task-due">${Utils.formatDate(task.due_date)}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    /**
     * Render deal pipeline
     */
    renderPipeline() {
        const pipelineContainer = document.getElementById('deal-pipeline');
        if (!pipelineContainer) return;

        const pipeline = this.data.pipeline;
        if (!pipeline || !pipeline.stages) {
            pipelineContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-chart-line"></i>
                    <p>No pipeline data available</p>
                </div>
            `;
            return;
        }

        pipelineContainer.innerHTML = `
            <div class="pipeline-stages">
                ${pipeline.stages.map(stage => `
                    <div class="pipeline-stage">
                        <div class="stage-header">
                            <div class="stage-title">${stage.name}</div>
                            <div class="stage-count">${stage.deals?.length || 0}</div>
                        </div>
                        <div class="stage-deals">
                            ${(stage.deals || []).map(deal => `
                                <div class="deal-card" onclick="app.navigateToView('deals')">
                                    <div class="deal-title">${deal.title}</div>
                                    <div class="deal-company">${deal.company_name || 'No Company'}</div>
                                    <div class="deal-value">${Utils.formatCurrency(deal.value)}</div>
                                    <div class="deal-probability">
                                        <div class="probability-bar">
                                            <div class="probability-fill" style="width: ${deal.probability}%"></div>
                                        </div>
                                        <span>${deal.probability}%</span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    /**
     * Render hot leads
     */
    renderLeads() {
        const leadsContainer = document.getElementById('hot-leads');
        if (!leadsContainer) return;

        const leads = this.data.leads || [];

        if (leads.length === 0) {
            leadsContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-fire"></i>
                    <p>No hot leads</p>
                </div>
            `;
            return;
        }

        leadsContainer.innerHTML = leads.map(lead => `
            <div class="lead-item" onclick="app.navigateToView('contacts')">
                <div class="lead-avatar" style="background-color: ${Utils.getAvatarColor(lead.full_name)}">
                    ${Utils.getInitials(lead.full_name)}
                </div>
                <div class="lead-info">
                    <div class="lead-name">${lead.full_name}</div>
                    <div class="lead-company">${lead.company_name || 'No Company'}</div>
                    <div class="lead-score">
                        <span class="score-badge ${this.getScoreBadgeClass(lead.lead_score)}">${lead.lead_score}</span>
                        <span class="score-label">Lead Score</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    /**
     * Render AI insights
     */
    renderInsights() {
        const insightsContainer = document.getElementById('ai-insights');
        if (!insightsContainer) return;

        const insights = this.data.insights || [];

        if (insights.length === 0) {
            insightsContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-lightbulb"></i>
                    <p>No AI insights available</p>
                </div>
            `;
            return;
        }

        insightsContainer.innerHTML = insights.map(insight => `
            <div class="insight-item">
                <div class="insight-type">${insight.type}</div>
                <div class="insight-content">${insight.content}</div>
                <div class="insight-actions">
                    ${insight.actions?.map(action => `
                        <a href="${action.url}" class="insight-action">${action.label}</a>
                    `).join('') || ''}
                </div>
            </div>
        `).join('');
    }

    /**
     * Render notifications
     */
    renderNotifications() {
        const notificationsContainer = document.getElementById('dashboard-notifications');
        if (!notificationsContainer) return;

        const notifications = this.data.notifications || [];

        if (notifications.length === 0) {
            notificationsContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-bell"></i>
                    <p>No notifications</p>
                </div>
            `;
            return;
        }

        notificationsContainer.innerHTML = notifications.slice(0, 5).map(notification => `
            <div class="notification-item ${notification.read ? '' : 'unread'}">
                <div class="notification-icon ${notification.type}">
                    <i class="fas fa-${this.getNotificationIcon(notification.type)}"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-title">${notification.title}</div>
                    <div class="notification-message">${notification.message}</div>
                    <div class="notification-time">${Utils.formatRelativeTime(notification.created_at)}</div>
                </div>
            </div>
        `).join('');
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refresh();
            });
        }

        // Mark all notifications as read
        const markAllReadBtn = document.getElementById('mark-all-read');
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', () => {
                this.markAllNotificationsRead();
            });
        }
    }

    /**
     * Toggle task completion
     */
    async toggleTask(taskId) {
        try {
            await api.completeTask(taskId);
            notifications.success('Task updated successfully');
            await this.loadData(); // Refresh data
        } catch (error) {
            console.error('Task toggle error:', error);
            notifications.error('Failed to update task');
        }
    }

    /**
     * Mark all notifications as read
     */
    async markAllNotificationsRead() {
        try {
            // TODO: Implement mark all as read API
            notifications.success('All notifications marked as read');
            await this.loadData(); // Refresh data
        } catch (error) {
            console.error('Mark notifications read error:', error);
            notifications.error('Failed to mark notifications as read');
        }
    }

    /**
     * Refresh dashboard data
     */
    async refresh() {
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Refreshing...';
            refreshBtn.disabled = true;
        }

        try {
            await this.loadData();
            notifications.success('Dashboard refreshed');
        } catch (error) {
            notifications.error('Failed to refresh dashboard');
        } finally {
            if (refreshBtn) {
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
                refreshBtn.disabled = false;
            }
        }
    }

    /**
     * Start auto-refresh
     */
    startAutoRefresh() {
        // Refresh every 5 minutes
        this.refreshInterval = setInterval(() => {
            this.loadData();
        }, 5 * 60 * 1000);
    }

    /**
     * Stop auto-refresh
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    /**
     * Helper methods
     */
    getActivityIcon(type) {
        const icons = {
            call: 'phone',
            email: 'envelope',
            meeting: 'calendar',
            note: 'sticky-note',
            task: 'check-square'
        };
        return icons[type] || 'circle';
    }

    getNotificationIcon(type) {
        const icons = {
            info: 'info-circle',
            warning: 'exclamation-triangle',
            error: 'times-circle',
            success: 'check-circle'
        };
        return icons[type] || 'bell';
    }

    getScoreBadgeClass(score) {
        if (score >= 80) return 'high';
        if (score >= 50) return 'medium';
        return 'low';
    }

    /**
     * Cleanup
     */
    destroy() {
        this.stopAutoRefresh();
    }
}

// Create global instance
const dashboard = new Dashboard();

// Export for global use
window.dashboard = dashboard;
