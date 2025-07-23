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
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///agentic_crm.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
    # from app.routes.google_auth import google_auth_bp  # Temporarily disabled for stable launch
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(crm_bp, url_prefix='/api/crm')
    app.register_blueprint(memory_bp, url_prefix='/api/memory')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    # app.register_blueprint(google_auth_bp, url_prefix='/api/auth')  # Temporarily disabled for stable launch
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'Agentic CRM'}
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
