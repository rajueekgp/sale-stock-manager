from flask import Blueprint, request, jsonify
from database import db
from models import Product, Category, SaleItem, Sale, ProductBatch, Purchase, PurchaseItem, Return, ReturnItem
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, desc, asc

products_bp = Blueprint('products', __name__)

@products_bp.route('/products', methods=['GET'])
def get_products():
    """Get all products with pagination, search, and filters"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int) # Keep one per_page
        search = request.args.get('search', '')
        category_id = request.args.get('category_id', type=int)
        low_stock = request.args.get('low_stock', False, type=bool)
        out_of_stock = request.args.get('out_of_stock', False, type=bool)
        sort_by = request.args.get('sort_by', 'name')  # name, price, stock_quantity, created_at
        sort_order = request.args.get('sort_order', 'asc')  # asc, desc
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        
        query = Product.query.filter(Product.is_active == True)
        
        # Search filter
        if search:
            query = query.filter(
                or_(
                    Product.name.contains(search),
                    Product.sku.contains(search),
                    Product.barcode.contains(search),
                    Product.description.contains(search)
                )
            )
        
        # Category filter
        if category_id:
            query = query.filter(Product.category_id == category_id)

        # Stock filters
        if low_stock:
            query = query.filter(
                and_(
                    Product.stock_quantity <= Product.min_stock_level,
                    Product.stock_quantity > 0
                )
            )
        
        if out_of_stock:
            query = query.filter(Product.stock_quantity == 0)
        
        # Price filters
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        
        # Sorting
        if sort_by == 'price':
            order_column = Product.price
        elif sort_by == 'stock_quantity':
            order_column = Product.stock_quantity
        elif sort_by == 'created_at':
            order_column = Product.created_at
        else:
            order_column = Product.name
        
        if sort_order == 'desc':
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))
        
        products = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [product.to_dict() for product in products.items],
            'pagination': {
                'page': page,
                'pages': products.pages,
                'per_page': per_page,
                'total': products.total
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/products/<int:product_id>/ledger', methods=['GET'])
def get_product_ledger(product_id):
    """Get all transactions (sales, purchases, returns) for a specific product."""
    try:
        product = Product.query.get_or_404(product_id)

        # Get sales for the product
        sales = db.session.query(Sale).join(SaleItem).filter(SaleItem.product_id == product_id).order_by(Sale.created_at.desc()).all()

        # Get purchases for the product
        purchases = db.session.query(Purchase).join(PurchaseItem).filter(PurchaseItem.product_id == product_id).order_by(Purchase.created_at.desc()).all()

        # Get returns for the product
        returns = db.session.query(Return).join(ReturnItem).filter(ReturnItem.product_id == product_id).order_by(Return.created_at.desc()).all()

        return jsonify({
            'success': True,
            'data': {
                'product': product.to_dict(),
                'sales': [sale.to_dict() for sale in sales],
                'purchases': [purchase.to_dict() for purchase in purchases],
                'returns': [ret.to_dict() for ret in returns]
            }
        })
    except Exception as e:
        if '404 Not Found' in str(e):
             return jsonify({'success': False, 'error': 'Product not found'}), 404
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get single product with detailed information"""
    try:
        product = Product.query.get_or_404(product_id)
        product_dict = product.to_dict()
        
        # Get sales statistics
        total_sold_result = db.session.query(func.sum(SaleItem.quantity)).filter(
            SaleItem.product_id == product_id
        ).first()
        total_sold = total_sold_result[0] if total_sold_result and total_sold_result[0] is not None else 0
        
        total_revenue_result = db.session.query(func.sum(SaleItem.total_price)).filter(SaleItem.product_id == product_id).first()
        total_revenue = total_revenue_result[0] if total_revenue_result and total_revenue_result[0] is not None else 0
        
        # Get recent sales (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_sales = db.session.query(func.sum(SaleItem.quantity)).join(Sale).filter(
            SaleItem.product_id == product_id,
            Sale.created_at >= thirty_days_ago
        ).scalar() or 0
        
        # Placeholder for purchase history as PurchaseItem is not imported here
        total_purchased = 0 
        
        # Calculate velocity (sales per day over last 30 days)
        velocity = recent_sales / 30 if recent_sales > 0 else 0
        
        # Estimate days until out of stock
        days_until_out = product.stock_quantity / velocity if velocity > 0 else float('inf')
        
        product_dict.update({
            'statistics': {
                'total_sold': total_sold,
                'total_revenue': total_revenue,
                'total_purchased': total_purchased,
                'recent_sales_30_days': recent_sales,
                'sales_velocity': velocity,
                'days_until_out_of_stock': days_until_out if days_until_out != float('inf') else None,
                'profit_per_unit': product.price - product.cost_price,
                'profit_margin': ((product.price - product.cost_price) / product.price * 100) if product.price > 0 else 0
            }
        })
        
        return jsonify({
            'success': True,
            'data': product_dict
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/products', methods=['POST'])
def create_product():
    """Create a new product"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'price', 'sku', 'category_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'{field} is required'
                }), 400
        
        # Check if SKU already exists
        existing_product = Product.query.filter_by(sku=data['sku']).first()
        if existing_product:
            return jsonify({
                'success': False,
                'error': 'Product with this SKU already exists'
            }), 400
        
        # Check if barcode already exists (if provided)
        if data.get('barcode') and data['barcode']:
            existing_barcode = Product.query.filter_by(barcode=data['barcode']).first()
            if existing_barcode:
                return jsonify({'success': False, 'error': 'Product with this barcode already exists'}), 400
        
        # Validate category exists
        category = Category.query.get(data['category_id'])
        if not category:
            return jsonify({
                'success': False,
                'error': 'Category not found'
            }), 400
        
        # Validate numeric fields
        if data['price'] < 0:
            return jsonify({
                'success': False,
                'error': 'Price cannot be negative'
            }), 400
        
        if data.get('cost_price', 0) < 0:
            return jsonify({
                'success': False,
                'error': 'Cost price cannot be negative'
            }), 400
        
        product = Product(
            name=data['name'].strip(),
            description=data.get('description', '').strip(),
            price=float(data['price']),
            cost_price=float(data.get('cost_price', 0)),
            stock_quantity=int(data.get('stock_quantity', 0)),
            min_stock_level=int(data.get('min_stock_level', 5)),
            sku=data['sku'].strip().upper(),
            barcode=data.get('barcode', '').strip(),
            category_id=int(data['category_id']),
            batch_management_enabled=data.get('batch_management_enabled', False),
            gst_rate=data.get('gst_rate', 0.0)
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': product.to_dict(),
            'message': 'Product created successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update product information"""
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        # Check if SKU already exists (excluding current product)
        if 'sku' in data and data['sku'] != product.sku:
            existing_product = Product.query.filter_by(sku=data['sku']).first()
            if existing_product:
                return jsonify({
                    'success': False,
                    'error': 'Product with this SKU already exists'
                }), 400
        
        # Check if barcode already exists (excluding current product)
        if 'barcode' in data and data['barcode'] and data['barcode'] != product.barcode:
            existing_barcode = Product.query.filter_by(barcode=data['barcode']).first()
            if existing_barcode:
                return jsonify({
                    'success': False,
                    'error': 'Product with this barcode already exists'
                }), 400
        
        # Validate category exists (if being updated)
        if 'category_id' in data:
            category = Category.query.get(data['category_id'])
            if not category:
                return jsonify({
                    'success': False,
                    'error': 'Category not found'
                }), 400
        
        # Validate numeric fields
        if 'price' in data and data['price'] < 0:
            return jsonify({
                'success': False,
                'error': 'Price cannot be negative'
            }), 400
        
        if 'cost_price' in data and data['cost_price'] < 0:
            return jsonify({
                'success': False,
                'error': 'Cost price cannot be negative'
            }), 400
        
        # Update fields
        updatable_fields = [
            'name', 'description', 'price', 'cost_price', 'stock_quantity',
            'min_stock_level', 'sku', 'barcode', 'category_id', 'is_active',
            'batch_management_enabled', 'gst_rate'
        ]
        
        for field in updatable_fields:
            if field in data:
                if field in ['name', 'description', 'sku', 'barcode']:
                    setattr(product, field, str(data[field]).strip())
                elif field in ['price', 'cost_price']:
                    setattr(product, field, float(data[field]))
                elif field in ['stock_quantity', 'min_stock_level', 'category_id']:
                    setattr(product, field, int(data[field]))
                else:
                    setattr(product, field, data[field])
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': product.to_dict(),
            'message': 'Product updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Soft delete product (mark as inactive)"""
    try:
        product = Product.query.get_or_404(product_id)
        
        # Check if product has sales history
        sales_count = SaleItem.query.filter_by(product_id=product_id).count()
        if sales_count > 0:
            # Soft delete - mark as inactive
            product.is_active = False
            product.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Product marked as inactive (has {sales_count} sales records)'
            })
        else:
            # Hard delete if no sales history
            db.session.delete(product)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Product deleted successfully'
            })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/products/<int:product_id>/restore', methods=['POST'])
def restore_product(product_id):
    """Restore inactive product"""
    try:
        product = Product.query.get_or_404(product_id)
        
        if product.is_active:
            return jsonify({
                'success': False,
                'error': 'Product is already active'
            }), 400
        
        product.is_active = True
        product.is_active = False
        product.updated_at = datetime.utcnow()
        product.is_active = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': product.to_dict(),
            'message': 'Product restored successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/products/<int:product_id>/batches', methods=['POST'])
def create_product_batch(product_id):
    """Create a new batch for a product"""
    try:
        product = Product.query.get_or_404(product_id)
        if not product.batch_management_enabled:
            return jsonify({'success': False, 'error': 'Batch management is not enabled for this product.'}), 400

        data = request.get_json()
        batch_number = data.get('batch_number')
        if not batch_number:
            return jsonify({'success': False, 'error': 'Batch number is required.'}), 400

        # Check if batch number already exists for this product
        existing_batch = ProductBatch.query.filter_by(product_id=product_id, batch_number=batch_number).first()
        if existing_batch:
            return jsonify({'success': False, 'error': f'Batch "{batch_number}" already exists for this product.'}), 400

        # Convert empty strings for numeric fields to None
        purchase_price = data.get('purchase_price')
        sale_price = data.get('sale_price')
        gst_rate = data.get('gst_rate')

        new_batch = ProductBatch(
            product_id=product_id,
            batch_number=batch_number,
            barcode=data.get('barcode'),
            purchase_price=float(purchase_price) if purchase_price else None,
            sale_price=float(sale_price) if sale_price else None,
            gst_rate=float(gst_rate) if gst_rate else None,
            expiry_date=datetime.fromisoformat(data['expiry_date']) if data.get('expiry_date') else None
        )

        db.session.add(new_batch)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': new_batch.to_dict(),
            'message': 'Batch created successfully.'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/products/barcode/<barcode>', methods=['GET'])
def get_product_by_barcode(barcode):
    """Get product by barcode (for barcode scanning)"""
    try:
        product = Product.query.filter_by(barcode=barcode, is_active=True).first()
        
        if not product:
            return jsonify({
                'success': False,
                'error': 'Product not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': product.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/products/analytics', methods=['GET'])
def get_product_analytics():
    """Get product analytics and insights"""
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total products
        total_products = Product.query.filter_by(is_active=True).count()
        
        # Low stock products
        low_stock_products = Product.query.filter(
            Product.stock_quantity <= Product.min_stock_level,
            Product.stock_quantity > 0,
            Product.is_active == True
        ).count()
        
        # Out of stock products
        out_of_stock_products = Product.query.filter(
            Product.stock_quantity == 0,
            Product.is_active == True
        ).count()
        
        # Total inventory value
        inventory_value = db.session.query(
            func.sum(Product.stock_quantity * Product.cost_price)
        ).filter(Product.is_active == True).scalar() or 0
        
        # Top selling products
        top_selling = db.session.query(
            Product.name,
            Product.sku,
            func.sum(SaleItem.quantity).label('total_sold'),
            func.sum(SaleItem.total_price).label('total_revenue')
        ).join(SaleItem).join(Sale).filter(
            Sale.created_at >= start_date,
            Product.is_active == True
        ).group_by(Product.id).order_by(desc('total_sold')).limit(10).all()
        
        # Most profitable products
        most_profitable = db.session.query(
            Product.name,
            Product.sku,
            Product.price,
            Product.cost_price,
            func.sum(SaleItem.quantity).label('total_sold'),
            func.sum((Product.price - Product.cost_price) * SaleItem.quantity).label('total_profit')
        ).join(SaleItem).join(Sale).filter(
            Sale.created_at >= start_date,
            Product.is_active == True
        ).group_by(Product.id).order_by(desc('total_profit')).limit(10).all()
        
        # Category performance
        category_performance = db.session.query(
            Category.name,
            func.count(Product.id).label('product_count'),
            func.sum(SaleItem.quantity).label('total_sold'),
            func.sum(SaleItem.total_price).label('total_revenue')
        ).join(Product).join(SaleItem).join(Sale).filter(
            Sale.created_at >= start_date,
            Product.is_active == True
        ).group_by(Category.id).order_by(desc('total_revenue')).all()
        
        # Slow moving products (products with low sales)
        slow_moving = db.session.query(
            Product.name,
            Product.sku,
            Product.stock_quantity,
            func.coalesce(func.sum(SaleItem.quantity), 0).label('total_sold')
        ).outerjoin(SaleItem).outerjoin(Sale, and_(
            SaleItem.sale_id == Sale.id,
            Sale.created_at >= start_date
        )).filter(
            Product.is_active == True
        ).group_by(Product.id).having(
            func.coalesce(func.sum(SaleItem.quantity), 0) <= 5
        ).order_by('total_sold').limit(10).all()
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total_products': total_products,
                    'low_stock_products': low_stock_products,
                    'out_of_stock_products': out_of_stock_products,
                    'inventory_value': inventory_value,
                    'stock_health_percentage': ((total_products - low_stock_products - out_of_stock_products) / total_products * 100) if total_products > 0 else 0
                },
                'top_selling': [
                    {
                        'name': p.name,
                        'sku': p.sku,
                        'quantity_sold': p.total_sold,
                        'revenue': p.total_revenue
                    } for p in top_selling
                ],
                'most_profitable': [
                    {
                        'name': p.name,
                        'sku': p.sku,
                        'price': p.price,
                        'cost_price': p.cost_price,
                        'quantity_sold': p.total_sold,
                        'total_profit': p.total_profit,
                        'profit_margin': ((p.price - p.cost_price) / p.price * 100) if p.price > 0 else 0
                    } for p in most_profitable
                ],
                'category_performance': [
                    {
                        'category': cp.name,
                        'product_count': cp.product_count,
                        'quantity_sold': cp.total_sold or 0,
                        'revenue': cp.total_revenue or 0
                    } for cp in category_performance
                ],
                'slow_moving': [
                    {
                        'name': sm.name,
                        'sku': sm.sku,
                        'stock_quantity': sm.stock_quantity,
                        'quantity_sold': sm.total_sold
                    } for sm in slow_moving
                ],
                'period_days': days
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/products/bulk-update', methods=['POST'])
def bulk_update_products():
    """Bulk update multiple products"""
    try:
        data = request.get_json()
        updates = data.get('updates', [])
        if not updates:
            return jsonify({
                'success': False,
                'error': 'No updates provided'
            }), 400
        
        updated_products = []
        errors = []
        
        for i, update in enumerate(updates):
            try:
                product_id = update.get('product_id')
                if not product_id:
                    errors.append(f'Row {i+1}: product_id is required')
                    continue
                
                product = Product.query.get(product_id)
                if not product:
                    errors.append(f'Row {i+1}: Product with ID {product_id} not found')
                    continue
                
                # Update allowed fields
                updatable_fields = ['price', 'cost_price', 'stock_quantity', 'min_stock_level', 'is_active']
                
                for field in updatable_fields:
                    if field in update:
                        if field in ['price', 'cost_price']:
                            if update[field] < 0:
                                errors.append(f'Row {i+1}: {field} cannot be negative')
                                continue
                            setattr(product, field, float(update[field]))
                        elif field in ['stock_quantity', 'min_stock_level']:
                            setattr(product, field, int(update[field]))
                        else:
                            setattr(product, field, update[field])
                
                product.updated_at = datetime.utcnow()
                updated_products.append(product.to_dict())
                
            except Exception as e:
                errors.append(f'Row {i+1}: {str(e)}')
        
        if errors:
            db.session.rollback()
            return jsonify({
                'success': False,
                'errors': errors
            }), 400
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': updated_products,
            'message': f'Successfully updated {len(updated_products)} products'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/products/bulk-import', methods=['POST'])
def bulk_import_products():
    """Bulk import products from JSON data"""
    try:
        data = request.get_json()
        products_data = data.get('products', [])
        
        if not products_data:
            return jsonify({
                'success': False,
                'error': 'No product data provided'
            }), 400
        
        created_products = []
        errors = []
        
        for i, product_data in enumerate(products_data):
            try:
                # Validate required fields
                required_fields = ['name', 'price', 'sku', 'category_id']
                for field in required_fields:
                    if not product_data.get(field):
                        errors.append(f'Row {i+1}: {field} is required')
                        continue
                
                # Check for duplicate SKU
                existing_product = Product.query.filter_by(sku=product_data['sku']).first()
                if existing_product:
                    errors.append(f'Row {i+1}: SKU {product_data["sku"]} already exists')
                    continue
                
                # Validate category
                category = Category.query.get(product_data['category_id'])
                if not category:
                    errors.append(f'Row {i+1}: Category {product_data["category_id"]} not found')
                    continue
                
                product = Product(
                    name=product_data['name'].strip(),
                    description=product_data.get('description', '').strip(),
                    price=float(product_data['price']),
                    cost_price=float(product_data.get('cost_price', 0)),
                    stock_quantity=int(product_data.get('stock_quantity', 0)),
                    min_stock_level=int(product_data.get('min_stock_level', 5)),
                    sku=product_data['sku'].strip().upper(),
                    barcode=product_data.get('barcode', '').strip(),
                    category_id=int(product_data['category_id']),
                    is_active=product_data.get('is_active', True)
                )
                
                db.session.add(product)
                created_products.append(product_data['name'])
                
            except Exception as e:
                errors.append(f'Row {i+1}: {str(e)}')
        
        if errors:
            db.session.rollback()
            return jsonify({
                'success': False,
                'errors': errors
            }), 400
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'created_count': len(created_products),
                'created_products': created_products
            },
            'message': f'Successfully imported {len(created_products)} products'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/products/<int:product_id>/sales-history', methods=['GET'])
def get_product_sales_history(product_id):
    """Get sales history for a specific product"""
    try:
        product = Product.query.get_or_404(product_id)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = db.session.query(
            Sale.id,
            Sale.sale_number,
            Sale.created_at,
            Sale.customer_id,
            Customer.name.label('customer_name'),
            SaleItem.quantity,
            SaleItem.unit_price,
            SaleItem.total_price
        ).join(SaleItem).join(Sale).outerjoin(Customer).filter(
            SaleItem.product_id == product_id
        )
        
        if start_date:
            query = query.filter(Sale.created_at >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(Sale.created_at <= datetime.fromisoformat(end_date))
        
        sales = query.order_by(desc(Sale.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        sales_history = [
            {
                'sale_id': sale.id,
                'sale_number': sale.sale_number,
                'date': sale.created_at.isoformat(),
                'customer_name': sale.customer_name or 'Walk-in Customer',
                'quantity': sale.quantity,
                'unit_price': sale.unit_price,
                'total_price': sale.total_price
            } for sale in sales.items
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'product': product.to_dict(),
                'sales_history': sales_history
            },
            'pagination': {
                'page': page,
                'pages': sales.pages,
                'per_page': per_page,
                'total': sales.total
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/products/<int:product_id>/price-history', methods=['GET'])
def get_product_price_history(product_id):
    """Get price change history for a product (placeholder - would need price history table)"""
    try:
        product = Product.query.get_or_404(product_id)
        
        # This is a simplified version - in a real system, you'd have a price_history table
        # For now, we'll return current price info
        price_history = [
            {
                'date': product.updated_at.isoformat() if product.updated_at else product.created_at.isoformat(),
                'price': product.price,
                'cost_price': product.cost_price,
                'changed_by': 'System',  # Would be actual user in real implementation
                'reason': 'Current price'
            }
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'product': product.to_dict(),
                'price_history': price_history
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/products/low-stock-alerts', methods=['GET'])
def get_low_stock_alerts():
    """Get products that need restocking"""
    try:
        threshold_multiplier = request.args.get('threshold_multiplier', 1.0, type=float)
        
        products = Product.query.filter(
            Product.stock_quantity <= (Product.min_stock_level * threshold_multiplier),
            Product.is_active == True
        ).order_by(Product.stock_quantity.asc()).all()
        
        alerts = []
        for product in products:
            # Calculate urgency
            if product.stock_quantity == 0:
                urgency = 'critical'
            elif product.stock_quantity <= product.min_stock_level * 0.5:
                urgency = 'high'
            else:
                urgency = 'medium'
            
            alerts.append({
                'product': product.to_dict(),
                'urgency': urgency,
                'suggested_order_quantity': max(product.min_stock_level * 2 - product.stock_quantity, product.min_stock_level)
            })
        
        return jsonify({
            'success': True,
            'data': alerts,
            'summary': {
                'total_alerts': len(alerts),
                'critical': len([a for a in alerts if a['urgency'] == 'critical']),
                'high': len([a for a in alerts if a['urgency'] == 'high']),
                'medium': len([a for a in alerts if a['urgency'] == 'medium'])
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/products/duplicate-check', methods=['GET'])
def check_duplicate_products():
    """Find potential duplicate products based on name similarity"""
    try:
        # Find products with similar names (basic implementation)
        products = Product.query.filter_by(is_active=True).all()
        
        potential_duplicates = []
        processed_names = set()
        
        for product in products:
            if product.name.lower() in processed_names:
                continue
            
            # Find products with similar names
            similar_products = [
                p for p in products 
                if p.id != product.id and 
                p.name.lower().strip() == product.name.lower().strip()
            ]
            
            if similar_products:
                duplicate_group = {
                    'similar_name': product.name,
                    'products': [product.to_dict()] + [p.to_dict() for p in similar_products]
                }
                potential_duplicates.append(duplicate_group)
                processed_names.add(product.name.lower())
        
        return jsonify({
            'success': True,
            'data': potential_duplicates,
            'count': len(potential_duplicates)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/products/export', methods=['POST'])
def export_products():
    """Export product data (placeholder for CSV/Excel export)"""
    try:
        data = request.get_json()
        format_type = data.get('format', 'json')  # json, csv, excel
        include_inactive = data.get('include_inactive', False)
        include_analytics = data.get('include_analytics', False)
        
        query = Product.query
        if not include_inactive:
            query = query.filter(Product.is_active == True)
        
        products = query.all()
        
        export_data = []
        for product in products:
            product_data = product.to_dict()
            
            if include_analytics:
                # Add analytics data
                total_sold = db.session.query(func.sum(SaleItem.quantity)).filter(
                    SaleItem.product_id == product.id
                ).scalar() or 0
                
                total_revenue = db.session.query(func.sum(SaleItem.total_price)).filter(
                    SaleItem.product_id == product.id
                ).scalar() or 0
                
                product_data.update({
                    'total_sold': total_sold,
                    'total_revenue': total_revenue
                })
            
            export_data.append(product_data)
        
        return jsonify({
            'success': True,
            'data': export_data,
            'metadata': {
                'total_products': len(export_data),
                'export_format': format_type,
                'include_inactive': include_inactive,
                'include_analytics': include_analytics,
                'exported_at': datetime.utcnow().isoformat()
            },
            'message': f'Product data exported successfully ({len(export_data)} products)'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
