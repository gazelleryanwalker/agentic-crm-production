import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def validate_email(email: str) -> bool:
    """Validate email address format"""
    
    if not email:
        return False
    
    # RFC 5322 compliant email regex (simplified)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    return bool(re.match(email_pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate phone number format (flexible international format)"""
    
    if not phone:
        return True  # Phone is optional
    
    # Remove common separators
    clean_phone = re.sub(r'[\s\-\(\)\+\.]', '', phone)
    
    # Check if it's all digits and reasonable length
    if not clean_phone.isdigit():
        return False
    
    # Length should be between 7 and 15 digits (international standard)
    return 7 <= len(clean_phone) <= 15

def validate_required_fields(data: Dict, required_fields: List[str]) -> Dict[str, List[str]]:
    """Validate that required fields are present and not empty"""
    
    errors = {}
    
    for field in required_fields:
        if field not in data:
            errors.setdefault('missing', []).append(field)
        elif not data[field] or (isinstance(data[field], str) and not data[field].strip()):
            errors.setdefault('empty', []).append(field)
    
    return errors

def validate_contact_data(data: Dict) -> Dict[str, List[str]]:
    """Validate contact data comprehensively"""
    
    errors = {}
    
    # Required fields
    required = ['first_name', 'last_name', 'email']
    required_errors = validate_required_fields(data, required)
    if required_errors:
        errors.update(required_errors)
    
    # Email validation
    if data.get('email') and not validate_email(data['email']):
        errors.setdefault('invalid', []).append('email')
    
    # Phone validation
    if data.get('phone') and not validate_phone(data['phone']):
        errors.setdefault('invalid', []).append('phone')
    
    # Name length validation
    for field in ['first_name', 'last_name']:
        if data.get(field) and len(data[field]) > 100:
            errors.setdefault('too_long', []).append(field)
    
    # Title length validation
    if data.get('title') and len(data['title']) > 200:
        errors.setdefault('too_long', []).append('title')
    
    # Lead status validation
    valid_statuses = ['new', 'contacted', 'qualified', 'proposal', 'negotiation', 'closed', 'lost']
    if data.get('lead_status') and data['lead_status'] not in valid_statuses:
        errors.setdefault('invalid', []).append('lead_status')
    
    # Lead score validation
    if data.get('lead_score') is not None:
        try:
            score = int(data['lead_score'])
            if not 0 <= score <= 100:
                errors.setdefault('out_of_range', []).append('lead_score')
        except (ValueError, TypeError):
            errors.setdefault('invalid', []).append('lead_score')
    
    return errors

def validate_company_data(data: Dict) -> Dict[str, List[str]]:
    """Validate company data"""
    
    errors = {}
    
    # Required fields
    required = ['name']
    required_errors = validate_required_fields(data, required)
    if required_errors:
        errors.update(required_errors)
    
    # Name length validation
    if data.get('name') and len(data['name']) > 200:
        errors.setdefault('too_long', []).append('name')
    
    # Domain validation
    if data.get('domain'):
        domain_pattern = r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(domain_pattern, data['domain']):
            errors.setdefault('invalid', []).append('domain')
    
    # Industry validation
    if data.get('industry') and len(data['industry']) > 100:
        errors.setdefault('too_long', []).append('industry')
    
    # Size validation
    valid_sizes = ['startup', 'small', 'medium', 'large', 'enterprise']
    if data.get('size') and data['size'] not in valid_sizes:
        errors.setdefault('invalid', []).append('size')
    
    # Annual revenue validation
    if data.get('annual_revenue') is not None:
        try:
            revenue = float(data['annual_revenue'])
            if revenue < 0:
                errors.setdefault('invalid', []).append('annual_revenue')
        except (ValueError, TypeError):
            errors.setdefault('invalid', []).append('annual_revenue')
    
    return errors

def validate_deal_data(data: Dict) -> Dict[str, List[str]]:
    """Validate deal data"""
    
    errors = {}
    
    # Required fields
    required = ['title', 'value', 'stage']
    required_errors = validate_required_fields(data, required)
    if required_errors:
        errors.update(required_errors)
    
    # Title length validation
    if data.get('title') and len(data['title']) > 200:
        errors.setdefault('too_long', []).append('title')
    
    # Value validation
    if data.get('value') is not None:
        try:
            value = float(data['value'])
            if value < 0:
                errors.setdefault('invalid', []).append('value')
        except (ValueError, TypeError):
            errors.setdefault('invalid', []).append('value')
    
    # Stage validation
    valid_stages = ['prospecting', 'qualification', 'needs analysis', 'proposal', 'negotiation', 'closing', 'won', 'lost']
    if data.get('stage') and data['stage'].lower() not in valid_stages:
        errors.setdefault('invalid', []).append('stage')
    
    # Probability validation
    if data.get('probability') is not None:
        try:
            prob = int(data['probability'])
            if not 0 <= prob <= 100:
                errors.setdefault('out_of_range', []).append('probability')
        except (ValueError, TypeError):
            errors.setdefault('invalid', []).append('probability')
    
    # Date validation
    if data.get('expected_close_date'):
        if not validate_date_string(data['expected_close_date']):
            errors.setdefault('invalid', []).append('expected_close_date')
    
    return errors

def validate_task_data(data: Dict) -> Dict[str, List[str]]:
    """Validate task data"""
    
    errors = {}
    
    # Required fields
    required = ['title']
    required_errors = validate_required_fields(data, required)
    if required_errors:
        errors.update(required_errors)
    
    # Title length validation
    if data.get('title') and len(data['title']) > 200:
        errors.setdefault('too_long', []).append('title')
    
    # Priority validation
    valid_priorities = ['low', 'medium', 'high', 'urgent']
    if data.get('priority') and data['priority'] not in valid_priorities:
        errors.setdefault('invalid', []).append('priority')
    
    # Status validation
    valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
    if data.get('status') and data['status'] not in valid_statuses:
        errors.setdefault('invalid', []).append('status')
    
    # Due date validation
    if data.get('due_date'):
        if not validate_date_string(data['due_date']):
            errors.setdefault('invalid', []).append('due_date')
        else:
            # Check if due date is not in the past (for new tasks)
            try:
                due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
                if due_date < datetime.utcnow():
                    errors.setdefault('past_date', []).append('due_date')
            except:
                pass
    
    return errors

def validate_activity_data(data: Dict) -> Dict[str, List[str]]:
    """Validate activity data"""
    
    errors = {}
    
    # Required fields
    required = ['type', 'subject']
    required_errors = validate_required_fields(data, required)
    if required_errors:
        errors.update(required_errors)
    
    # Type validation
    valid_types = ['email', 'call', 'meeting', 'note', 'task']
    if data.get('type') and data['type'] not in valid_types:
        errors.setdefault('invalid', []).append('type')
    
    # Subject length validation
    if data.get('subject') and len(data['subject']) > 200:
        errors.setdefault('too_long', []).append('subject')
    
    # Duration validation
    if data.get('duration_minutes') is not None:
        try:
            duration = int(data['duration_minutes'])
            if duration < 0 or duration > 1440:  # Max 24 hours
                errors.setdefault('out_of_range', []).append('duration_minutes')
        except (ValueError, TypeError):
            errors.setdefault('invalid', []).append('duration_minutes')
    
    # Activity date validation
    if data.get('activity_date'):
        if not validate_date_string(data['activity_date']):
            errors.setdefault('invalid', []).append('activity_date')
    
    return errors

def validate_date_string(date_str: str) -> bool:
    """Validate date string format"""
    
    if not date_str:
        return False
    
    # Try common date formats
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%d %H:%M:%S'
    ]
    
    for fmt in formats:
        try:
            datetime.strptime(date_str.replace('+00:00', ''), fmt)
            return True
        except ValueError:
            continue
    
    return False

def validate_pagination_params(page: Any, per_page: Any) -> Dict[str, Any]:
    """Validate and normalize pagination parameters"""
    
    errors = {}
    normalized = {}
    
    # Validate page
    try:
        page_num = int(page) if page is not None else 1
        if page_num < 1:
            page_num = 1
        normalized['page'] = page_num
    except (ValueError, TypeError):
        errors['page'] = 'Invalid page number'
        normalized['page'] = 1
    
    # Validate per_page
    try:
        per_page_num = int(per_page) if per_page is not None else 20
        if per_page_num < 1:
            per_page_num = 20
        elif per_page_num > 100:  # Limit to prevent abuse
            per_page_num = 100
        normalized['per_page'] = per_page_num
    except (ValueError, TypeError):
        errors['per_page'] = 'Invalid per_page number'
        normalized['per_page'] = 20
    
    return {'errors': errors, 'params': normalized}

def validate_search_query(query: str, max_length: int = 500) -> Dict[str, Any]:
    """Validate search query"""
    
    errors = {}
    normalized = {}
    
    if not query:
        errors['query'] = 'Search query is required'
        return {'errors': errors, 'query': ''}
    
    # Length validation
    if len(query) > max_length:
        errors['query'] = f'Query too long (max {max_length} characters)'
        normalized['query'] = query[:max_length]
    else:
        normalized['query'] = query.strip()
    
    # Basic sanitization
    normalized['query'] = re.sub(r'[<>"\']', '', normalized['query'])
    
    return {'errors': errors, 'query': normalized['query']}

def validate_memory_data(data: Dict) -> Dict[str, List[str]]:
    """Validate memory data"""
    
    errors = {}
    
    # Required fields
    required = ['content', 'memory_type']
    required_errors = validate_required_fields(data, required)
    if required_errors:
        errors.update(required_errors)
    
    # Content length validation
    if data.get('content') and len(data['content']) > 10000:
        errors.setdefault('too_long', []).append('content')
    
    # Memory type validation
    valid_types = ['user', 'session', 'agent']
    if data.get('memory_type') and data['memory_type'] not in valid_types:
        errors.setdefault('invalid', []).append('memory_type')
    
    # Category length validation
    if data.get('category') and len(data['category']) > 100:
        errors.setdefault('too_long', []).append('category')
    
    # Tags validation
    if data.get('tags'):
        if not isinstance(data['tags'], list):
            errors.setdefault('invalid', []).append('tags')
        else:
            for tag in data['tags']:
                if not isinstance(tag, str) or len(tag) > 50:
                    errors.setdefault('invalid', []).append('tags')
                    break
    
    return errors

def sanitize_input_data(data: Dict, allowed_fields: List[str]) -> Dict:
    """Sanitize input data by removing disallowed fields and cleaning values"""
    
    sanitized = {}
    
    for field in allowed_fields:
        if field in data:
            value = data[field]
            
            # Handle different data types
            if isinstance(value, str):
                # Basic HTML/script tag removal
                value = re.sub(r'<[^>]*>', '', value)
                # Remove null bytes
                value = value.replace('\x00', '')
                # Trim whitespace
                value = value.strip()
            
            sanitized[field] = value
    
    return sanitized

def format_validation_errors(errors: Dict[str, List[str]]) -> List[str]:
    """Format validation errors into user-friendly messages"""
    
    messages = []
    
    if 'missing' in errors:
        messages.append(f"Missing required fields: {', '.join(errors['missing'])}")
    
    if 'empty' in errors:
        messages.append(f"Empty required fields: {', '.join(errors['empty'])}")
    
    if 'invalid' in errors:
        messages.append(f"Invalid format for fields: {', '.join(errors['invalid'])}")
    
    if 'too_long' in errors:
        messages.append(f"Fields too long: {', '.join(errors['too_long'])}")
    
    if 'out_of_range' in errors:
        messages.append(f"Values out of range: {', '.join(errors['out_of_range'])}")
    
    if 'past_date' in errors:
        messages.append(f"Past dates not allowed: {', '.join(errors['past_date'])}")
    
    return messages
