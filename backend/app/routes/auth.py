from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.utils.validators import validate_email, validate_required_fields, format_validation_errors
from app.utils.security import hash_password, verify_password
from app.utils.helpers import sanitize_input
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        validation_errors = validate_required_fields(data, required_fields)
        
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': format_validation_errors(validation_errors)
            }), 400
        
        # Sanitize inputs
        username = sanitize_input(data['username'], 80)
        email = sanitize_input(data['email'], 120).lower()
        password = data['password']
        first_name = sanitize_input(data.get('first_name', ''), 100)
        last_name = sanitize_input(data.get('last_name', ''), 100)
        
        # Validate email format
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check password strength
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400
        
        # Check if user already exists
        existing_user = db.session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.username == username:
                return jsonify({'error': 'Username already exists'}), 409
            else:
                return jsonify({'error': 'Email already registered'}), 409
        
        # Create new user
        user = User.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        logger.info(f"New user registered: {username}")
        
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return access token"""
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['email', 'password']
        validation_errors = validate_required_fields(data, required_fields)
        
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': format_validation_errors(validation_errors)
            }), 400
        
        email = sanitize_input(data['email'], 120).lower()
        password = data['password']
        
        # Find user by email or username
        user = db.session.query(User).filter(
            (User.email == email) | (User.username == email)
        ).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Update last login
        from datetime import datetime
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        logger.info(f"User logged in: {user.username}")
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    
    try:
        user_id = get_jwt_identity()
        user = db.session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Profile fetch error: {e}")
        return jsonify({'error': 'Failed to fetch profile'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user profile"""
    
    try:
        user_id = get_jwt_identity()
        user = db.session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update allowed fields
        allowed_fields = ['first_name', 'last_name', 'timezone', 'preferences']
        
        for field in allowed_fields:
            if field in data:
                if field in ['first_name', 'last_name']:
                    setattr(user, field, sanitize_input(data[field], 100))
                elif field == 'timezone':
                    setattr(user, field, sanitize_input(data[field], 50))
                elif field == 'preferences':
                    # Store preferences as JSON string
                    import json
                    setattr(user, field, json.dumps(data[field]))
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Profile updated for user: {user.username}")
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    
    try:
        user_id = get_jwt_identity()
        user = db.session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['current_password', 'new_password']
        validation_errors = validate_required_fields(data, required_fields)
        
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': format_validation_errors(validation_errors)
            }), 400
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        # Verify current password
        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Validate new password
        if len(new_password) < 8:
            return jsonify({'error': 'New password must be at least 8 characters long'}), 400
        
        if new_password == current_password:
            return jsonify({'error': 'New password must be different from current password'}), 400
        
        # Update password
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Password changed for user: {user.username}")
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Password change error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to change password'}), 500

@auth_bp.route('/verify-token', methods=['POST'])
@jwt_required()
def verify_token():
    """Verify if token is valid"""
    
    try:
        user_id = get_jwt_identity()
        user = db.session.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            return jsonify({'valid': False}), 401
        
        return jsonify({
            'valid': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return jsonify({'valid': False}), 401

@auth_bp.route('/google/auth', methods=['POST'])
def google_auth():
    """Handle Google OAuth authentication"""
    
    try:
        data = request.get_json()
        if not data or 'code' not in data:
            return jsonify({'error': 'Authorization code required'}), 400
        
        # TODO: Implement Google OAuth flow
        # This would involve:
        # 1. Exchange code for tokens
        # 2. Get user info from Google
        # 3. Create or update user account
        # 4. Store Google credentials securely
        # 5. Return JWT token
        
        return jsonify({
            'message': 'Google authentication not yet implemented',
            'status': 'coming_soon'
        }), 501
        
    except Exception as e:
        logger.error(f"Google auth error: {e}")
        return jsonify({'error': 'Google authentication failed'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (client-side token removal)"""
    
    try:
        user_id = get_jwt_identity()
        logger.info(f"User logged out: {user_id}")
        
        # In a more sophisticated implementation, you might:
        # - Add token to blacklist
        # - Clear server-side sessions
        # - Log the logout event
        
        return jsonify({
            'message': 'Logout successful'
        }), 200
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': 'Logout failed'}), 500
