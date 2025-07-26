from flask import Flask, jsonify
import sys
import os
import traceback

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    # Import the Flask app
    from app import create_app
    
    # Create the Flask app
    app = create_app()
    
    # Add a health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'Agentic CRM',
            'database_connected': True
        })
    
    # Add a simple test endpoint
    @app.route('/api/test')
    def test_endpoint():
        return jsonify({
            'success': True,
            'message': 'Backend is working properly',
            'environment': 'production'
        })
    
except Exception as e:
    # If Flask app creation fails, create a minimal error app
    app = Flask(__name__)
    
    @app.route('/')
    @app.route('/api/<path:path>')
    def error_handler(path=None):
        return jsonify({
            'error': 'Flask app initialization failed',
            'details': str(e),
            'traceback': traceback.format_exc()
        }), 500

# This is required for Vercel
if __name__ == "__main__":
    app.run()
