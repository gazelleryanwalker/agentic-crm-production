#!/usr/bin/env python3
"""
Database initialization script for Agentic CRM
This script ensures all tables are created and default admin user exists
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def init_database():
    """Initialize database with all tables and default admin user"""
    try:
        # Import after path is set
        from app import create_app, db
        from app.models.user import User
        from app.models.contact import Contact
        from app.models.deal import Deal
        from app.models.task import Task
        from app.models.memory import Memory
        from app.models.seo import SEOProject, SEOAnalysis, SEORule, SEOOptimization, SEOKeyword, SEOAudit, SEOTemplate
        
        print("Creating Flask app...")
        app = create_app()
        
        with app.app_context():
            print("Creating database tables...")
            
            # Drop all tables first to ensure clean state
            db.drop_all()
            print("Dropped existing tables")
            
            # Create all tables
            db.create_all()
            print("Created all database tables successfully")
            
            # Create default admin user
            admin_user = User.query.filter_by(username='admin').first()
            
            if not admin_user:
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
                print("✅ Default admin user created: admin@agenticcrm.com / admin123")
            else:
                print("✅ Admin user already exists")
            
            # Verify tables exist
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
                tables = result.fetchall()
            table_names = [table[0] for table in tables]
            
            expected_tables = [
                'users', 'contacts', 'deals', 'tasks', 'memories',
                'seo_projects', 'seo_analyses', 'seo_rules', 'seo_optimizations',
                'seo_keywords', 'seo_audits', 'seo_templates'
            ]
            
            print(f"✅ Created tables: {', '.join(table_names)}")
            
            missing_tables = [table for table in expected_tables if table not in table_names]
            if missing_tables:
                print(f"⚠️  Missing tables: {', '.join(missing_tables)}")
            else:
                print("✅ All expected tables created successfully")
            
            return True
            
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Initializing Agentic CRM Database...")
    success = init_database()
    if success:
        print("✅ Database initialization completed successfully!")
    else:
        print("❌ Database initialization failed!")
        sys.exit(1)
