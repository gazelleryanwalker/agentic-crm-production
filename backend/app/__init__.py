from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
from datetime import timedelta

db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'agentic-crm-secret-key-change-in-production')
    
    # Database configuration - handle both PostgreSQL and SQLite
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///agentic_crm.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {'connect_timeout': 10}
    }
    
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.crm import crm_bp
    from app.routes.memory import memory_bp
    from app.routes.ai import ai_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.debug import debug_bp
    from app.routes.seo import seo_bp
    # from app.routes.google_auth import google_auth_bp  # Temporarily disabled for stable launch
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(crm_bp, url_prefix='/api/crm')
    app.register_blueprint(memory_bp, url_prefix='/api/memory')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(debug_bp, url_prefix='/api/debug')
    app.register_blueprint(seo_bp, url_prefix='/api/seo')
    # app.register_blueprint(google_auth_bp, url_prefix='/api/auth')  # Temporarily disabled for stable launch
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'Agentic CRM'}
    
    # Import all models to ensure tables are created
    from app.models.user import User
    from app.models.contact import Contact
    from app.models.deal import Deal
    from app.models.task import Task
    from app.models.memory import Memory
    from app.models.seo import SEOProject, SEOAnalysis, SEORule, SEOOptimization, SEOKeyword, SEOAudit, SEOTemplate
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully")
            create_default_admin()
        except Exception as e:
            print(f"Error creating database tables: {e}")
    
    return app

def create_default_admin():
    """Create default admin user if it doesn't exist"""
    try:
        from app.models.user import User
        
        # Check if admin user already exists
        admin_user = db.session.query(User).filter_by(username='admin').first()
        
        if not admin_user:
            # Create default admin user
            admin_user = User(
                username='admin',
                email='admin@agenticcrm.com',
                first_name='Admin',
                last_name='User',
                is_admin=True,
                is_active=True
            )
            admin_user.set_password('admin123')
            
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created: admin@agenticcrm.com / admin123")
        else:
            print("Admin user already exists")
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.session.rollback()
