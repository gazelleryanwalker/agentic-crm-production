// Agentic CRM - Main Application Controller

/**
 * Main application controller
 */
class AgenticCRM {
    constructor() {
        this.currentView = 'dashboard';
        this.isLoading = true;
        this.sidebarCollapsed = Utils.storage.get(CONFIG.SIDEBAR_COLLAPSED_KEY, false);
        this.init();
    }

    /**
     * Initialize the application
     */
    async init() {
        try {
            // Show loading screen
            this.showLoadingScreen();
            
            // Initialize components
            await this.initializeApp();
            
            // Check authentication
            const isAuthenticated = await auth.checkAuth();
            
            if (isAuthenticated) {
                // Show main app
                await this.showMainApp();
            } else {
                // Show login screen
                this.showLoginScreen();
            }
            
        } catch (error) {
            console.error('App initialization error:', error);
            notifications.error('Failed to initialize application');
            this.showLoginScreen();
        } finally {
            this.hideLoadingScreen();
        }
    }

    /**
     * Show loading screen
     */
    showLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.classList.remove('hidden');
        }
    }

    /**
     * Hide loading screen
     */
    hideLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            setTimeout(() => {
                loadingScreen.classList.add('hidden');
            }, 1000); // Show loading for at least 1 second for better UX
        }
    }

    /**
     * Show login screen
     */
    showLoginScreen() {
        const loginScreen = document.getElementById('login-screen');
        const mainApp = document.getElementById('main-app');
        
        if (loginScreen) loginScreen.classList.remove('hidden');
        if (mainApp) mainApp.classList.add('hidden');
    }

    /**
     * Show main application
     */
    async showMainApp() {
        const loginScreen = document.getElementById('login-screen');
        const mainApp = document.getElementById('main-app');
        
        if (loginScreen) loginScreen.classList.add('hidden');
        if (mainApp) mainApp.classList.remove('hidden');
        
        // Initialize main app components
        await this.initializeMainApp();
    }

    /**
     * Initialize application components
     */
    async initializeApp() {
        // Setup global error handling
        this.setupErrorHandling();
        
        // Setup keyboard shortcuts
        this.setupKeyboardShortcuts();
        
        // Setup sidebar
        this.setupSidebar();
        
        // Setup navigation
        this.setupNavigation();
        
        // Setup search
        this.setupGlobalSearch();
        
        // Setup quick actions
        this.setupQuickActions();
        
        // Setup AI assistant
        this.setupAIAssistant();
    }

    /**
     * Initialize main app after authentication
     */
    async initializeMainApp() {
        // Update user profile display
        userProfile.updateUserDisplay();
        
        // Load dashboard by default
        await this.navigateToView('dashboard');
        
        // Setup periodic data refresh
        this.setupPeriodicRefresh();
        
        // Load notifications
        await this.loadNotifications();
    }

    /**
     * Setup global error handling
     */
    setupErrorHandling() {
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            notifications.error('An unexpected error occurred');
        });

        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            notifications.error('An unexpected error occurred');
        });
    }

    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+K - Global search
            if (e.ctrlKey && e.key === 'k') {
                e.preventDefault();
                this.focusGlobalSearch();
            }
            
            // Ctrl+Shift+C - New contact
            if (e.ctrlKey && e.shiftKey && e.key === 'C') {
                e.preventDefault();
                this.showNewContactModal();
            }
            
            // Ctrl+Shift+D - New deal
            if (e.ctrlKey && e.shiftKey && e.key === 'D') {
                e.preventDefault();
                this.showNewDealModal();
            }
            
            // Ctrl+Shift+T - New task
            if (e.ctrlKey && e.shiftKey && e.key === 'T') {
                e.preventDefault();
                this.showNewTaskModal();
            }
            
            // Ctrl+Shift+A - AI assistant
            if (e.ctrlKey && e.shiftKey && e.key === 'A') {
                e.preventDefault();
                this.toggleAIAssistant();
            }
            
            // Escape - Close modals
            if (e.key === 'Escape') {
                this.closeModals();
            }
        });
    }

    /**
     * Setup sidebar functionality
     */
    setupSidebar() {
        const sidebar = document.querySelector('.sidebar');
        const sidebarToggle = document.getElementById('sidebar-toggle');
        
        // Apply stored sidebar state
        if (this.sidebarCollapsed && sidebar) {
            sidebar.classList.add('collapsed');
        }
        
        // Sidebar toggle
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                this.toggleSidebar();
            });
        }
    }

    /**
     * Toggle sidebar
     */
    toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        if (!sidebar) return;
        
        this.sidebarCollapsed = !this.sidebarCollapsed;
        sidebar.classList.toggle('collapsed', this.sidebarCollapsed);
        
        // Store state
        Utils.storage.set(CONFIG.SIDEBAR_COLLAPSED_KEY, this.sidebarCollapsed);
    }

    /**
     * Setup navigation
     */
    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link[data-view]');
        
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const view = link.dataset.view;
                this.navigateToView(view);
            });
        });
    }

    /**
     * Navigate to a specific view
     */
    async navigateToView(viewName) {
        if (this.currentView === viewName) return;
        
        try {
            // Update navigation state
            this.updateNavigation(viewName);
            
            // Update page title and breadcrumb
            this.updatePageHeader(viewName);
            
            // Show view
            await this.showView(viewName);
            
            // Update current view
            this.currentView = viewName;
            
            // Update URL
            Utils.updateUrl({ view: viewName });
            
        } catch (error) {
            console.error('Navigation error:', error);
            notifications.error('Failed to load view');
        }
    }

    /**
     * Update navigation active state
     */
    updateNavigation(viewName) {
        // Remove active class from all nav items
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Add active class to current nav item
        const currentNavLink = document.querySelector(`[data-view="${viewName}"]`);
        if (currentNavLink) {
            currentNavLink.closest('.nav-item').classList.add('active');
        }
    }

    /**
     * Update page header
     */
    updatePageHeader(viewName) {
        const pageTitle = document.getElementById('page-title');
        const breadcrumb = document.getElementById('breadcrumb');
        
        const viewTitles = {
            dashboard: 'Dashboard',
            contacts: 'Contacts',
            deals: 'Deals',
            tasks: 'Tasks',
            activities: 'Activities',
            memory: 'Memory',
            'ai-insights': 'AI Insights',
            analytics: 'Analytics',
            integrations: 'Integrations',
            settings: 'Settings'
        };
        
        const title = viewTitles[viewName] || Utils.camelToTitle(viewName);
        
        if (pageTitle) {
            pageTitle.textContent = title;
        }
        
        if (breadcrumb) {
            breadcrumb.innerHTML = `
                <span>Home</span>
                <i class="fas fa-chevron-right"></i>
                <span>${title}</span>
            `;
        }
    }

    /**
     * Show specific view
     */
    async showView(viewName) {
        // Hide all views
        document.querySelectorAll('.view').forEach(view => {
            view.classList.remove('active');
        });
        
        // Show target view
        const targetView = document.getElementById(`${viewName}-view`);
        if (targetView) {
            targetView.classList.add('active');
            
            // Load view content if needed
            await this.loadViewContent(viewName, targetView);
        }
    }

    /**
     * Load content for specific view
     */
    async loadViewContent(viewName, viewElement) {
        // Check if content already loaded
        if (viewElement.dataset.loaded === 'true') {
            return;
        }
        
        try {
            switch (viewName) {
                case 'dashboard':
                    await this.loadDashboard(viewElement);
                    break;
                case 'contacts':
                    await this.loadContacts(viewElement);
                    break;
                case 'deals':
                    await this.loadDeals(viewElement);
                    break;
                case 'tasks':
                    await this.loadTasks(viewElement);
                    break;
                case 'activities':
                    await this.loadActivities(viewElement);
                    break;
                case 'memory':
                    await this.loadMemory(viewElement);
                    break;
                case 'ai-insights':
                    await this.loadAIInsights(viewElement);
                    break;
                case 'analytics':
                    await this.loadAnalytics(viewElement);
                    break;
                case 'settings':
                    await this.loadSettings(viewElement);
                    break;
            }
            
            // Mark as loaded
            viewElement.dataset.loaded = 'true';
            
        } catch (error) {
            console.error(`Error loading ${viewName} view:`, error);
            viewElement.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Failed to load ${Utils.camelToTitle(viewName)}</h3>
                    <p>Please try refreshing the page.</p>
                    <button class="btn btn-primary" onclick="location.reload()">
                        <i class="fas fa-refresh"></i> Refresh
                    </button>
                </div>
            `;
        }
    }

    /**
     * Load dashboard content
     */
    async loadDashboard(viewElement) {
        if (window.dashboard) {
            await window.dashboard.init(viewElement);
        } else {
            viewElement.innerHTML = '<div class="loading">Loading dashboard...</div>';
        }
    }

    /**
     * Load contacts content
     */
    async loadContacts(viewElement) {
        if (window.contacts) {
            await window.contacts.init(viewElement);
        } else {
            viewElement.innerHTML = '<div class="loading">Loading contacts...</div>';
        }
    }

    /**
     * Load deals content
     */
    async loadDeals(viewElement) {
        if (window.deals) {
            await window.deals.init(viewElement);
        } else {
            viewElement.innerHTML = '<div class="loading">Loading deals...</div>';
        }
    }

    /**
     * Load tasks content
     */
    async loadTasks(viewElement) {
        if (window.tasks) {
            await window.tasks.init(viewElement);
        } else {
            viewElement.innerHTML = '<div class="loading">Loading tasks...</div>';
        }
    }

    /**
     * Load activities content
     */
    async loadActivities(viewElement) {
        viewElement.innerHTML = '<div class="loading">Loading activities...</div>';
    }

    /**
     * Load memory content
     */
    async loadMemory(viewElement) {
        if (window.memory) {
            await window.memory.init(viewElement);
        } else {
            viewElement.innerHTML = '<div class="loading">Loading memory...</div>';
        }
    }

    /**
     * Load AI insights content
     */
    async loadAIInsights(viewElement) {
        viewElement.innerHTML = '<div class="loading">Loading AI insights...</div>';
    }

    /**
     * Load analytics content
     */
    async loadAnalytics(viewElement) {
        viewElement.innerHTML = '<div class="loading">Loading analytics...</div>';
    }

    /**
     * Load settings content
     */
    async loadSettings(viewElement) {
        viewElement.innerHTML = '<div class="loading">Loading settings...</div>';
    }

    /**
     * Setup global search
     */
    setupGlobalSearch() {
        const searchInput = document.getElementById('global-search');
        const searchResults = document.getElementById('search-results');
        
        if (!searchInput) return;
        
        const debouncedSearch = Utils.debounce(async (query) => {
            if (query.length >= CONFIG.MIN_SEARCH_LENGTH) {
                await this.performGlobalSearch(query);
            } else {
                this.hideSearchResults();
            }
        }, CONFIG.SEARCH_DEBOUNCE_MS);
        
        searchInput.addEventListener('input', (e) => {
            debouncedSearch(e.target.value.trim());
        });
        
        searchInput.addEventListener('focus', () => {
            if (searchInput.value.trim().length >= CONFIG.MIN_SEARCH_LENGTH) {
                this.showSearchResults();
            }
        });
        
        // Hide search results when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchResults?.contains(e.target)) {
                this.hideSearchResults();
            }
        });
    }

    /**
     * Perform global search
     */
    async performGlobalSearch(query) {
        try {
            const results = await api.globalSearch(query);
            this.displaySearchResults(results);
        } catch (error) {
            console.error('Search error:', error);
            this.hideSearchResults();
        }
    }

    /**
     * Display search results
     */
    displaySearchResults(results) {
        const searchResults = document.getElementById('search-results');
        if (!searchResults) return;
        
        if (!results || results.length === 0) {
            searchResults.innerHTML = '<div class="search-no-results">No results found</div>';
        } else {
            searchResults.innerHTML = results.map(result => `
                <div class="search-result-item" onclick="app.handleSearchResultClick('${result.type}', ${result.id})">
                    <div class="search-result-icon ${result.type}">
                        <i class="fas fa-${this.getSearchResultIcon(result.type)}"></i>
                    </div>
                    <div class="search-result-content">
                        <div class="search-result-title">${result.title}</div>
                        <div class="search-result-subtitle">${result.subtitle || ''}</div>
                    </div>
                </div>
            `).join('');
        }
        
        this.showSearchResults();
    }

    /**
     * Get icon for search result type
     */
    getSearchResultIcon(type) {
        const icons = {
            contact: 'user',
            company: 'building',
            deal: 'handshake',
            task: 'tasks',
            activity: 'calendar-alt',
            memory: 'brain'
        };
        return icons[type] || 'file';
    }

    /**
     * Handle search result click
     */
    handleSearchResultClick(type, id) {
        this.hideSearchResults();
        
        // Navigate to appropriate view and show item
        switch (type) {
            case 'contact':
                this.navigateToView('contacts');
                // TODO: Show contact details
                break;
            case 'deal':
                this.navigateToView('deals');
                // TODO: Show deal details
                break;
            case 'task':
                this.navigateToView('tasks');
                // TODO: Show task details
                break;
            // Add more cases as needed
        }
    }

    /**
     * Show search results
     */
    showSearchResults() {
        const searchResults = document.getElementById('search-results');
        if (searchResults) {
            searchResults.classList.remove('hidden');
        }
    }

    /**
     * Hide search results
     */
    hideSearchResults() {
        const searchResults = document.getElementById('search-results');
        if (searchResults) {
            searchResults.classList.add('hidden');
        }
    }

    /**
     * Focus global search
     */
    focusGlobalSearch() {
        const searchInput = document.getElementById('global-search');
        if (searchInput) {
            searchInput.focus();
        }
    }

    /**
     * Setup quick actions
     */
    setupQuickActions() {
        const quickAddBtn = document.getElementById('quick-add-btn');
        const quickAddMenu = document.getElementById('quick-add-menu');
        
        if (quickAddBtn && quickAddMenu) {
            quickAddBtn.addEventListener('click', () => {
                quickAddMenu.classList.toggle('open');
            });
            
            // Handle quick add actions
            quickAddMenu.addEventListener('click', (e) => {
                const action = e.target.closest('[data-action]')?.dataset.action;
                if (action) {
                    this.handleQuickAction(action);
                    quickAddMenu.classList.remove('open');
                }
            });
            
            // Close menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!quickAddBtn.contains(e.target) && !quickAddMenu.contains(e.target)) {
                    quickAddMenu.classList.remove('open');
                }
            });
        }
    }

    /**
     * Handle quick actions
     */
    handleQuickAction(action) {
        switch (action) {
            case 'add-contact':
                this.showNewContactModal();
                break;
            case 'add-deal':
                this.showNewDealModal();
                break;
            case 'add-task':
                this.showNewTaskModal();
                break;
            case 'log-activity':
                this.showNewActivityModal();
                break;
        }
    }

    /**
     * Setup AI assistant
     */
    setupAIAssistant() {
        const aiAssistantBtn = document.getElementById('ai-assistant-btn');
        const aiAssistantPanel = document.getElementById('ai-assistant-panel');
        
        if (aiAssistantBtn) {
            aiAssistantBtn.addEventListener('click', () => {
                this.toggleAIAssistant();
            });
        }
        
        if (aiAssistantPanel) {
            const closeBtn = aiAssistantPanel.querySelector('.ai-assistant-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    this.closeAIAssistant();
                });
            }
        }
    }

    /**
     * Toggle AI assistant
     */
    toggleAIAssistant() {
        const aiAssistantPanel = document.getElementById('ai-assistant-panel');
        if (aiAssistantPanel) {
            aiAssistantPanel.classList.toggle('open');
        }
    }

    /**
     * Close AI assistant
     */
    closeAIAssistant() {
        const aiAssistantPanel = document.getElementById('ai-assistant-panel');
        if (aiAssistantPanel) {
            aiAssistantPanel.classList.remove('open');
        }
    }

    /**
     * Setup periodic refresh
     */
    setupPeriodicRefresh() {
        // Refresh notifications every 30 seconds
        setInterval(() => {
            this.loadNotifications();
        }, CONFIG.AUTO_SAVE.notification_check);
        
        // Check session every minute
        setInterval(() => {
            auth.checkAuth();
        }, CONFIG.AUTO_SAVE.session_check);
    }

    /**
     * Load notifications
     */
    async loadNotifications() {
        try {
            const notifications = await api.getNotifications();
            this.updateNotificationBadge(notifications.length);
        } catch (error) {
            console.warn('Failed to load notifications:', error);
        }
    }

    /**
     * Update notification badge
     */
    updateNotificationBadge(count) {
        const badge = document.getElementById('notification-count');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'block' : 'none';
        }
    }

    /**
     * Modal helpers
     */
    showNewContactModal() {
        // TODO: Implement contact modal
        notifications.info('New contact modal coming soon');
    }

    showNewDealModal() {
        // TODO: Implement deal modal
        notifications.info('New deal modal coming soon');
    }

    showNewTaskModal() {
        // TODO: Implement task modal
        notifications.info('New task modal coming soon');
    }

    showNewActivityModal() {
        // TODO: Implement activity modal
        notifications.info('New activity modal coming soon');
    }

    closeModals() {
        const modalOverlay = document.getElementById('modal-overlay');
        if (modalOverlay && !modalOverlay.classList.contains('hidden')) {
            modalOverlay.classList.add('hidden');
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new AgenticCRM();
});

// Export for global use
window.AgenticCRM = AgenticCRM;
