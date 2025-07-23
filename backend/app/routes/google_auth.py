import os
import json
from flask import Blueprint, request, jsonify, redirect, session, url_for
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.services.google_service import GoogleWorkspaceService
from app.models.user import User
from app import db
from flask_jwt_extended import create_access_token, create_refresh_token
import logging

logger = logging.getLogger(__name__)

google_auth_bp = Blueprint('google_auth', __name__)

# Google OAuth 2.0 configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid_configuration"

# OAuth 2.0 scopes for Google Workspace
SCOPES = [
    'openid',
    'email',
    'profile',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.file'
]

def create_flow():
    """Create Google OAuth flow"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise ValueError("Google OAuth credentials not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.")
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [f"{request.host_url}api/auth/google/callback"]
            }
        },
        scopes=SCOPES
    )
    flow.redirect_uri = f"{request.host_url}api/auth/google/callback"
    return flow

@google_auth_bp.route('/google/login', methods=['GET'])
def google_login():
    """Initiate Google OAuth login"""
    try:
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            return jsonify({
                'error': 'Google OAuth not configured',
                'message': 'Please configure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables',
                'setup_instructions': {
                    'step1': 'Go to Google Cloud Console (https://console.cloud.google.com/)',
                    'step2': 'Create a new project or select existing project',
                    'step3': 'Enable Gmail API, Calendar API, and Drive API',
                    'step4': 'Create OAuth 2.0 credentials',
                    'step5': 'Add your domain to authorized origins',
                    'step6': 'Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables'
                }
            }), 400
        
        flow = create_flow()
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        session['state'] = state
        return jsonify({
            'authorization_url': authorization_url,
            'state': state
        })
        
    except Exception as e:
        logger.error(f"Error initiating Google login: {e}")
        return jsonify({'error': 'Failed to initiate Google login', 'details': str(e)}), 500

@google_auth_bp.route('/google/callback', methods=['GET'])
def google_callback():
    """Handle Google OAuth callback"""
    try:
        # Verify state parameter
        if request.args.get('state') != session.get('state'):
            return jsonify({'error': 'Invalid state parameter'}), 400
        
        # Handle authorization code
        code = request.args.get('code')
        if not code:
            error = request.args.get('error')
            return jsonify({'error': f'Authorization failed: {error}'}), 400
        
        # Exchange code for credentials
        flow = create_flow()
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        
        # Get user info from Google
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        
        # Check if user exists or create new user
        user = User.query.filter_by(email=user_info['email']).first()
        
        if not user:
            # Create new user from Google account
            user = User(
                username=user_info['email'].split('@')[0],
                email=user_info['email'],
                first_name=user_info.get('given_name', ''),
                last_name=user_info.get('family_name', ''),
                is_active=True,
                google_id=user_info['id']
            )
            # Set a random password (user will login via Google)
            user.set_password(os.urandom(32).hex())
            db.session.add(user)
            db.session.commit()
            logger.info(f"Created new user from Google account: {user.email}")
        else:
            # Update existing user's Google ID if not set
            if not user.google_id:
                user.google_id = user_info['id']
                db.session.commit()
        
        # Store Google credentials for the user
        credentials_dict = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        # You might want to store these credentials in the database
        # For now, we'll store them in the session
        session['google_credentials'] = credentials_dict
        session['user_id'] = user.id
        
        # Create JWT tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        # Initialize Google Workspace service
        try:
            google_service = GoogleWorkspaceService(credentials=credentials)
            # Store service in session or cache for later use
            logger.info(f"Google Workspace service initialized for user: {user.email}")
        except Exception as e:
            logger.warning(f"Could not initialize Google Workspace service: {e}")
        
        # Redirect to frontend with success
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:8080')
        redirect_url = f"{frontend_url}?google_auth=success&access_token={access_token}&refresh_token={refresh_token}"
        
        return redirect(redirect_url)
        
    except Exception as e:
        logger.error(f"Error in Google callback: {e}")
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:8080')
        redirect_url = f"{frontend_url}?google_auth=error&message={str(e)}"
        return redirect(redirect_url)

@google_auth_bp.route('/google/status', methods=['GET'])
def google_status():
    """Check Google OAuth configuration status"""
    return jsonify({
        'configured': bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
        'client_id_set': bool(GOOGLE_CLIENT_ID),
        'client_secret_set': bool(GOOGLE_CLIENT_SECRET),
        'scopes': SCOPES,
        'setup_url': 'https://console.cloud.google.com/'
    })

@google_auth_bp.route('/google/disconnect', methods=['POST'])
def google_disconnect():
    """Disconnect Google account"""
    try:
        # Clear Google credentials from session
        session.pop('google_credentials', None)
        
        # You might also want to revoke the token with Google
        # and remove stored credentials from database
        
        return jsonify({'message': 'Google account disconnected successfully'})
        
    except Exception as e:
        logger.error(f"Error disconnecting Google account: {e}")
        return jsonify({'error': 'Failed to disconnect Google account'}), 500
