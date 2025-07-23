// Agentic CRM - Configuration and Constants

const CONFIG = {
    // API Configuration
    API_BASE_URL: window.location.origin.includes('localhost') 
        ? 'http://localhost:5001/api' 
        : '/api',
    
    // Authentication
    TOKEN_KEY: 'agentic_crm_token',
    USER_KEY: 'agentic_crm_user',
    TOKEN_REFRESH_THRESHOLD: 5 * 60 * 1000, // 5 minutes before expiry
    
    // UI Configuration
    SIDEBAR_COLLAPSED_KEY: 'sidebar_collapsed',
    THEME_KEY: 'theme_preference',
    
    // Pagination
    DEFAULT_PAGE_SIZE: 20,
    MAX_PAGE_SIZE: 100,
    
    // Search
    SEARCH_DEBOUNCE_MS: 300,
    MIN_SEARCH_LENGTH: 2,
    
    // Notifications
    NOTIFICATION_DURATION: 5000,
    MAX_NOTIFICATIONS: 5,
    
    // AI Assistant
    AI_CHAT_MAX_MESSAGES: 50,
    AI_RESPONSE_TIMEOUT: 30000,
    
    // Memory System
    MEMORY_SEARCH_LIMIT: 10,
    MEMORY_RELEVANCE_THRESHOLD: 0.3,
    
    // File Upload
    MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
    ALLOWED_FILE_TYPES: [
        'image/jpeg',
        'image/png',
        'image/gif',
        'application/pdf',
        'text/plain',
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ],
    
    // Chart Colors
    CHART_COLORS: {
        primary: '#2563eb',
        success: '#22c55e',
        warning: '#f59e0b',
        error: '#ef4444',
        info: '#06b6d4',
        gray: '#64748b'
    },
    
    // Status Colors
    STATUS_COLORS: {
        // Deal Stages
        'prospecting': '#64748b',
        'qualification': '#3b82f6',
        'proposal': '#f59e0b',
        'negotiation': '#ef4444',
        'closed_won': '#22c55e',
        'closed_lost': '#6b7280',
        
        // Lead Status
        'new': '#3b82f6',
        'contacted': '#f59e0b',
        'qualified': '#22c55e',
        'unqualified': '#6b7280',
        
        // Task Priority
        'high': '#ef4444',
        'medium': '#f59e0b',
        'low': '#22c55e',
        
        // Activity Types
        'call': '#3b82f6',
        'email': '#06b6d4',
        'meeting': '#8b5cf6',
        'note': '#64748b'
    },
    
    // Date Formats
    DATE_FORMATS: {
        display: 'MMM DD, YYYY',
        displayWithTime: 'MMM DD, YYYY HH:mm',
        input: 'YYYY-MM-DD',
        inputWithTime: 'YYYY-MM-DDTHH:mm',
        api: 'YYYY-MM-DDTHH:mm:ss.SSSZ'
    },
    
    // Currency
    CURRENCY: {
        symbol: '$',
        code: 'USD',
        locale: 'en-US'
    },
    
    // Validation Rules
    VALIDATION: {
        email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        phone: /^[\+]?[1-9][\d]{0,15}$/,
        url: /^https?:\/\/.+/,
        
        // Field lengths
        name: { min: 2, max: 100 },
        email: { max: 255 },
        phone: { max: 50 },
        title: { max: 200 },
        description: { max: 2000 },
        notes: { max: 5000 }
    },
    
    // Default Values
    DEFAULTS: {
        lead_score: 0,
        deal_probability: 50,
        task_priority: 'medium',
        activity_type: 'note',
        page_size: 20
    },
    
    // Feature Flags
    FEATURES: {
        ai_insights: true,
        google_integration: true,
        memory_system: true,
        advanced_analytics: true,
        bulk_operations: true,
        export_data: true,
        import_data: true,
        custom_fields: false, // Future feature
        workflow_automation: false, // Future feature
        team_collaboration: false // Future feature
    },
    
    // Error Messages
    ERRORS: {
        network: 'Network error. Please check your connection and try again.',
        unauthorized: 'Your session has expired. Please log in again.',
        forbidden: 'You don\'t have permission to perform this action.',
        not_found: 'The requested resource was not found.',
        validation: 'Please check your input and try again.',
        server: 'An unexpected error occurred. Please try again later.',
        file_too_large: 'File size exceeds the maximum limit.',
        invalid_file_type: 'Invalid file type. Please select a supported file.',
        ai_unavailable: 'AI services are temporarily unavailable.',
        memory_search_failed: 'Memory search failed. Please try again.'
    },
    
    // Success Messages
    SUCCESS: {
        saved: 'Changes saved successfully',
        created: 'Item created successfully',
        updated: 'Item updated successfully',
        deleted: 'Item deleted successfully',
        imported: 'Data imported successfully',
        exported: 'Data exported successfully',
        email_sent: 'Email sent successfully',
        task_completed: 'Task marked as completed',
        login: 'Welcome back!',
        logout: 'You have been logged out successfully'
    },
    
    // Loading Messages
    LOADING: {
        default: 'Loading...',
        saving: 'Saving...',
        deleting: 'Deleting...',
        importing: 'Importing data...',
        exporting: 'Exporting data...',
        analyzing: 'Analyzing with AI...',
        searching: 'Searching...',
        authenticating: 'Authenticating...'
    },
    
    // Keyboard Shortcuts
    SHORTCUTS: {
        search: 'Ctrl+K',
        new_contact: 'Ctrl+Shift+C',
        new_deal: 'Ctrl+Shift+D',
        new_task: 'Ctrl+Shift+T',
        ai_assistant: 'Ctrl+Shift+A',
        save: 'Ctrl+S',
        close_modal: 'Escape'
    },
    
    // Local Storage Keys
    STORAGE_KEYS: {
        theme: 'agentic_crm_theme',
        sidebar_collapsed: 'agentic_crm_sidebar_collapsed',
        user_preferences: 'agentic_crm_user_preferences',
        recent_searches: 'agentic_crm_recent_searches',
        draft_forms: 'agentic_crm_draft_forms'
    },
    
    // Animation Durations (in milliseconds)
    ANIMATIONS: {
        fast: 150,
        normal: 300,
        slow: 500,
        page_transition: 400
    },
    
    // Breakpoints for responsive design
    BREAKPOINTS: {
        mobile: 768,
        tablet: 1024,
        desktop: 1280,
        wide: 1536
    },
    
    // Auto-save intervals
    AUTO_SAVE: {
        draft_interval: 30000, // 30 seconds
        session_check: 60000, // 1 minute
        notification_check: 30000 // 30 seconds
    }
};

// Environment-specific overrides
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    CONFIG.DEBUG = true;
    CONFIG.LOG_LEVEL = 'debug';
} else {
    CONFIG.DEBUG = false;
    CONFIG.LOG_LEVEL = 'error';
}

// Freeze configuration to prevent accidental modifications
Object.freeze(CONFIG);

// Export for use in other modules
window.CONFIG = CONFIG;
