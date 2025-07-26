from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json

# Create a simple Flask app for Vercel
app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'fallback-jwt-key')

# Health check endpoint
@app.route('/health')
@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'Agentic CRM',
        'environment': 'production',
        'timestamp': '2024-01-01T00:00:00Z'
    })

# Authentication endpoints
@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username', '').lower()
        password = data.get('password', '')
        
        # Simple admin authentication
        if username in ['admin', 'admin@agenticcrm.com'] and password == 'admin123':
            return jsonify({
                'success': True,
                'access_token': 'dummy-jwt-token-for-testing',
                'user': {
                    'id': 1,
                    'username': 'admin',
                    'email': 'admin@agenticcrm.com',
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'is_admin': True
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid username or password'
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Dashboard endpoint
@app.route('/api/dashboard')
def dashboard():
    return jsonify({
        'success': True,
        'stats': {
            'total_contacts': 0,
            'total_deals': 0,
            'total_tasks': 0,
            'seo_projects': 0
        },
        'recent_activities': [],
        'message': 'Dashboard loaded successfully'
    })

# Contacts endpoints
@app.route('/api/contacts')
def get_contacts():
    return jsonify({
        'success': True,
        'contacts': [],
        'total': 0
    })

@app.route('/api/contacts', methods=['POST'])
def create_contact():
    return jsonify({
        'success': True,
        'message': 'Contact created successfully',
        'contact': {'id': 1, 'name': 'Test Contact'}
    })

# Deals endpoints
@app.route('/api/deals')
def get_deals():
    return jsonify({
        'success': True,
        'deals': [],
        'total': 0
    })

# Tasks endpoints
@app.route('/api/tasks')
def get_tasks():
    return jsonify({
        'success': True,
        'tasks': [],
        'total': 0
    })

# SEO endpoints
@app.route('/api/seo/projects')
def get_seo_projects():
    return jsonify({
        'success': True,
        'projects': [],
        'total': 0,
        'message': 'SEO projects loaded successfully'
    })

@app.route('/api/seo/analyze', methods=['POST'])
def analyze_website():
    data = request.get_json()
    url = data.get('url', '')
    
    return jsonify({
        'success': True,
        'analysis': {
            'url': url,
            'title': 'Sample Website',
            'meta_description': 'Sample meta description',
            'h1_tags': ['Sample H1'],
            'recommendations': [
                'Optimize meta description length',
                'Add more internal links',
                'Improve page loading speed'
            ]
        },
        'message': 'Website analysis completed'
    })

# Memory endpoints
@app.route('/api/memory')
def get_memories():
    return jsonify({
        'success': True,
        'memories': [],
        'total': 0
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': str(error)
    }), 500

# This is required for Vercel
if __name__ == "__main__":
    app.run()
