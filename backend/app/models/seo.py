from .. import db
from datetime import datetime
from sqlalchemy import Text, JSON

class SEOProject(db.Model):
    """SEO Project model for managing client SEO automation projects"""
    __tablename__ = 'seo_projects'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    domain = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(50), default='active')  # active, paused, completed
    snippet_token = db.Column(db.String(100), unique=True)  # For JavaScript snippet authentication
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_analysis = db.Column(db.DateTime)
    total_pages = db.Column(db.Integer, default=0)
    optimized_pages = db.Column(db.Integer, default=0)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('seo_projects', lazy=True))
    analyses = db.relationship('SEOAnalysis', backref='project', lazy=True, cascade='all, delete-orphan')
    rules = db.relationship('SEORule', backref='project', lazy=True, cascade='all, delete-orphan')
    optimizations = db.relationship('SEOOptimization', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<SEOProject {self.name}>'

class SEOAnalysis(db.Model):
    """SEO Analysis model for storing page analysis results"""
    __tablename__ = 'seo_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('seo_projects.id'), nullable=False)
    url = db.Column(db.String(1000), nullable=False)
    
    # Current SEO elements
    current_title = db.Column(db.String(500))
    current_description = db.Column(Text)
    current_h1 = db.Column(db.String(500))
    current_keywords = db.Column(Text)  # JSON array of keywords
    
    # Analysis results
    recommendations = db.Column(Text)  # JSON object with AI recommendations
    seo_score = db.Column(db.Integer, default=0)  # Overall SEO score (0-100)
    
    # Status tracking
    status = db.Column(db.String(50), default='pending')  # pending, approved, applied, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SEOAnalysis {self.url}>'

class SEORule(db.Model):
    """SEO Rule model for automated optimization rules"""
    __tablename__ = 'seo_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('seo_projects.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    rule_type = db.Column(db.String(50), nullable=False)  # title, description, h1, schema, internal_links
    
    # Rule configuration
    conditions = db.Column(Text)  # JSON object defining when rule applies
    actions = db.Column(Text)  # JSON object defining what changes to make
    priority = db.Column(db.Integer, default=1)  # Rule priority (1-10)
    
    # Status and tracking
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    times_applied = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<SEORule {self.name}>'

class SEOOptimization(db.Model):
    """SEO Optimization model for tracking applied optimizations"""
    __tablename__ = 'seo_optimizations'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('seo_projects.id'), nullable=False)
    analysis_id = db.Column(db.Integer, db.ForeignKey('seo_analyses.id'), nullable=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('seo_rules.id'), nullable=True)
    
    url = db.Column(db.String(1000), nullable=False)
    optimization_type = db.Column(db.String(50), nullable=False)  # title, description, h1, schema, links
    
    # Optimization details
    original_value = db.Column(Text)
    optimized_value = db.Column(Text)
    change_description = db.Column(Text)
    
    # Status tracking
    status = db.Column(db.String(50), default='pending')  # pending, applied, reverted, failed
    applied_at = db.Column(db.DateTime)
    reverted_at = db.Column(db.DateTime)
    
    # Performance tracking
    clicks_before = db.Column(db.Integer, default=0)
    clicks_after = db.Column(db.Integer, default=0)
    impressions_before = db.Column(db.Integer, default=0)
    impressions_after = db.Column(db.Integer, default=0)
    ctr_before = db.Column(db.Float, default=0.0)
    ctr_after = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    analysis = db.relationship('SEOAnalysis', backref='optimizations')
    rule = db.relationship('SEORule', backref='optimizations')
    
    def __repr__(self):
        return f'<SEOOptimization {self.optimization_type} for {self.url}>'

class SEOKeyword(db.Model):
    """SEO Keyword model for tracking keyword performance"""
    __tablename__ = 'seo_keywords'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('seo_projects.id'), nullable=False)
    keyword = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(1000))  # Target URL for this keyword
    
    # Keyword metrics
    search_volume = db.Column(db.Integer, default=0)
    difficulty = db.Column(db.Integer, default=0)  # 1-100 difficulty score
    current_position = db.Column(db.Integer)
    target_position = db.Column(db.Integer, default=1)
    
    # Performance tracking
    clicks = db.Column(db.Integer, default=0)
    impressions = db.Column(db.Integer, default=0)
    ctr = db.Column(db.Float, default=0.0)
    
    # Status
    status = db.Column(db.String(50), default='tracking')  # tracking, optimizing, achieved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('SEOProject', backref='keywords')
    
    def __repr__(self):
        return f'<SEOKeyword {self.keyword}>'

class SEOAudit(db.Model):
    """SEO Audit model for comprehensive site audits"""
    __tablename__ = 'seo_audits'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('seo_projects.id'), nullable=False)
    audit_type = db.Column(db.String(50), nullable=False)  # full, technical, content, links
    
    # Audit results
    overall_score = db.Column(db.Integer, default=0)  # 0-100
    issues_found = db.Column(db.Integer, default=0)
    issues_fixed = db.Column(db.Integer, default=0)
    
    # Detailed results
    technical_issues = db.Column(Text)  # JSON array of technical issues
    content_issues = db.Column(Text)  # JSON array of content issues
    link_issues = db.Column(Text)  # JSON array of link issues
    recommendations = db.Column(Text)  # JSON array of recommendations
    
    # Status and timing
    status = db.Column(db.String(50), default='running')  # running, completed, failed
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    project = db.relationship('SEOProject', backref='audits')
    
    def __repr__(self):
        return f'<SEOAudit {self.audit_type} for project {self.project_id}>'

class SEOTemplate(db.Model):
    """SEO Template model for reusable optimization templates"""
    __tablename__ = 'seo_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    template_type = db.Column(db.String(50), nullable=False)  # title, description, schema, etc.
    
    # Template content
    template_content = db.Column(Text)  # Template with placeholders
    variables = db.Column(Text)  # JSON array of available variables
    description = db.Column(Text)
    
    # Usage tracking
    times_used = db.Column(db.Integer, default=0)
    is_public = db.Column(db.Boolean, default=False)  # Can be shared with other users
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='seo_templates')
    
    def __repr__(self):
        return f'<SEOTemplate {self.name}>'
