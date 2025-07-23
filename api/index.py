from flask import Flask
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import the Flask app
from app import create_app

# Create the Flask app
app = create_app()

# This is required for Vercel
if __name__ == "__main__":
    app.run()
