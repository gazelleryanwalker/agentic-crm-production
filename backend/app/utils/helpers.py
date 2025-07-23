import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import json
import logging

logger = logging.getLogger(__name__)

def parse_date(date_input: Union[str, datetime, None]) -> Optional[datetime]:
    """Parse various date formats into datetime object"""
    
    if not date_input:
        return None
    
    if isinstance(date_input, datetime):
        return date_input
    
    if not isinstance(date_input, str):
        return None
    
    # Common date formats to try
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%d %H:%M:%S',
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%Y/%m/%d'
    ]
    
    # Clean the date string
    date_str = date_input.strip()
    
    # Handle timezone offset
    if '+' in date_str and date_str.endswith('+00:00'):
        date_str = date_str.replace('+00:00', '')
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"Could not parse date: {date_input}")
    return None

def format_currency(amount: float, currency: str = 'USD') -> str:
    """Format currency amount for display"""
    
    if amount is None:
        return '$0'
    
    try:
        if currency.upper() == 'USD':
            if amount >= 1000000:
                return f"${amount/1000000:.1f}M"
            elif amount >= 1000:
                return f"${amount/1000:.1f}K"
            else:
                return f"${amount:,.0f}"
        else:
            return f"{amount:,.2f} {currency}"
    except (ValueError, TypeError):
        return '$0'

def sanitize_input(input_str: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent XSS and other attacks"""
    
    if not input_str:
        return ""
    
    # Convert to string if not already
    if not isinstance(input_str, str):
        input_str = str(input_str)
    
    # Remove HTML tags
    input_str = re.sub(r'<[^>]*>', '', input_str)
    
    # Remove script tags and their content
    input_str = re.sub(r'<script[^>]*>.*?</script>', '', input_str, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove dangerous characters
    input_str = re.sub(r'[<>"\']', '', input_str)
    
    # Remove null bytes
    input_str = input_str.replace('\x00', '')
    
    # Limit length
    if len(input_str) > max_length:
        input_str = input_str[:max_length]
    
    return input_str.strip()

def generate_slug(text: str, max_length: int = 50) -> str:
    """Generate URL-friendly slug from text"""
    
    if not text:
        return ""
    
    # Convert to lowercase
    slug = text.lower()
    
    # Replace spaces and special characters with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Limit length
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
    
    return slug

def extract_domain_from_email(email: str) -> Optional[str]:
    """Extract domain from email address"""
    
    if not email or '@' not in email:
        return None
    
    try:
        return email.split('@')[1].lower()
    except IndexError:
        return None

def calculate_age_in_days(date: datetime) -> int:
    """Calculate age in days from a given date"""
    
    if not date:
        return 0
    
    return (datetime.utcnow() - date).days

def format_time_ago(date: datetime) -> str:
    """Format datetime as 'time ago' string"""
    
    if not date:
        return "Unknown"
    
    now = datetime.utcnow()
    diff = now - date
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length with suffix"""
    
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def normalize_phone_number(phone: str) -> str:
    """Normalize phone number format"""
    
    if not phone:
        return ""
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Format based on length
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone  # Return original if can't format

def extract_initials(name: str) -> str:
    """Extract initials from full name"""
    
    if not name:
        return ""
    
    words = name.strip().split()
    initials = ''.join([word[0].upper() for word in words if word])
    
    return initials[:3]  # Limit to 3 characters

def calculate_percentage(part: float, total: float) -> float:
    """Calculate percentage with division by zero protection"""
    
    if not total or total == 0:
        return 0.0
    
    return round((part / total) * 100, 1)

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely parse JSON string with fallback"""
    
    if not json_str:
        return default
    
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """Safely serialize object to JSON with fallback"""
    
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return default

def merge_dicts(*dicts: Dict) -> Dict:
    """Merge multiple dictionaries, later ones override earlier ones"""
    
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    
    return result

def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """Flatten nested dictionary"""
    
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    
    return dict(items)

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split list into chunks of specified size"""
    
    if not lst or chunk_size <= 0:
        return []
    
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def remove_duplicates(lst: List, key_func: callable = None) -> List:
    """Remove duplicates from list, optionally using key function"""
    
    if not lst:
        return []
    
    if key_func:
        seen = set()
        result = []
        for item in lst:
            key = key_func(item)
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result
    else:
        return list(dict.fromkeys(lst))  # Preserves order

def generate_random_color() -> str:
    """Generate random hex color"""
    
    import random
    return f"#{random.randint(0, 0xFFFFFF):06x}"

def is_business_day(date: datetime) -> bool:
    """Check if date is a business day (Monday-Friday)"""
    
    return date.weekday() < 5

def next_business_day(date: datetime = None) -> datetime:
    """Get next business day"""
    
    if not date:
        date = datetime.utcnow()
    
    next_day = date + timedelta(days=1)
    
    # Skip weekends
    while next_day.weekday() >= 5:
        next_day += timedelta(days=1)
    
    return next_day

def business_days_between(start_date: datetime, end_date: datetime) -> int:
    """Calculate number of business days between two dates"""
    
    if start_date >= end_date:
        return 0
    
    current = start_date
    count = 0
    
    while current < end_date:
        if is_business_day(current):
            count += 1
        current += timedelta(days=1)
    
    return count

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"

def validate_url(url: str) -> bool:
    """Validate URL format"""
    
    if not url:
        return False
    
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))

def extract_urls_from_text(text: str) -> List[str]:
    """Extract URLs from text"""
    
    if not text:
        return []
    
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    
    return url_pattern.findall(text)

def mask_sensitive_data(text: str, mask_char: str = '*') -> str:
    """Mask sensitive data like emails, phone numbers, etc."""
    
    if not text:
        return ""
    
    # Mask email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                  lambda m: m.group(0)[:2] + mask_char * (len(m.group(0)) - 4) + m.group(0)[-2:], 
                  text)
    
    # Mask phone numbers
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', 
                  lambda m: mask_char * (len(m.group(0)) - 4) + m.group(0)[-4:], 
                  text)
    
    return text

def create_pagination_info(page: int, per_page: int, total_items: int) -> Dict:
    """Create pagination information dictionary"""
    
    total_pages = (total_items + per_page - 1) // per_page  # Ceiling division
    
    return {
        'page': page,
        'per_page': per_page,
        'total_items': total_items,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < total_pages else None
    }
