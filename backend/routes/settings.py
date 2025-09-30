
from flask import Blueprint, request, jsonify
import json
import os

settings_bp = Blueprint('settings', __name__)

# Define the path for the settings file
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), '..', 'settings.json')

def get_default_settings():
    """Returns a dictionary of default settings."""
    return {
        "store_name": "StockPoint Plus",
        "store_address": "123 Market St, Suite 100",
        "store_contact": "+1 (555) 123-4567",
        "store_email": "contact@stockpoint.plus",
        "gst_number": "",
        "currency_symbol": "$",
        "tax_rate": 8.0,
        "printer_name": "Default Printer",
        "paper_size": "80mm",
        "print_logo": True,
        "receipt_header": "Thank you for your business!",
        "receipt_footer": "Please come again.",
        "autocut": True,
        "cash_drawer": False,
        "copies": 1,
        "barcode_format": "CODE128",
        "barcode_width": 2,
        "barcode_height": 100,
        "barcode_display_value": True,
        "theme": "light",
        "enable_sounds": True
    }

@settings_bp.route('/settings', methods=['GET'])
def get_settings():
    """Get the current application settings."""
    try:
        if not os.path.exists(SETTINGS_FILE):
            # If file doesn't exist, create it with default settings
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(get_default_settings(), f, indent=4)
        
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
            
        return jsonify({'success': True, 'data': settings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@settings_bp.route('/settings', methods=['POST'])
def save_settings():
    """Save the application settings."""
    try:
        new_settings = request.get_json()
        if not new_settings:
            return jsonify({'success': False, 'error': 'No settings data provided'}), 400

        # For safety, merge with existing/default settings to not miss any key
        current_settings = get_default_settings()
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                current_settings.update(json.load(f))
        
        current_settings.update(new_settings)

        with open(SETTINGS_FILE, 'w') as f:
            json.dump(current_settings, f, indent=4)
            
        return jsonify({'success': True, 'message': 'Settings saved successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500