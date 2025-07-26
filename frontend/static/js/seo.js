// SEO Automation Module
class SEOManager {
    constructor() {
        this.currentProject = null;
        this.projects = [];
        this.optimizations = [];
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadProjects();
    }

    bindEvents() {
        // Project management events
        document.addEventListener('click', (e) => {
            if (e.target.matches('#create-seo-project-btn')) {
                this.showCreateProjectModal();
            }
            if (e.target.matches('#save-seo-project-btn')) {
                this.createProject();
            }
            if (e.target.matches('.analyze-website-btn')) {
                const projectId = e.target.dataset.projectId;
                this.showAnalyzeModal(projectId);
            }
            if (e.target.matches('#start-analysis-btn')) {
                this.analyzeWebsite();
            }
            if (e.target.matches('.view-optimizations-btn')) {
                const projectId = e.target.dataset.projectId;
                this.viewOptimizations(projectId);
            }
            if (e.target.matches('.generate-snippet-btn')) {
                const projectId = e.target.dataset.projectId;
                this.generateSnippet(projectId);
            }
            if (e.target.matches('.apply-optimization-btn')) {
                const optimizationId = e.target.dataset.optimizationId;
                this.applyOptimization(optimizationId);
            }
        });

        // Form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.matches('#create-seo-project-form')) {
                e.preventDefault();
                this.createProject();
            }
            if (e.target.matches('#analyze-website-form')) {
                e.preventDefault();
                this.analyzeWebsite();
            }
        });
    }

    async loadProjects() {
        try {
            const response = await fetch('/api/seo/projects', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.projects = data.projects;
                this.renderProjects();
            } else {
                console.error('Failed to load SEO projects');
            }
        } catch (error) {
            console.error('Error loading SEO projects:', error);
        }
    }

    renderProjects() {
        const container = document.getElementById('seo-projects-container');
        if (!container) return;

        if (this.projects.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>No SEO Projects Yet</h3>
                    <p>Create your first SEO automation project to get started.</p>
                    <button id="create-seo-project-btn" class="btn btn-primary">
                        <i class="fas fa-plus"></i> Create SEO Project
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="projects-header">
                <h3>SEO Automation Projects</h3>
                <button id="create-seo-project-btn" class="btn btn-primary">
                    <i class="fas fa-plus"></i> New Project
                </button>
            </div>
            <div class="projects-grid">
                ${this.projects.map(project => this.renderProjectCard(project)).join('')}
            </div>
        `;
    }

    renderProjectCard(project) {
        const statusClass = project.status === 'active' ? 'success' : 'warning';
        const lastAnalysis = project.last_analysis 
            ? new Date(project.last_analysis).toLocaleDateString()
            : 'Never';

        return `
            <div class="project-card">
                <div class="project-header">
                    <h4>${project.name}</h4>
                    <span class="status-badge status-${statusClass}">${project.status}</span>
                </div>
                <div class="project-details">
                    <p><strong>Domain:</strong> ${project.domain}</p>
                    <p><strong>Pages:</strong> ${project.optimized_pages}/${project.total_pages} optimized</p>
                    <p><strong>Last Analysis:</strong> ${lastAnalysis}</p>
                </div>
                <div class="project-actions">
                    <button class="btn btn-sm btn-outline analyze-website-btn" data-project-id="${project.id}">
                        <i class="fas fa-search"></i> Analyze
                    </button>
                    <button class="btn btn-sm btn-outline view-optimizations-btn" data-project-id="${project.id}">
                        <i class="fas fa-eye"></i> View Results
                    </button>
                    <button class="btn btn-sm btn-primary generate-snippet-btn" data-project-id="${project.id}">
                        <i class="fas fa-code"></i> Get Snippet
                    </button>
                </div>
            </div>
        `;
    }

    showCreateProjectModal() {
        const modal = document.getElementById('seo-project-modal');
        if (!modal) {
            this.createProjectModal();
        }
        document.getElementById('seo-project-modal').style.display = 'block';
    }

    createProjectModal() {
        const modalHTML = `
            <div id="seo-project-modal" class="modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Create SEO Project</h3>
                        <span class="close" onclick="document.getElementById('seo-project-modal').style.display='none'">&times;</span>
                    </div>
                    <form id="create-seo-project-form">
                        <div class="form-group">
                            <label for="project-name">Project Name</label>
                            <input type="text" id="project-name" name="name" required 
                                   placeholder="e.g., My Website SEO">
                        </div>
                        <div class="form-group">
                            <label for="project-domain">Website Domain</label>
                            <input type="url" id="project-domain" name="domain" required 
                                   placeholder="https://example.com">
                        </div>
                        <div class="modal-actions">
                            <button type="button" class="btn btn-secondary" 
                                    onclick="document.getElementById('seo-project-modal').style.display='none'">
                                Cancel
                            </button>
                            <button type="submit" id="save-seo-project-btn" class="btn btn-primary">
                                Create Project
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    async createProject() {
        const form = document.getElementById('create-seo-project-form');
        const formData = new FormData(form);
        
        const projectData = {
            name: formData.get('name'),
            domain: formData.get('domain')
        };

        try {
            const response = await fetch('/api/seo/projects', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify(projectData)
            });

            if (response.ok) {
                const data = await response.json();
                this.showNotification('SEO project created successfully!', 'success');
                document.getElementById('seo-project-modal').style.display = 'none';
                this.loadProjects(); // Reload projects
            } else {
                const error = await response.json();
                this.showNotification(error.message || 'Failed to create project', 'error');
            }
        } catch (error) {
            console.error('Error creating project:', error);
            this.showNotification('Failed to create project', 'error');
        }
    }

    showAnalyzeModal(projectId) {
        const project = this.projects.find(p => p.id == projectId);
        if (!project) return;

        const modal = document.getElementById('analyze-modal');
        if (!modal) {
            this.createAnalyzeModal();
        }

        document.getElementById('analyze-project-name').textContent = project.name;
        document.getElementById('analyze-project-id').value = projectId;
        document.getElementById('analyze-urls').value = project.domain;
        document.getElementById('analyze-modal').style.display = 'block';
    }

    createAnalyzeModal() {
        const modalHTML = `
            <div id="analyze-modal" class="modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Analyze Website: <span id="analyze-project-name"></span></h3>
                        <span class="close" onclick="document.getElementById('analyze-modal').style.display='none'">&times;</span>
                    </div>
                    <form id="analyze-website-form">
                        <input type="hidden" id="analyze-project-id" name="project_id">
                        <div class="form-group">
                            <label for="analyze-urls">URLs to Analyze (one per line)</label>
                            <textarea id="analyze-urls" name="urls" rows="5" required 
                                      placeholder="https://example.com&#10;https://example.com/about&#10;https://example.com/services"></textarea>
                            <small class="form-help">Enter the URLs you want to analyze for SEO optimization</small>
                        </div>
                        <div class="modal-actions">
                            <button type="button" class="btn btn-secondary" 
                                    onclick="document.getElementById('analyze-modal').style.display='none'">
                                Cancel
                            </button>
                            <button type="submit" id="start-analysis-btn" class="btn btn-primary">
                                <i class="fas fa-search"></i> Start Analysis
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    async analyzeWebsite() {
        const projectId = document.getElementById('analyze-project-id').value;
        const urlsText = document.getElementById('analyze-urls').value;
        const urls = urlsText.split('\n').map(url => url.trim()).filter(url => url);

        if (urls.length === 0) {
            this.showNotification('Please enter at least one URL to analyze', 'error');
            return;
        }

        const button = document.getElementById('start-analysis-btn');
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
        button.disabled = true;

        try {
            const response = await fetch(`/api/seo/projects/${projectId}/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({ urls })
            });

            if (response.ok) {
                const data = await response.json();
                this.showNotification('Website analysis completed!', 'success');
                document.getElementById('analyze-modal').style.display = 'none';
                this.loadProjects(); // Reload to update stats
                
                // Show results
                this.showAnalysisResults(data.results);
            } else {
                const error = await response.json();
                this.showNotification(error.message || 'Analysis failed', 'error');
            }
        } catch (error) {
            console.error('Error analyzing website:', error);
            this.showNotification('Analysis failed', 'error');
        } finally {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }

    showAnalysisResults(results) {
        const modalHTML = `
            <div id="analysis-results-modal" class="modal">
                <div class="modal-content large">
                    <div class="modal-header">
                        <h3>Analysis Results</h3>
                        <span class="close" onclick="document.getElementById('analysis-results-modal').style.display='none'">&times;</span>
                    </div>
                    <div class="analysis-results">
                        ${results.map(result => this.renderAnalysisResult(result)).join('')}
                    </div>
                    <div class="modal-actions">
                        <button type="button" class="btn btn-primary" 
                                onclick="document.getElementById('analysis-results-modal').style.display='none'">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('analysis-results-modal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        document.getElementById('analysis-results-modal').style.display = 'block';
    }

    renderAnalysisResult(result) {
        if (result.error) {
            return `
                <div class="analysis-result error">
                    <h4>${result.url}</h4>
                    <p class="error-message">${result.error}</p>
                </div>
            `;
        }

        const recommendations = result.recommendations;
        const score = recommendations.overall_score || 0;
        const scoreClass = score >= 80 ? 'good' : score >= 60 ? 'fair' : 'poor';

        return `
            <div class="analysis-result">
                <div class="result-header">
                    <h4>${result.url}</h4>
                    <div class="seo-score score-${scoreClass}">${score}/100</div>
                </div>
                
                <div class="current-seo">
                    <h5>Current SEO Elements</h5>
                    <div class="seo-elements">
                        <div class="seo-element">
                            <strong>Title:</strong> ${result.current_seo.title || 'No title'}
                        </div>
                        <div class="seo-element">
                            <strong>Description:</strong> ${result.current_seo.description || 'No description'}
                        </div>
                        <div class="seo-element">
                            <strong>H1:</strong> ${result.current_seo.h1 || 'No H1'}
                        </div>
                    </div>
                </div>

                <div class="recommendations">
                    <h5>AI Recommendations</h5>
                    ${this.renderRecommendations(recommendations)}
                </div>

                <div class="priority-actions">
                    <h5>Priority Actions</h5>
                    <ul>
                        ${(recommendations.priority_actions || []).map(action => `<li>${action}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    }

    renderRecommendations(recommendations) {
        let html = '';

        if (recommendations.title_optimization) {
            html += `
                <div class="recommendation">
                    <h6>Title Optimization</h6>
                    <p><strong>Recommended:</strong> ${recommendations.title_optimization.recommended_title}</p>
                    <p><small>${recommendations.title_optimization.reasoning}</small></p>
                </div>
            `;
        }

        if (recommendations.meta_description) {
            html += `
                <div class="recommendation">
                    <h6>Meta Description</h6>
                    <p><strong>Recommended:</strong> ${recommendations.meta_description.recommended_description}</p>
                    <p><small>${recommendations.meta_description.reasoning}</small></p>
                </div>
            `;
        }

        if (recommendations.h1_optimization) {
            html += `
                <div class="recommendation">
                    <h6>H1 Optimization</h6>
                    <p><strong>Recommended:</strong> ${recommendations.h1_optimization.recommended_h1}</p>
                    <p><small>${recommendations.h1_optimization.reasoning}</small></p>
                </div>
            `;
        }

        return html || '<p>No specific recommendations available.</p>';
    }

    async generateSnippet(projectId) {
        try {
            const response = await fetch(`/api/seo/projects/${projectId}/generate-snippet`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.showSnippetModal(data);
            } else {
                const error = await response.json();
                this.showNotification(error.message || 'Failed to generate snippet', 'error');
            }
        } catch (error) {
            console.error('Error generating snippet:', error);
            this.showNotification('Failed to generate snippet', 'error');
        }
    }

    showSnippetModal(data) {
        const modalHTML = `
            <div id="snippet-modal" class="modal">
                <div class="modal-content large">
                    <div class="modal-header">
                        <h3>SEO Automation Snippet</h3>
                        <span class="close" onclick="document.getElementById('snippet-modal').style.display='none'">&times;</span>
                    </div>
                    <div class="snippet-content">
                        <div class="instructions">
                            <h4>Installation Instructions</h4>
                            <ol>
                                ${data.instructions.map(instruction => `<li>${instruction}</li>`).join('')}
                            </ol>
                        </div>
                        
                        <div class="snippet-code">
                            <h4>JavaScript Snippet</h4>
                            <div class="code-container">
                                <textarea id="snippet-code" readonly>${data.snippet}</textarea>
                                <button class="copy-btn" onclick="this.previousElementSibling.select(); document.execCommand('copy'); this.textContent='Copied!'">
                                    Copy Code
                                </button>
                            </div>
                        </div>

                        <div class="platform-guides">
                            <h4>Platform-Specific Guides</h4>
                            <div class="platform-tabs">
                                <button class="platform-tab active" data-platform="wordpress">WordPress</button>
                                <button class="platform-tab" data-platform="webflow">Webflow</button>
                                <button class="platform-tab" data-platform="framer">Framer</button>
                                <button class="platform-tab" data-platform="hubspot">HubSpot</button>
                            </div>
                            <div class="platform-content">
                                <div id="wordpress-guide" class="platform-guide active">
                                    <p>1. Go to your WordPress admin dashboard</p>
                                    <p>2. Navigate to Appearance → Theme Editor</p>
                                    <p>3. Edit header.php and paste the code before &lt;/head&gt;</p>
                                    <p>4. Save changes</p>
                                </div>
                                <div id="webflow-guide" class="platform-guide">
                                    <p>1. Open your Webflow project</p>
                                    <p>2. Go to Project Settings → Custom Code</p>
                                    <p>3. Paste the code in the Head Code section</p>
                                    <p>4. Publish your site</p>
                                </div>
                                <div id="framer-guide" class="platform-guide">
                                    <p>1. Open your Framer project</p>
                                    <p>2. Go to Site Settings → General</p>
                                    <p>3. Scroll to Custom Code and paste in Head</p>
                                    <p>4. Publish your changes</p>
                                </div>
                                <div id="hubspot-guide" class="platform-guide">
                                    <p>1. Go to HubSpot Marketing → Website → Website Pages</p>
                                    <p>2. Click Settings → Advanced Options</p>
                                    <p>3. Add the code to Additional Head HTML</p>
                                    <p>4. Save and publish</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-actions">
                        <button type="button" class="btn btn-primary" 
                                onclick="document.getElementById('snippet-modal').style.display='none'">
                            Done
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('snippet-modal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Add platform tab functionality
        document.querySelectorAll('.platform-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                document.querySelectorAll('.platform-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.platform-guide').forEach(g => g.classList.remove('active'));
                
                e.target.classList.add('active');
                document.getElementById(e.target.dataset.platform + '-guide').classList.add('active');
            });
        });
        
        document.getElementById('snippet-modal').style.display = 'block';
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()">&times;</button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
}

// Initialize SEO Manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('seo-projects-container')) {
        window.seoManager = new SEOManager();
    }
});
