"""
Utility helper functions for the POS system
"""

import re
import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import jsonify, request

def generate_sku():
    """Generate a unique SKU"""
    return f"SKU-{str(uuid.uuid4())[:8].upper()}"

def generate_sale_number():
    """Generate a unique sale number"""
    return f"SALE-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

def generate_purchase_number():
    """Generate a unique purchase number"""
    return f"PUR-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format"""
    pattern = r'^\+?1?-?\.?\s?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})$'
    return re.match(pattern, phone) is not None

def format_currency(amount):
    """Format amount as currency"""
    return f"${amount:.2f}"

def calculate_tax(amount, tax_rate=0.08):
    """Calculate tax amount"""
    return amount * tax_rate

def calculate_discount(amount, discount_percent):
    """Calculate discount amount"""
    return amount * (discount_percent / 100)

def paginate_query(query, page, per_page=20):
    """Paginate a SQLAlchemy query"""
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

def get_date_range(days=30):
    """Get date range for reports"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date

def safe_float(value, default=0.0):
    """Safely convert value to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """Safely convert value to integer"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def format_datetime(dt):
    """Format datetime for API response"""
    if dt:
        return dt.isoformat()
    return None

def parse_datetime(dt_string):
    """Parse datetime string"""
    try:
        return datetime.fromisoformat(dt_string)
    except (ValueError, TypeError):
        return None

class APIResponse:
    """Standardized API response helper"""
    
    @staticmethod
    def success(data=None, message="Success", status_code=200):
        response = {
            'success': True,
            'message': message
        }
        if data is not None:
            response['data'] = data
        return jsonify(response), status_code
    
    @staticmethod
    def error(message="An error occurred", status_code=400, errors=None):
        response = {
            'success': False,
            'error': message
        }
        if errors:
            response['errors'] = errors
        return jsonify(response), status_code
    
    @staticmethod
    def not_found(message="Resource not found"):
        return APIResponse.error(message, 404)
    
    @staticmethod
    def unauthorized(message="Unauthorized"):
        return APIResponse.error(message, 401)
    
    @staticmethod
    def forbidden(message="Forbidden"):
        return APIResponse.error(message, 403)
    
    @staticmethod
    def validation_error(errors):
        return APIResponse.error("Validation failed", 422, errors)