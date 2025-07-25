from flask import Blueprint, jsonify
from app import db
from app.models.user import User

debug_bp = Blueprint('debug', __name__)

@debug_bp.route('/check-admin', methods=['GET'])
def check_admin():
    """Debug endpoint to check if admin user exists"""
    try:
        # Check if admin user exists
        admin_user = db.session.query(User).filter_by(username='admin').first()
        admin_by_email = db.session.query(User).filter_by(email='admin@agenticcrm.com').first()
        
        # Count total users
        total_users = db.session.query(User).count()
        
        return jsonify({
            'admin_user_by_username': admin_user.to_dict() if admin_user else None,
            'admin_user_by_email': admin_by_email.to_dict() if admin_by_email else None,
            'total_users': total_users,
            'database_connected': True
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'database_connected': False
        }), 500

@debug_bp.route('/create-admin', methods=['POST'])
def create_admin_manual():
    """Manually create admin user"""
    try:
        # Check if admin user already exists
        existing_admin = db.session.query(User).filter_by(username='admin').first()
        
        if existing_admin:
            return jsonify({
                'message': 'Admin user already exists',
                'user': existing_admin.to_dict()
            })
        
        # Create admin user
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
        
        return jsonify({
            'message': 'Admin user created successfully',
            'user': admin_user.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e)
        }), 500
