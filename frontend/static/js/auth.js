// Agentic CRM - Authentication Service

/**
 * Authentication service for handling user login/logout
 */
class AuthService {
    constructor() {
        this.currentUser = null;
        this.token = null;
        this.init();
    }

    /**
     * Initialize authentication service
     */
    init() {
        this.bindEvents();
        this.checkAuthStatus();
        this.handleOAuthCallback();
    }

    /**
     * Load stored authentication data
     */
    loadStoredAuth() {
        this.token = Utils.storage.get(CONFIG.TOKEN_KEY);
        this.currentUser = Utils.storage.get(CONFIG.USER_KEY);
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!(this.token && this.currentUser);
    }

    /**
     * Get current user
     */
    getCurrentUser() {
        return this.currentUser;
    }

    /**
     * Get current token
     */
    getToken() {
        return this.token;
    }

    /**
     * Login user
     */
    async login(credentials) {
        try {
            const response = await api.login(credentials);
            
            if (response.access_token && response.user) {
                this.token = response.access_token;
                this.currentUser = response.user;
                
                // Store in localStorage
                Utils.storage.set(CONFIG.TOKEN_KEY, this.token);
                Utils.storage.set(CONFIG.USER_KEY, this.currentUser);
                
                // Setup token refresh
                this.setupTokenRefresh();
                
                notifications.success(CONFIG.SUCCESS.login);
                return { success: true, user: this.currentUser };
            } else {
                throw new Error('Invalid response format');
            }
        } catch (error) {
            notifications.error(error.message || 'Login failed');
            return { success: false, error: error.message };
        }
    }

    /**
     * Register new user
     */
    async register(userData) {
        try {
            const response = await api.register(userData);
            
            if (response.access_token && response.user) {
                this.token = response.access_token;
                this.currentUser = response.user;
                
                // Store in localStorage
                Utils.storage.set(CONFIG.TOKEN_KEY, this.token);
                Utils.storage.set(CONFIG.USER_KEY, this.currentUser);
                
                // Setup token refresh
                this.setupTokenRefresh();
                
                notifications.success('Account created successfully');
                return { success: true, user: this.currentUser };
            } else {
                throw new Error('Invalid response format');
            }
        } catch (error) {
            notifications.error(error.message || 'Registration failed');
            return { success: false, error: error.message };
        }
    }

    /**
     * Logout user
     */
    async logout() {
        try {
            // Call logout endpoint
            if (this.token) {
                await api.logout();
            }
        } catch (error) {
            console.warn('Logout API call failed:', error);
        } finally {
            // Clear local data regardless of API call result
            this.clearAuth();
            notifications.success(CONFIG.SUCCESS.logout);
        }
    }

    /**
     * Clear authentication data
     */
    clearAuth() {
        this.token = null;
        this.currentUser = null;
        
        Utils.storage.remove(CONFIG.TOKEN_KEY);
        Utils.storage.remove(CONFIG.USER_KEY);
        
        // Clear token refresh timer
        if (this.refreshTimer) {
            clearTimeout(this.refreshTimer);
            this.refreshTimer = null;
        }
    }

    /**
     * Update user profile
     */
    async updateProfile(data) {
        try {
            const response = await api.updateProfile(data);
            
            if (response.user) {
                this.currentUser = response.user;
                Utils.storage.set(CONFIG.USER_KEY, this.currentUser);
                notifications.success(CONFIG.SUCCESS.updated);
                return { success: true, user: this.currentUser };
            }
        } catch (error) {
            notifications.error(error.message || 'Profile update failed');
            return { success: false, error: error.message };
        }
    }

    /**
     * Change password
     */
    async changePassword(data) {
        try {
            await api.changePassword(data);
            notifications.success('Password changed successfully');
            return { success: true };
        } catch (error) {
            notifications.error(error.message || 'Password change failed');
            return { success: false, error: error.message };
        }
    }

    /**
     * Setup automatic token refresh
     */
    setupTokenRefresh() {
        if (!this.token) return;

        // Clear existing timer
        if (this.refreshTimer) {
            clearTimeout(this.refreshTimer);
        }

        // Set timer to refresh token before it expires
        this.refreshTimer = setTimeout(() => {
            this.refreshToken();
        }, CONFIG.TOKEN_REFRESH_THRESHOLD);
    }

    /**
     * Refresh authentication token
     */
    async refreshToken() {
        try {
            const response = await api.get('/auth/refresh');
            
            if (response.access_token) {
                this.token = response.access_token;
                Utils.storage.set(CONFIG.TOKEN_KEY, this.token);
                this.setupTokenRefresh();
            }
        } catch (error) {
            console.warn('Token refresh failed:', error);
            // If refresh fails, user needs to login again
            this.clearAuth();
            window.location.href = '/login';
        }
    }

    /**
     * Google OAuth login
     */
    async googleLogin() {
        try {
            // Check if Google OAuth is configured
            const statusResponse = await apiService.request('/auth/google/status', 'GET');
            
            if (!statusResponse.configured) {
                notificationService.showError('Google OAuth not configured. Please set up Google Cloud credentials.');
                console.log('Setup instructions:', statusResponse);
                return false;
            }
            
            // Initiate Google OAuth flow
            const response = await apiService.request('/auth/google/login', 'GET');
            
            if (response.authorization_url) {
                // Redirect to Google OAuth
                window.location.href = response.authorization_url;
                return true;
            } else {
                throw new Error('No authorization URL received');
            }
        } catch (error) {
            console.error('Google login error:', error);
            notificationService.showError(error.message || 'Google login failed');
            return false;
        }
    }

    /**
     * Check authentication status on page load
     */
    async checkAuth() {
        if (!this.isAuthenticated()) {
            return false;
        }

        try {
            // Verify token is still valid
            const response = await api.getProfile();
            
            if (response.user) {
                this.currentUser = response.user;
                Utils.storage.set(CONFIG.USER_KEY, this.currentUser);
                return true;
            }
        } catch (error) {
            console.warn('Auth check failed:', error);
            this.clearAuth();
        }

        return false;
    }
}

/**
 * Login form handler
 */
class LoginForm {
    constructor() {
        this.form = null;
        this.emailInput = null;
        this.passwordInput = null;
        this.submitButton = null;
        this.init();
    }

    init() {
        this.form = document.getElementById('login-form');
        if (!this.form) return;

        this.emailInput = document.getElementById('email');
        this.passwordInput = document.getElementById('password');
        this.submitButton = this.form.querySelector('button[type="submit"]');

        this.bindEvents();
    }

    bindEvents() {
        if (!this.form) return;

        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });

        // Google login button
        const googleLoginBtn = document.getElementById('google-login');
        if (googleLoginBtn) {
            googleLoginBtn.addEventListener('click', async (e) => {
                e.preventDefault();
                await authService.googleLogin();
            });
        }

        // Show register form
        const showRegisterBtn = document.getElementById('show-register');
        if (showRegisterBtn) {
            showRegisterBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.showRegisterForm();
            });
        }
    }

    async handleSubmit() {
        const email = this.emailInput.value.trim();
        const password = this.passwordInput.value;

        // Basic validation
        if (!email || !password) {
            notifications.error('Please fill in all fields');
            return;
        }

        if (!Utils.isValidEmail(email)) {
            notifications.error('Please enter a valid email address');
            return;
        }

        // Show loading state
        this.setLoading(true);

        try {
            const result = await auth.login({ email, password });
            
            if (result.success) {
                // Redirect to main app
                this.redirectToApp();
            }
        } finally {
            this.setLoading(false);
        }
    }

    async handleGoogleLogin() {
        this.setLoading(true);
        
        try {
            const result = await auth.googleLogin();
            
            if (result.success) {
                this.redirectToApp();
            }
        } finally {
            this.setLoading(false);
        }
    }

    showRegisterForm() {
        // This would show a registration form
        // For now, just show a message
        notifications.info('Registration form coming soon');
    }

    setLoading(loading) {
        if (!this.submitButton) return;

        if (loading) {
            this.submitButton.disabled = true;
            this.submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing In...';
        } else {
            this.submitButton.disabled = false;
            this.submitButton.innerHTML = '<i class="fas fa-sign-in-alt"></i> Sign In';
        }
    }

    redirectToApp() {
        // Hide login screen and show main app
        const loginScreen = document.getElementById('login-screen');
        const mainApp = document.getElementById('main-app');
        
        if (loginScreen && mainApp) {
            loginScreen.classList.add('hidden');
            mainApp.classList.remove('hidden');
        }
    }
}

/**
 * User profile component
 */
class UserProfile {
    constructor() {
        this.init();
    }

    init() {
        this.updateUserDisplay();
        this.bindEvents();
    }

    updateUserDisplay() {
        const user = auth.getCurrentUser();
        if (!user) return;

        // Update user name display
        const userNameElement = document.getElementById('user-name');
        if (userNameElement) {
            userNameElement.textContent = user.first_name 
                ? `${user.first_name} ${user.last_name || ''}`.trim()
                : user.username || user.email;
        }

        // Update user avatar
        const userAvatar = document.querySelector('.user-avatar');
        if (userAvatar && user.first_name) {
            const initials = Utils.getInitials(`${user.first_name} ${user.last_name || ''}`);
            userAvatar.innerHTML = initials;
        }
    }

    bindEvents() {
        // User menu toggle
        const userMenuToggle = document.getElementById('user-menu-toggle');
        if (userMenuToggle) {
            userMenuToggle.addEventListener('click', () => {
                this.toggleUserMenu();
            });
        }

        // Logout functionality (would be in a dropdown menu)
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="logout"]')) {
                this.handleLogout();
            }
        });
    }

    toggleUserMenu() {
        // This would toggle a user dropdown menu
        // For now, just show logout option
        const confirmed = confirm('Do you want to log out?');
        if (confirmed) {
            this.handleLogout();
        }
    }

    async handleLogout() {
        await auth.logout();
        
        // Show login screen
        const loginScreen = document.getElementById('login-screen');
        const mainApp = document.getElementById('main-app');
        
        if (loginScreen && mainApp) {
            mainApp.classList.add('hidden');
            loginScreen.classList.remove('hidden');
        }
    }
}

// Create global instances
const auth = new AuthService();
const loginForm = new LoginForm();
const userProfile = new UserProfile();

// Export for global use
window.auth = auth;
window.loginForm = loginForm;
window.userProfile = userProfile;
