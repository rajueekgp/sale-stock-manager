"""
Routes package initialization
"""

# Import all blueprints
from .products import products_bp
from .sales import sales_bp
from .customers import customers_bp
from .inventory import inventory_bp
from .reports import reports_bp
from .categories import categories_bp
from .settings import settings_bp
from .purchases import purchases_bp
from .returns import returns_bp
from .credit_notes import credit_notes_bp
from .database_viewer import database_viewer_bp

def register_blueprints(app):
    """Register all blueprints with the Flask application"""
    
    # Register blueprints with URL prefixes
    app.register_blueprint(products_bp, url_prefix='/api')
    app.register_blueprint(sales_bp, url_prefix='/api')
    app.register_blueprint(customers_bp, url_prefix='/api')
    app.register_blueprint(inventory_bp, url_prefix='/api')
    app.register_blueprint(reports_bp, url_prefix='/api')
    app.register_blueprint(categories_bp, url_prefix='/api')
    app.register_blueprint(settings_bp, url_prefix='/api')
    app.register_blueprint(purchases_bp, url_prefix='/api')
    app.register_blueprint(returns_bp, url_prefix='/api')
    app.register_blueprint(credit_notes_bp, url_prefix='/api')
    app.register_blueprint(database_viewer_bp, url_prefix='/api')
    
    print("All blueprints registered successfully")

__all__ = [
    'products_bp',
    'sales_bp', 
    'customers_bp',
    'inventory_bp',
    'reports_bp',
    'categories_bp',
    'settings_bp',
    'purchases_bp',
    'returns_bp',
    'credit_notes_bp',
    'database_viewer_bp',
    'register_blueprints'
]