from database import db
from datetime import datetime
from sqlalchemy import func

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() + "Z",
            'product_count': len(self.products)
        }

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    cost_price = db.Column(db.Float, default=0.0)
    stock_quantity = db.Column(db.Integer, default=0)
    min_stock_level = db.Column(db.Integer, default=5)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    barcode = db.Column(db.String(100))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    batch_management_enabled = db.Column(db.Boolean, default=False, nullable=False)
    gst_rate = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        stock = self.stock_quantity
        # If batch management is on, the true stock is the sum of batch stocks.
        if self.batch_management_enabled:
            stock = db.session.query(func.sum(ProductBatch.stock_quantity)).filter_by(product_id=self.id).scalar() or 0

        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'cost_price': self.cost_price,
            'stock_quantity': stock,
            'min_stock_level': self.min_stock_level,
            'sku': self.sku,
            'barcode': self.barcode,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'is_active': self.is_active,
            'is_low_stock': stock <= self.min_stock_level,
            'created_at': self.created_at.isoformat() + "Z",
            'updated_at': self.updated_at.isoformat() + "Z",
            'batch_management_enabled': self.batch_management_enabled,
            'gst_rate': self.gst_rate,
            'batches': [b.to_dict() for b in self.batches] if self.batch_management_enabled else []
        }

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    gst_number = db.Column(db.String(15), unique=True, nullable=True)
    opening_balance = db.Column(db.Float, default=0.0)
    # store_credit = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sales = db.relationship('Sale', backref='customer', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'gst_number': self.gst_number,
            'opening_balance': self.opening_balance,
            # 'store_credit': self.store_credit,
            'created_at': self.created_at.isoformat() + "Z",
            'total_purchases': sum(sale.total_amount for sale in self.sales)
        }

class Sale(db.Model):
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    sale_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    subtotal = db.Column(db.Float, nullable=False)
    tax_amount = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), default='cash')
    status = db.Column(db.String(20), default='completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'sale_number': self.sale_number,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else 'Walk-in Customer',
            'subtotal': self.subtotal,
            'tax_amount': self.tax_amount,
            'discount_amount': self.discount_amount,
            'total_amount': self.total_amount,
            'payment_method': self.payment_method,
            'status': self.status,
            'created_at': self.created_at.isoformat() + "Z",
            'items': [item.to_dict() for item in self.items]
        }

class SaleItem(db.Model):
    __tablename__ = 'sale_items'
    
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('product_batches.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    
    # Relationships
    product = db.relationship('Product', backref='sale_items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'sale_id': self.sale_id,
            'product_id': self.product_id,
            'batch_id': self.batch_id,
            'product_name': self.product.name if self.product else None,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_price': self.total_price
        }

class Purchase(db.Model):
    __tablename__ = 'purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    purchase_number = db.Column(db.String(50), unique=True, nullable=False)
    supplier_name = db.Column(db.String(200), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    items = db.relationship('PurchaseItem', backref='purchase', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'purchase_number': self.purchase_number,
            'supplier_name': self.supplier_name,
            'total_amount': self.total_amount,
            'status': self.status,
            'created_at': self.created_at.isoformat() + "Z",
            'items': [item.to_dict() for item in self.items]
        }

class PurchaseItem(db.Model):
    __tablename__ = 'purchase_items'
    
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('product_batches.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_cost = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    
    # Relationships
    product = db.relationship('Product', backref='purchase_items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'purchase_id': self.purchase_id,
            'product_id': self.product_id,
            'batch_id': self.batch_id,
            'product_name': self.product.name if self.product else None,
            'quantity': self.quantity,
            'unit_cost': self.unit_cost,
            'total_cost': self.total_cost
        }

class ProductBatch(db.Model):
    __tablename__ = 'product_batches'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    batch_number = db.Column(db.String(100), nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    
    # Optional overrides from the main product
    barcode = db.Column(db.String(100))
    purchase_price = db.Column(db.Float)
    sale_price = db.Column(db.Float)
    gst_rate = db.Column(db.Float)
    
    expiry_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product', backref=db.backref('batches', lazy=True, cascade='all, delete-orphan'))
    
    __table_args__ = (db.UniqueConstraint('product_id', 'batch_number', name='_product_batch_uc'),)

    def to_dict(self):
        return {
            'id': self.id, 'product_id': self.product_id, 'batch_number': self.batch_number,
            'stock_quantity': self.stock_quantity, 'barcode': self.barcode,
            'purchase_price': self.purchase_price, 'sale_price': self.sale_price,
            'gst_rate': self.gst_rate, 'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'created_at': self.created_at.isoformat() + "Z",
        }

class Return(db.Model):
    __tablename__ = 'returns'
    
    id = db.Column(db.Integer, primary_key=True)
    return_number = db.Column(db.String(50), unique=True, nullable=False)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    total_refund_amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='Completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    items = db.relationship('ReturnItem', backref='return_record', lazy=True, cascade='all, delete-orphan')
    sale = db.relationship('Sale', backref='returns')
    
    def to_dict(self):
        return {
            'id': self.id,
            'return_number': self.return_number,
            'sale_id': self.sale_id,
            'sale_number': self.sale.sale_number if self.sale else None,
            'customer_id': self.customer_id,
            'customer_name': self.sale.customer.name if self.sale and self.sale.customer else 'Walk-in Customer',
            'total_refund_amount': self.total_refund_amount,
            'reason': self.reason,
            'status': self.status,
            'created_at': self.created_at.isoformat() + "Z",
            'items': [item.to_dict() for item in self.items]
        }

class ReturnItem(db.Model):
    __tablename__ = 'return_items'
    
    id = db.Column(db.Integer, primary_key=True)
    return_id = db.Column(db.Integer, db.ForeignKey('returns.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('product_batches.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    
    # Relationships
    product = db.relationship('Product', backref='return_items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'return_id': self.return_id,
            'product_id': self.product_id,
            'batch_id': self.batch_id,
            'product_name': self.product.name if self.product else None,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_price': self.total_price
        }

class CreditNote(db.Model):
    __tablename__ = 'credit_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    credit_note_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    return_id = db.Column(db.Integer, db.ForeignKey('returns.id'))
    initial_amount = db.Column(db.Float, nullable=False)
    remaining_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Open') # Open, Applied, Voided
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Relationships
    customer = db.relationship('Customer', backref='credit_notes')
    return_record = db.relationship('Return', backref='credit_note')

    def to_dict(self):
        return {
            'id': self.id,
            'credit_note_number': self.credit_note_number,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else None,
            'return_id': self.return_id,
            'initial_amount': self.initial_amount,
            'remaining_amount': self.remaining_amount,
            'status': self.status,
            'created_at': self.created_at.isoformat() + "Z",
            'expires_at': self.expires_at.isoformat() + "Z" if self.expires_at else None
        }