from flask import Flask, jsonify, request
from flask_cors import CORS
from database import init_db, db
from routes import register_blueprints
from models import *
import os
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import uuid

app = Flask(__name__, instance_relative_config=False)
CORS(app)

# Initialize database
init_db(app)

# Import and register blueprints after app initialization
try:
    from routes import register_blueprints
    register_blueprints(app)
    print("Blueprints registered successfully")
except ImportError as e:
    print(f"Error importing blueprints: {e}")
    print("Continuing without blueprints...")

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'success': True,
        'message': 'POS API is running',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

# API info endpoint
@app.route('/info', methods=['GET'])
def api_info():
    return jsonify({
        'success': True,
        'data': {
            'name': 'POS System API',
            'version': '1.0.0',
            'description': 'Point of Sale System REST API',
            'endpoints': {
                'products': '/api/products',
                'sales': '/api/sales',
                'customers': '/api/customers',
                'inventory': '/api/inventory',
                'reports': '/api/reports',
                'categories': '/api/categories'
            }
        }
    })

# Dashboard endpoint (main overview)
@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    try:
        # Get dashboard statistics
        total_products = Product.query.filter_by(is_active=True).count()
        total_customers = Customer.query.count()
        
        # Sales today
        today = datetime.utcnow().date()
        today_sales = Sale.query.filter(
            func.date(Sale.created_at) == today
        ).all()
        today_revenue = sum(sale.total_amount for sale in today_sales)
        
        # Sales this month
        first_day_month = today.replace(day=1)
        month_sales = Sale.query.filter(
            Sale.created_at >= first_day_month
        ).all()
        month_revenue = sum(sale.total_amount for sale in month_sales)
        
        # Low stock products
        low_stock_products = Product.query.filter(
            Product.stock_quantity <= Product.min_stock_level,
            Product.is_active == True
        ).count()
        
        # Recent sales
        recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(5).all()
        
        # Top selling products (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        top_products = db.session.query(
            Product.name,
            func.sum(SaleItem.quantity).label('total_sold')
        ).join(SaleItem).join(Sale).filter(
            Sale.created_at >= thirty_days_ago
        ).group_by(Product.id).order_by(
            func.sum(SaleItem.quantity).desc()
        ).limit(5).all()
        
        return jsonify({
            'success': True,
            'data': {
                'total_products': total_products,
                'total_customers': total_customers,
                'today_revenue': today_revenue,
                'today_sales_count': len(today_sales),
                'month_revenue': month_revenue,
                'month_sales_count': len(month_sales),
                'low_stock_products': low_stock_products,
                'recent_sales': [sale.to_dict() for sale in recent_sales],
                'top_products': [{'name': p[0], 'total_sold': p[1]} for p in top_products]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# Main execution
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)