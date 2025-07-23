// Tasks Management Module
class TasksController {
    constructor() {
        this.tasks = [];
        this.currentPage = 1;
        this.pageSize = CONFIG.PAGINATION.DEFAULT_PAGE_SIZE;
        this.searchQuery = '';
        this.sortBy = 'updated_at';
        this.sortOrder = 'desc';
        this.filters = {};
    }

    async init() {
        console.log('TasksController initialized');
        await this.loadTasks();
        this.bindEvents();
    }

    async loadTasks() {
        try {
            const response = await apiService.getTasks({
                page: this.currentPage,
                limit: this.pageSize,
                search: this.searchQuery,
                sort_by: this.sortBy,
                sort_order: this.sortOrder,
                ...this.filters
            });
            
            this.tasks = response.tasks || [];
            this.renderTasks();
        } catch (error) {
            console.error('Error loading tasks:', error);
            notificationService.showError('Failed to load tasks');
        }
    }

    renderTasks() {
        console.log('Rendering tasks:', this.tasks.length);
        // Task rendering logic would go here
    }

    bindEvents() {
        // Event binding logic would go here
        console.log('Task events bound');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.hash === '#tasks') {
        window.tasksController = new TasksController();
        window.tasksController.init();
    }
});
