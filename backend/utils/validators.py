"""
Validation functions for the POS system
"""

import re
from datetime import datetime

class ValidationError(Exception):
    """Custom validation error"""
    pass

def validate_required_fields(data, required_fields):
    """Validate that required fields are present"""
    missing_fields = []
    for field in required_fields:
        if field not in data or not data[field]:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

def validate_product_data(data):
    """Validate product data"""
    errors = []
    
    # Required fields
    required_fields = ['name', 'price', 'sku', 'category_id']
    for field in required_fields:
        if not data.get(field):
            errors.append(f"{field} is required")
    
    # Price validation
    if 'price' in data:
        try:
            price = float(data['price'])
            if price < 0:
                errors.append("Price cannot be negative")
        except (ValueError, TypeError):
            errors.append("Price must be a valid number")
    
    # Cost price validation
    if 'cost_price' in data:
        try:
            cost_price = float(data['cost_price'])
            if cost_price < 0:
                errors.append("Cost price cannot be negative")
        except (ValueError, TypeError):
            errors.append("Cost price must be a valid number")
    
    # Stock quantity validation
    if 'stock_quantity' in data:
        try:
            stock = int(data['stock_quantity'])
            if stock < 0:
                errors.append("Stock quantity cannot be negative")
        except (ValueError, TypeError):
            errors.append("Stock quantity must be a valid integer")
    
    # SKU validation
    if 'sku' in data:
        sku = data['sku'].strip()
        if len(sku) < 3:
            errors.append("SKU must be at least 3 characters long")
        if not re.match(r'^[A-Z0-9-_]+$', sku):
            errors.append("SKU can only contain uppercase letters, numbers, hyphens, and underscores")
    
    if errors:
        raise ValidationError(errors)

def validate_customer_data(data):
    """Validate customer data"""
    errors = []
    
    # Name is required
    if not data.get('name'):
        errors.append("Name is required")
    
    # Email validation
    if 'email' in data and data['email']:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            errors.append("Invalid email format")
    
    # Phone validation
    if 'phone' in data and data['phone']:
        phone_pattern = r'^\+?1?-?\.?\s?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})$'
        if not re.match(phone_pattern, data['phone']):
            errors.append("Invalid phone number format")
    
    if errors:
        raise ValidationError(errors)

def validate_sale_data(data):
    """Validate sale data"""
    errors = []
    
    # Required fields
    if not data.get('items'):
        errors.append("Items are required")
    elif not isinstance(data['items'], list) or len(data['items']) == 0:
        errors.append("At least one item is required")
    
    if not data.get('total_amount'):
        errors.append("Total amount is required")
    
    # Validate items
    if 'items' in data and isinstance(data['items'], list):
        for i, item in enumerate(data['items']):
            if not item.get('product_id'):
                errors.append(f"Item {i+1}: Product ID is required")
            
            if not item.get('quantity') or item['quantity'] <= 0:
                errors.append(f"Item {i+1}: Quantity must be greater than 0")
            
            if not item.get('unit_price') or item['unit_price'] <= 0:
                errors.append(f"Item {i+1}: Unit price must be greater than 0")
    
    # Amount validations
    for field in ['subtotal', 'total_amount']:
        if field in data:
            try:
                amount = float(data[field])
                if amount < 0:
                    errors.append(f"{field.replace('_', ' ').title()} cannot be negative")
            except (ValueError, TypeError):
                errors.append(f"{field.replace('_', ' ').title()} must be a valid number")
    
    if errors:
        raise ValidationError(errors)

def validate_inventory_adjustment(data):
    """Validate inventory adjustment data"""
    errors = []
    
    required_fields = ['product_id', 'type', 'quantity']
    for field in required_fields:
        if not data.get(field):
            errors.append(f"{field} is required")
    
    # Type validation
    if 'type' in data and data['type'] not in ['increase', 'decrease']:
        errors.append("Type must be 'increase' or 'decrease'")
    
    # Quantity validation
    if 'quantity' in data:
        try:
            quantity = int(data['quantity'])
            if quantity <= 0:
                errors.append("Quantity must be greater than 0")
        except (ValueError, TypeError):
            errors.append("Quantity must be a valid integer")
    
    if errors:
        raise ValidationError(errors)

def validate_date_range(start_date, end_date):
    """Validate date range"""
    errors = []
    
    try:
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        
        if start_date and end_date:
            if start_dt > end_dt:
                errors.append("Start date cannot be after end date")
    except ValueError:
        errors.append("Invalid date format. Use ISO format (YYYY-MM-DD)")
    
    if errors:
        raise ValidationError(errors)