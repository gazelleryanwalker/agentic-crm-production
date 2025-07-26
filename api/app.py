from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
import sys
import traceback

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Create a simple Flask app for serverless
app = Flask(__name__)
CORS(app)

# Basic configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key')

# Simple health check
@app.route('/health')
@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'Agentic CRM',
        'environment': 'production'
    })

# Simple login endpoint for testing
@app.route('/api/auth/login', methods=['POST'])
def simple_login():
    try:
        data = request.get_json()
        username = data.get('username', '')
        password = data.get('password', '')
        
        # Simple hardcoded admin check for now
        if username in ['admin', 'admin@agenticcrm.com'] and password == 'admin123':
            return jsonify({
                'success': True,
                'access_token': 'dummy-token-for-testing',
                'user': {
                    'id': 1,
                    'username': 'admin',
                    'email': 'admin@agenticcrm.com',
                    'is_admin': True
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid credentials'
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

# Simple dashboard endpoint
@app.route('/api/dashboard')
def dashboard():
    return jsonify({
        'success': True,
        'message': 'Dashboard data',
        'stats': {
            'total_contacts': 0,
            'total_deals': 0,
            'total_tasks': 0,
            'seo_projects': 0
        }
    })

# Simple SEO endpoint
@app.route('/api/seo/projects')
def seo_projects():
    return jsonify({
        'success': True,
        'projects': [],
        'message': 'SEO projects endpoint working'
    })

# Serve the frontend
@app.route('/')
def serve_frontend():
    try:
        # Read the index.html file
        frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
        with open(frontend_path, 'r') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Agentic CRM</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .container {{ max-width: 600px; margin: 0 auto; }}
                .status {{ padding: 20px; background: #e8f5e8; border-radius: 8px; }}
                .error {{ background: #ffe8e8; }}
                .button {{ display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Agentic CRM</h1>
                <div class="status">
                    <h2>✅ Backend is Working!</h2>
                    <p>The Flask backend is running successfully on Vercel.</p>
                    <p><strong>Test Credentials:</strong></p>
                    <ul>
                        <li>Username: admin</li>
                        <li>Password: admin123</li>
                    </ul>
                    <a href="/api/health" class="button">Check API Health</a>
                    <a href="/api/dashboard" class="button">Test Dashboard API</a>
                    <a href="/api/seo/projects" class="button">Test SEO API</a>
                </div>
                <div class="status error">
                    <h3>Frontend Loading Issue</h3>
                    <p>Error loading frontend: {str(e)}</p>
                    <p>But the backend APIs are working properly!</p>
                </div>
            </div>
        </body>
        </html>
        """

# Error handler
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
        'message': str(error),
        'traceback': traceback.format_exc()
    }), 500

if __name__ == '__main__':
    app.run(debug=True)
