import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
import bcrypt
import logging

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """Hash password using bcrypt for secure storage"""
    
    if not password:
        raise ValueError("Password cannot be empty")
    
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    
    if not password or not hashed_password:
        return False
    
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def generate_token(payload: Dict, secret_key: str, expires_in_hours: int = 24) -> str:
    """Generate JWT token with expiration"""
    
    # Add expiration time
    payload['exp'] = datetime.utcnow() + timedelta(hours=expires_in_hours)
    payload['iat'] = datetime.utcnow()
    
    # Generate token
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    
    return token

def verify_token(token: str, secret_key: str) -> Optional[Dict]:
    """Verify and decode JWT token"""
    
    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None

def generate_api_key(length: int = 32) -> str:
    """Generate secure API key"""
    
    return secrets.token_urlsafe(length)

def generate_secure_filename(original_filename: str) -> str:
    """Generate secure filename to prevent path traversal attacks"""
    
    import os
    import re
    
    # Remove path components
    filename = os.path.basename(original_filename)
    
    # Remove or replace dangerous characters
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Add timestamp to ensure uniqueness
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(filename)
    
    return f"{name}_{timestamp}{ext}"

def sanitize_sql_input(input_str: str) -> str:
    """Basic SQL injection prevention (use parameterized queries instead)"""
    
    if not input_str:
        return ""
    
    # Remove common SQL injection patterns
    dangerous_patterns = [
        r"'", r'"', r';', r'--', r'/*', r'*/', r'xp_', r'sp_',
        r'union', r'select', r'insert', r'update', r'delete', r'drop',
        r'create', r'alter', r'exec', r'execute'
    ]
    
    sanitized = input_str
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    return sanitized.strip()

def validate_input_length(input_str: str, max_length: int = 1000) -> bool:
    """Validate input length to prevent buffer overflow attacks"""
    
    return len(input_str) <= max_length if input_str else True

def generate_csrf_token() -> str:
    """Generate CSRF token for form protection"""
    
    return secrets.token_urlsafe(32)

def hash_api_key(api_key: str) -> str:
    """Hash API key for secure storage"""
    
    return hashlib.sha256(api_key.encode()).hexdigest()

def constant_time_compare(a: str, b: str) -> bool:
    """Compare strings in constant time to prevent timing attacks"""
    
    if len(a) != len(b):
        return False
    
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    
    return result == 0

def encrypt_sensitive_data(data: str, key: str) -> str:
    """Simple encryption for sensitive data (use proper encryption in production)"""
    
    from cryptography.fernet import Fernet
    import base64
    
    # Generate key from provided key
    key_bytes = hashlib.sha256(key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    
    f = Fernet(fernet_key)
    encrypted = f.encrypt(data.encode())
    
    return encrypted.decode()

def decrypt_sensitive_data(encrypted_data: str, key: str) -> str:
    """Decrypt sensitive data"""
    
    from cryptography.fernet import Fernet
    import base64
    
    try:
        # Generate key from provided key
        key_bytes = hashlib.sha256(key.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        
        f = Fernet(fernet_key)
        decrypted = f.decrypt(encrypted_data.encode())
        
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        return ""

def rate_limit_key(user_id: int, action: str) -> str:
    """Generate rate limiting key"""
    
    return f"rate_limit:{user_id}:{action}"

def is_safe_redirect_url(url: str, allowed_hosts: list) -> bool:
    """Check if redirect URL is safe"""
    
    from urllib.parse import urlparse
    
    if not url:
        return False
    
    parsed = urlparse(url)
    
    # Allow relative URLs
    if not parsed.netloc:
        return True
    
    # Check against allowed hosts
    return parsed.netloc in allowed_hosts
