// Agentic CRM - API Service

/**
 * API service for handling HTTP requests
 */
class APIService {
    constructor() {
        this.baseURL = CONFIG.API_BASE_URL;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
        };
    }

    /**
     * Get authorization header
     */
    getAuthHeader() {
        const token = Utils.storage.get(CONFIG.TOKEN_KEY);
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    }

    /**
     * Make HTTP request
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                ...this.defaultHeaders,
                ...this.getAuthHeader(),
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            // Handle authentication errors
            if (response.status === 401) {
                this.handleAuthError();
                throw new Error(CONFIG.ERRORS.unauthorized);
            }

            // Handle other HTTP errors
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || this.getErrorMessage(response.status));
            }

            // Return response data
            const data = await response.json();
            return data;

        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error(CONFIG.ERRORS.network);
            }
            throw error;
        }
    }

    /**
     * GET request
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        
        return this.request(url, {
            method: 'GET'
        });
    }

    /**
     * POST request
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT request
     */
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE request
     */
    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }

    /**
     * Upload file
     */
    async upload(endpoint, file, additionalData = {}) {
        const formData = new FormData();
        formData.append('file', file);
        
        Object.keys(additionalData).forEach(key => {
            formData.append(key, additionalData[key]);
        });

        return this.request(endpoint, {
            method: 'POST',
            headers: {
                // Remove Content-Type to let browser set it with boundary
                ...this.getAuthHeader()
            },
            body: formData
        });
    }

    /**
     * Handle authentication errors
     */
    handleAuthError() {
        Utils.storage.remove(CONFIG.TOKEN_KEY);
        Utils.storage.remove(CONFIG.USER_KEY);
        
        // Redirect to login if not already there
        if (!window.location.pathname.includes('login')) {
            window.location.href = '/login';
        }
    }

    /**
     * Get error message for HTTP status
     */
    getErrorMessage(status) {
        switch (status) {
            case 400:
                return CONFIG.ERRORS.validation;
            case 401:
                return CONFIG.ERRORS.unauthorized;
            case 403:
                return CONFIG.ERRORS.forbidden;
            case 404:
                return CONFIG.ERRORS.not_found;
            case 500:
                return CONFIG.ERRORS.server;
            default:
                return CONFIG.ERRORS.server;
        }
    }
}

/**
 * CRM API endpoints
 */
class CRMAPI extends APIService {
    
    // Authentication
    async login(credentials) {
        return this.post('/auth/login', credentials);
    }

    async register(userData) {
        return this.post('/auth/register', userData);
    }

    async logout() {
        return this.post('/auth/logout');
    }

    async getProfile() {
        return this.get('/auth/profile');
    }

    async updateProfile(data) {
        return this.put('/auth/profile', data);
    }

    async changePassword(data) {
        return this.put('/auth/change-password', data);
    }

    // Dashboard
    async getDashboardStats() {
        return this.get('/dashboard/stats');
    }

    async getRecentActivities(limit = 10) {
        return this.get('/dashboard/recent-activities', { limit });
    }

    async getUpcomingTasks(limit = 10) {
        return this.get('/dashboard/upcoming-tasks', { limit });
    }

    async getPipelineOverview() {
        return this.get('/dashboard/pipeline');
    }

    async getHotLeads(limit = 5) {
        return this.get('/dashboard/hot-leads', { limit });
    }

    async getAIInsights() {
        return this.get('/dashboard/ai-insights');
    }

    async getNotifications() {
        return this.get('/dashboard/notifications');
    }

    // Contacts
    async getContacts(params = {}) {
        return this.get('/crm/contacts', params);
    }

    async getContact(id) {
        return this.get(`/crm/contacts/${id}`);
    }

    async createContact(data) {
        return this.post('/crm/contacts', data);
    }

    async updateContact(id, data) {
        return this.put(`/crm/contacts/${id}`, data);
    }

    async deleteContact(id) {
        return this.delete(`/crm/contacts/${id}`);
    }

    async searchContacts(query) {
        return this.get('/crm/search', { q: query, type: 'contacts' });
    }

    // Companies
    async getCompanies(params = {}) {
        return this.get('/crm/companies', params);
    }

    async getCompany(id) {
        return this.get(`/crm/companies/${id}`);
    }

    async createCompany(data) {
        return this.post('/crm/companies', data);
    }

    async updateCompany(id, data) {
        return this.put(`/crm/companies/${id}`, data);
    }

    async deleteCompany(id) {
        return this.delete(`/crm/companies/${id}`);
    }

    // Deals
    async getDeals(params = {}) {
        return this.get('/crm/deals', params);
    }

    async getDeal(id) {
        return this.get(`/crm/deals/${id}`);
    }

    async createDeal(data) {
        return this.post('/crm/deals', data);
    }

    async updateDeal(id, data) {
        return this.put(`/crm/deals/${id}`, data);
    }

    async deleteDeal(id) {
        return this.delete(`/crm/deals/${id}`);
    }

    // Tasks
    async getTasks(params = {}) {
        return this.get('/crm/tasks', params);
    }

    async getTask(id) {
        return this.get(`/crm/tasks/${id}`);
    }

    async createTask(data) {
        return this.post('/crm/tasks', data);
    }

    async updateTask(id, data) {
        return this.put(`/crm/tasks/${id}`, data);
    }

    async deleteTask(id) {
        return this.delete(`/crm/tasks/${id}`);
    }

    async completeTask(id) {
        return this.put(`/crm/tasks/${id}`, { status: 'completed' });
    }

    // Activities
    async getActivities(params = {}) {
        return this.get('/crm/activities', params);
    }

    async getActivity(id) {
        return this.get(`/crm/activities/${id}`);
    }

    async createActivity(data) {
        return this.post('/crm/activities', data);
    }

    async updateActivity(id, data) {
        return this.put(`/crm/activities/${id}`, data);
    }

    async deleteActivity(id) {
        return this.delete(`/crm/activities/${id}`);
    }

    // Analytics
    async getAnalytics(params = {}) {
        return this.get('/crm/analytics', params);
    }

    // Memory System
    async addMemory(data) {
        return this.post('/memory/add', data);
    }

    async searchMemories(query, params = {}) {
        return this.get('/memory/search', { q: query, ...params });
    }

    async getMemoryStats() {
        return this.get('/memory/stats');
    }

    async optimizeMemories() {
        return this.post('/memory/optimize');
    }

    async getRelatedMemories(memoryId) {
        return this.get(`/memory/related/${memoryId}`);
    }

    async boostMemoryRelevance(memoryId, factor = 1.1) {
        return this.post(`/memory/boost/${memoryId}`, { factor });
    }

    async getMemoryTypes() {
        return this.get('/memory/types');
    }

    async getMemoryCategories() {
        return this.get('/memory/categories');
    }

    // AI Services
    async analyzeConversation(data) {
        return this.post('/ai/analyze/conversation', data);
    }

    async analyzeEmail(data) {
        return this.post('/ai/analyze/email', data);
    }

    async generateProposal(data) {
        return this.post('/ai/generate/proposal', data);
    }

    async generateEmailResponse(data) {
        return this.post('/ai/generate/email-response', data);
    }

    async predictDealOutcome(dealId) {
        return this.get(`/ai/predict/deal/${dealId}`);
    }

    async getContactInsights(contactId) {
        return this.get(`/ai/insights/contact/${contactId}`);
    }

    async getDealInsights(dealId) {
        return this.get(`/ai/insights/deal/${dealId}`);
    }

    async getRecommendations() {
        return this.get('/ai/recommendations');
    }

    // Global Search
    async globalSearch(query) {
        return this.get('/crm/search', { q: query });
    }
}

/**
 * Notification service for handling toast messages
 */
class NotificationService {
    constructor() {
        this.container = null;
        this.notifications = [];
        this.init();
    }

    init() {
        this.container = document.getElementById('notifications-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'notifications-container';
            this.container.className = 'notifications-container';
            document.body.appendChild(this.container);
        }
    }

    show(message, type = 'info', duration = CONFIG.NOTIFICATION_DURATION) {
        const notification = this.create(message, type);
        this.container.appendChild(notification);
        this.notifications.push(notification);

        // Limit number of notifications
        if (this.notifications.length > CONFIG.MAX_NOTIFICATIONS) {
            const oldest = this.notifications.shift();
            this.remove(oldest);
        }

        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => this.remove(notification), duration);
        }

        return notification;
    }

    create(message, type) {
        const notification = document.createElement('div');
        notification.className = `toast ${type}`;
        notification.innerHTML = `
            <div class="toast-header">
                <div class="toast-title">${this.getTitle(type)}</div>
                <button class="toast-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="toast-message">${message}</div>
        `;

        return notification;
    }

    remove(notification) {
        if (notification && notification.parentNode) {
            notification.parentNode.removeChild(notification);
            const index = this.notifications.indexOf(notification);
            if (index > -1) {
                this.notifications.splice(index, 1);
            }
        }
    }

    getTitle(type) {
        switch (type) {
            case 'success': return 'Success';
            case 'warning': return 'Warning';
            case 'error': return 'Error';
            case 'info':
            default: return 'Info';
        }
    }

    success(message, duration) {
        return this.show(message, 'success', duration);
    }

    error(message, duration) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration) {
        return this.show(message, 'info', duration);
    }

    clear() {
        this.notifications.forEach(notification => this.remove(notification));
        this.notifications = [];
    }
}

// Create global instances
const api = new CRMAPI();
const notifications = new NotificationService();

// Export for global use
window.api = api;
window.notifications = notifications;
