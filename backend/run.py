#!/usr/bin/env python3
"""
Agentic CRM - Main Application Entry Point
Autonomous Customer Relationship Management System
"""

import os
import logging
from datetime import datetime
from app import create_app, db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/agentic_crm.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_directories():
    """Create necessary directories"""
    directories = ['logs', 'data', 'uploads']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")

def initialize_database():
    """Initialize database with tables and sample data"""
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Check if we need to create a default admin user
            from app.models.user import User
            try:
                admin_user = db.session.query(User).filter(User.username == 'admin').first()
            except Exception as e:
                logger.warning(f"Database query error (likely schema mismatch): {e}")
                logger.info("Attempting to add missing columns to existing database...")
                
                # Add google_id column if it doesn't exist
                try:
                    db.engine.execute('ALTER TABLE users ADD COLUMN google_id VARCHAR(100) UNIQUE')
                    logger.info("Added google_id column to users table")
                except Exception as alter_error:
                    logger.info(f"Column may already exist or other issue: {alter_error}")
                
                # Try the query again
                try:
                    admin_user = db.session.query(User).filter(User.username == 'admin').first()
                except Exception as retry_error:
                    logger.error(f"Still cannot query users table: {retry_error}")
                    admin_user = None
            
            if not admin_user:
                # Create default admin user
                admin_user = User.create_user(
                    username='admin',
                    email='admin@agenticcrm.local',
                    password='admin123',  # Change this in production!
                    first_name='System',
                    last_name='Administrator'
                )
                admin_user.is_admin = True
                
                db.session.add(admin_user)
                db.session.commit()
                
                logger.info("Created default admin user (username: admin, password: admin123)")
                logger.warning("IMPORTANT: Change the default admin password in production!")
            
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

def setup_environment():
    """Setup environment variables and configuration"""
    
    # Set default environment variables if not present
    env_defaults = {
        'FLASK_ENV': 'development',
        'SECRET_KEY': 'agentic-crm-secret-key-change-in-production',
        'JWT_SECRET_KEY': 'jwt-secret-change-in-production',
        'DATABASE_URL': 'sqlite:///agentic_crm.db',
        'OPENAI_API_KEY': '',  # Must be set by user
        'REDIS_URL': 'redis://localhost:6379',
    }
    
    for key, default_value in env_defaults.items():
        if key not in os.environ:
            os.environ[key] = default_value
    
    # Warn about missing critical environment variables
    if not os.environ.get('OPENAI_API_KEY'):
        logger.warning("OPENAI_API_KEY not set - AI features will use fallback methods")
    
    logger.info("Environment configuration completed")

if __name__ == '__main__':
    # Setup
    create_directories()
    setup_environment()
    
    # Create Flask app
    app = create_app()
    
    # Initialize database
    initialize_database()
    
    # Print startup information
    print("\n" + "="*60)
    print("🚀 AGENTIC CRM - Autonomous Customer Relationship Management")
    print("="*60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌍 Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"🗄️  Database: {os.environ.get('DATABASE_URL', 'sqlite:///agentic_crm.db')}")
    print(f"🤖 AI Features: {'Enabled' if os.environ.get('OPENAI_API_KEY') else 'Fallback Mode'}")
    print("="*60)
    print("📋 Quick Start:")
    print("   1. Access the application at: http://localhost:5000")
    print("   2. Default admin login: admin / admin123")
    print("   3. Set OPENAI_API_KEY environment variable for full AI features")
    print("   4. Configure Google OAuth for workspace integration")
    print("="*60)
    print("🔧 API Endpoints:")
    print("   • Authentication: /api/auth/*")
    print("   • CRM Operations: /api/crm/*")
    print("   • AI Intelligence: /api/ai/*")
    print("   • Memory System: /api/memory/*")
    print("   • Dashboard: /api/dashboard/*")
    print("="*60)
    print("📚 Documentation: Check README.md for detailed setup instructions")
    print("🐛 Issues: Report at https://github.com/your-repo/agentic-crm")
    print("="*60 + "\n")
    
    # Run the application
    try:
        app.run(
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000)),
            debug=os.environ.get('FLASK_ENV') == 'development'
        )
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise
