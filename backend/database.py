from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sqlite3
import os

db = SQLAlchemy()

def init_db(app):
    """Initialize database with Flask app"""
    # Use absolute path to ensure database is in project root
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'pos_system.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        seed_data()

def seed_data():
    """Seed initial data"""
    from models import Category, Product, Customer
    
    # Check if data already exists
    if Category.query.first():
        return
    
    # Create categories
    categories = [
        Category(name='Electronics', description='Electronic items'),
        Category(name='Clothing', description='Clothing and accessories'),
        Category(name='Food', description='Food and beverages'),
        Category(name='Books', description='Books and magazines')
    ]
    
    for category in categories:
        db.session.add(category)
    
    db.session.commit()
    
    # Create sample products
    products = [
        Product(name='Laptop', price=999.99, stock_quantity=10, category_id=1, sku='LAP001'),
        Product(name='T-Shirt', price=19.99, stock_quantity=50, category_id=2, sku='TSH001'),
        Product(name='Coffee', price=4.99, stock_quantity=100, category_id=3, sku='COF001'),
        Product(name='Novel', price=12.99, stock_quantity=25, category_id=4, sku='NOV001')
    ]
    
    for product in products:
        db.session.add(product)
    
    # Create sample customers
    customers = [
        Customer(name='John Doe', email='john@example.com', phone='123-456-7890'),
        Customer(name='Jane Smith', email='jane@example.com', phone='098-765-4321')
    ]
    
    for customer in customers:
        db.session.add(customer)
    
    db.session.commit()