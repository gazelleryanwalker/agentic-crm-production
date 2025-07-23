// Agentic CRM - Utility Functions

/**
 * Utility functions for common operations
 */
const Utils = {
    
    /**
     * Format currency values
     */
    formatCurrency(amount, currency = CONFIG.CURRENCY) {
        if (amount === null || amount === undefined) return '-';
        
        return new Intl.NumberFormat(currency.locale, {
            style: 'currency',
            currency: currency.code,
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        }).format(amount);
    },
    
    /**
     * Format dates
     */
    formatDate(date, format = CONFIG.DATE_FORMATS.display) {
        if (!date) return '-';
        
        const d = new Date(date);
        if (isNaN(d.getTime())) return '-';
        
        const options = {
            year: 'numeric',
            month: 'short',
            day: '2-digit'
        };
        
        if (format === CONFIG.DATE_FORMATS.displayWithTime) {
            options.hour = '2-digit';
            options.minute = '2-digit';
        }
        
        return d.toLocaleDateString('en-US', options);
    },
    
    /**
     * Format relative time (e.g., "2 hours ago")
     */
    formatRelativeTime(date) {
        if (!date) return '-';
        
        const d = new Date(date);
        const now = new Date();
        const diffMs = now - d;
        
        const diffSeconds = Math.floor(diffMs / 1000);
        const diffMinutes = Math.floor(diffSeconds / 60);
        const diffHours = Math.floor(diffMinutes / 60);
        const diffDays = Math.floor(diffHours / 24);
        
        if (diffSeconds < 60) return 'Just now';
        if (diffMinutes < 60) return `${diffMinutes}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return this.formatDate(date);
    },
    
    /**
     * Generate initials from name
     */
    getInitials(name) {
        if (!name) return '?';
        
        return name
            .split(' ')
            .map(word => word.charAt(0).toUpperCase())
            .slice(0, 2)
            .join('');
    },
    
    /**
     * Generate avatar color based on name
     */
    getAvatarColor(name) {
        if (!name) return CONFIG.CHART_COLORS.gray;
        
        const colors = Object.values(CONFIG.CHART_COLORS);
        const hash = name.split('').reduce((a, b) => {
            a = ((a << 5) - a) + b.charCodeAt(0);
            return a & a;
        }, 0);
        
        return colors[Math.abs(hash) % colors.length];
    },
    
    /**
     * Debounce function calls
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    /**
     * Throttle function calls
     */
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    /**
     * Validate email address
     */
    isValidEmail(email) {
        return CONFIG.VALIDATION.email.test(email);
    },
    
    /**
     * Validate phone number
     */
    isValidPhone(phone) {
        return CONFIG.VALIDATION.phone.test(phone);
    },
    
    /**
     * Validate URL
     */
    isValidUrl(url) {
        return CONFIG.VALIDATION.url.test(url);
    },
    
    /**
     * Sanitize HTML content
     */
    sanitizeHtml(html) {
        const div = document.createElement('div');
        div.textContent = html;
        return div.innerHTML;
    },
    
    /**
     * Truncate text
     */
    truncateText(text, maxLength = 100) {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    },
    
    /**
     * Generate random ID
     */
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },
    
    /**
     * Deep clone object
     */
    deepClone(obj) {
        return JSON.parse(JSON.stringify(obj));
    },
    
    /**
     * Check if object is empty
     */
    isEmpty(obj) {
        if (obj === null || obj === undefined) return true;
        if (Array.isArray(obj)) return obj.length === 0;
        if (typeof obj === 'object') return Object.keys(obj).length === 0;
        if (typeof obj === 'string') return obj.trim().length === 0;
        return false;
    },
    
    /**
     * Capitalize first letter
     */
    capitalize(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    },
    
    /**
     * Convert camelCase to Title Case
     */
    camelToTitle(str) {
        return str
            .replace(/([A-Z])/g, ' $1')
            .replace(/^./, str => str.toUpperCase());
    },
    
    /**
     * Format file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    /**
     * Get file extension
     */
    getFileExtension(filename) {
        return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2);
    },
    
    /**
     * Check if file type is allowed
     */
    isAllowedFileType(file) {
        return CONFIG.ALLOWED_FILE_TYPES.includes(file.type);
    },
    
    /**
     * Download file from blob
     */
    downloadBlob(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    },
    
    /**
     * Copy text to clipboard
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            const success = document.execCommand('copy');
            document.body.removeChild(textArea);
            return success;
        }
    },
    
    /**
     * Get query parameters from URL
     */
    getQueryParams() {
        const params = new URLSearchParams(window.location.search);
        const result = {};
        for (const [key, value] of params) {
            result[key] = value;
        }
        return result;
    },
    
    /**
     * Update URL without page reload
     */
    updateUrl(params) {
        const url = new URL(window.location);
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined) {
                url.searchParams.set(key, params[key]);
            } else {
                url.searchParams.delete(key);
            }
        });
        window.history.replaceState({}, '', url);
    },
    
    /**
     * Local storage helpers
     */
    storage: {
        get(key, defaultValue = null) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (e) {
                console.warn('Failed to get from localStorage:', e);
                return defaultValue;
            }
        },
        
        set(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (e) {
                console.warn('Failed to set to localStorage:', e);
                return false;
            }
        },
        
        remove(key) {
            try {
                localStorage.removeItem(key);
                return true;
            } catch (e) {
                console.warn('Failed to remove from localStorage:', e);
                return false;
            }
        },
        
        clear() {
            try {
                localStorage.clear();
                return true;
            } catch (e) {
                console.warn('Failed to clear localStorage:', e);
                return false;
            }
        }
    },
    
    /**
     * Color utilities
     */
    color: {
        /**
         * Convert hex to RGB
         */
        hexToRgb(hex) {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result ? {
                r: parseInt(result[1], 16),
                g: parseInt(result[2], 16),
                b: parseInt(result[3], 16)
            } : null;
        },
        
        /**
         * Get contrast color (black or white)
         */
        getContrastColor(hex) {
            const rgb = this.hexToRgb(hex);
            if (!rgb) return '#000000';
            
            const brightness = (rgb.r * 299 + rgb.g * 587 + rgb.b * 114) / 1000;
            return brightness > 128 ? '#000000' : '#ffffff';
        },
        
        /**
         * Lighten color
         */
        lighten(hex, percent) {
            const rgb = this.hexToRgb(hex);
            if (!rgb) return hex;
            
            const amount = Math.round(2.55 * percent);
            const r = Math.min(255, rgb.r + amount);
            const g = Math.min(255, rgb.g + amount);
            const b = Math.min(255, rgb.b + amount);
            
            return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
        }
    },
    
    /**
     * Animation helpers
     */
    animation: {
        /**
         * Fade in element
         */
        fadeIn(element, duration = CONFIG.ANIMATIONS.normal) {
            element.style.opacity = '0';
            element.style.display = 'block';
            
            const start = performance.now();
            
            const animate = (timestamp) => {
                const elapsed = timestamp - start;
                const progress = Math.min(elapsed / duration, 1);
                
                element.style.opacity = progress;
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                }
            };
            
            requestAnimationFrame(animate);
        },
        
        /**
         * Fade out element
         */
        fadeOut(element, duration = CONFIG.ANIMATIONS.normal) {
            const start = performance.now();
            const initialOpacity = parseFloat(getComputedStyle(element).opacity);
            
            const animate = (timestamp) => {
                const elapsed = timestamp - start;
                const progress = Math.min(elapsed / duration, 1);
                
                element.style.opacity = initialOpacity * (1 - progress);
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    element.style.display = 'none';
                }
            };
            
            requestAnimationFrame(animate);
        },
        
        /**
         * Slide down element
         */
        slideDown(element, duration = CONFIG.ANIMATIONS.normal) {
            element.style.height = '0';
            element.style.overflow = 'hidden';
            element.style.display = 'block';
            
            const targetHeight = element.scrollHeight;
            const start = performance.now();
            
            const animate = (timestamp) => {
                const elapsed = timestamp - start;
                const progress = Math.min(elapsed / duration, 1);
                
                element.style.height = (targetHeight * progress) + 'px';
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    element.style.height = '';
                    element.style.overflow = '';
                }
            };
            
            requestAnimationFrame(animate);
        }
    },
    
    /**
     * Form validation helpers
     */
    validation: {
        /**
         * Validate required field
         */
        required(value) {
            return !Utils.isEmpty(value);
        },
        
        /**
         * Validate minimum length
         */
        minLength(value, min) {
            return !value || value.length >= min;
        },
        
        /**
         * Validate maximum length
         */
        maxLength(value, max) {
            return !value || value.length <= max;
        },
        
        /**
         * Validate field with multiple rules
         */
        validate(value, rules) {
            const errors = [];
            
            if (rules.required && !this.required(value)) {
                errors.push('This field is required');
            }
            
            if (rules.email && value && !Utils.isValidEmail(value)) {
                errors.push('Please enter a valid email address');
            }
            
            if (rules.phone && value && !Utils.isValidPhone(value)) {
                errors.push('Please enter a valid phone number');
            }
            
            if (rules.minLength && !this.minLength(value, rules.minLength)) {
                errors.push(`Must be at least ${rules.minLength} characters`);
            }
            
            if (rules.maxLength && !this.maxLength(value, rules.maxLength)) {
                errors.push(`Must be no more than ${rules.maxLength} characters`);
            }
            
            return errors;
        }
    }
};

// Export for global use
window.Utils = Utils;
