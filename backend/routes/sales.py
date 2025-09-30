from flask import Blueprint, request, jsonify
from database import db
from models import Sale, SaleItem, Product, Customer, Category, ProductBatch
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, desc, asc
from collections import defaultdict
import uuid

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/sales', methods=['GET'])
def get_sales():
    """Get all sales with pagination and filters"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        customer_id = request.args.get('customer_id', type=int)
        payment_method = request.args.get('payment_method')
        status = request.args.get('status')
        min_amount = request.args.get('min_amount', type=float)
        max_amount = request.args.get('max_amount', type=float)
        sort_by = request.args.get('sort_by', 'created_at')  # created_at, total_amount, sale_number
        sort_order = request.args.get('sort_order', 'desc')  # asc, desc
        search = request.args.get('search', '')
        
        query = Sale.query
        
        # Search filter for sale number, customer name, or product name
        if search:
            sales_with_product_subquery = db.session.query(Sale.id).join(SaleItem).join(Product).filter(Product.name.contains(search)).subquery()
            
            query = query.join(Customer, Sale.customer_id == Customer.id, isouter=True).filter(
                or_(
                    Sale.sale_number.contains(search),
                    Customer.name.contains(search),
                    Sale.id.in_(sales_with_product_subquery)
                )
            )

        # Date filters
        if start_date:
            query = query.filter(Sale.created_at >= datetime.fromisoformat(start_date))
        if end_date:
            # To include the whole day, filter up to the end of that day
            end_date_dt = datetime.fromisoformat(end_date) + timedelta(days=1)
            query = query.filter(Sale.created_at < end_date_dt)
        
        # Other filters
        if customer_id:
            query = query.filter(Sale.customer_id == customer_id)
        if payment_method:
            query = query.filter(Sale.payment_method == payment_method)
        if status:
            query = query.filter(Sale.status == status)
        if min_amount:
            query = query.filter(Sale.total_amount >= min_amount)
        if max_amount:
            query = query.filter(Sale.total_amount <= max_amount)
        
        # Sorting
        if sort_by == 'total_amount':
            order_column = Sale.total_amount
        elif sort_by == 'sale_number':
            order_column = Sale.sale_number
        else:
            order_column = Sale.created_at
        
        if sort_order == 'asc':
            query = query.order_by(asc(order_column))
        else:
            query = query.order_by(desc(order_column))
        
        sales = query.distinct().paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Calculate summary statistics for current filter
        total_sales = query.count()
        total_revenue = db.session.query(func.sum(Sale.total_amount)).filter(
            *[condition for condition in [
                Sale.created_at >= datetime.fromisoformat(start_date) if start_date else None,
                Sale.created_at <= datetime.fromisoformat(end_date) if end_date else None,
                Sale.customer_id == customer_id if customer_id else None,
                Sale.payment_method == payment_method if payment_method else None,
                Sale.status == status if status else None,
                Sale.total_amount >= min_amount if min_amount is not None else None,
                Sale.total_amount <= max_amount if max_amount is not None else None,
                or_(
                    Sale.sale_number.contains(search),
                    Customer.name.contains(search),
                    Sale.id.in_(db.session.query(Sale.id).join(SaleItem).join(Product).filter(Product.name.contains(search)))
                ) if search else None
            ] if condition is not None]
        ).scalar() or 0
        
        return jsonify({
            'success': True,
            'data': [sale.to_dict() for sale in sales.items],
            'summary': {
                'total_sales': total_sales,
                'total_revenue': total_revenue,
                'average_sale_amount': total_revenue / total_sales if total_sales > 0 else 0
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

@sales_bp.route('/sales/<int:sale_id>', methods=['GET'])
def get_sale(sale_id):
    """Get single sale with detailed information"""
    try:
        sale = Sale.query.get_or_404(sale_id)
        sale_dict = sale.to_dict()
        
        # Add detailed item information
        detailed_items = []
        for item in sale.items:
            item_dict = item.to_dict()
            if item.product:
                item_dict['product_details'] = {
                    'name': item.product.name,
                    'sku': item.product.sku,
                    'category': item.product.category.name if item.product.category else None,
                    'current_price': item.product.price,
                    'current_stock': item.product.stock_quantity
                }
            detailed_items.append(item_dict)
        
        sale_dict['items'] = detailed_items
        
        return jsonify({
            'success': True,
            'data': sale_dict
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/sales', methods=['POST'])
def create_sale():
    """Create a new sale"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['items', 'subtotal', 'total_amount']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'{field} is required'
                }), 400
        
        if not data['items']:
            return jsonify({
                'success': False,
                'error': 'At least one item is required'
            }), 400
        
        # Validate stock availability
        for item_data in data['items']:
            if 'product_id' not in item_data or 'quantity' not in item_data:
                return jsonify({
                    'success': False,
                    'error': 'Each item must have product_id and quantity'
                }), 400
            
            product = Product.query.get(item_data['product_id'])
            if not product:
                return jsonify({
                    'success': False,
                    'error': f'Product with ID {item_data["product_id"]} not found'
                }), 400
            
            if not product.is_active:
                return jsonify({
                    'success': False,
                    'error': f'Product {product.name} is not active'
                }), 400
            
            if product.stock_quantity < item_data['quantity']:
                return jsonify({
                    'success': False,
                    'error': f'Insufficient stock for {product.name}. Available: {product.stock_quantity}, Requested: {item_data["quantity"]}'
                }), 400
        
        # Generate sale number
        sale_number = f"SALE-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Create sale
        sale = Sale(
            sale_number=sale_number,
            customer_id=data.get('customer_id'),
            subtotal=data['subtotal'],
            tax_amount=data.get('tax_amount', 0),
            discount_amount=data.get('discount_amount', 0),
            total_amount=data['total_amount'],
            payment_method=data.get('payment_method', 'cash'),
            status=data.get('status', 'completed')
        )
        
        db.session.add(sale)
        db.session.flush()  # Get the sale ID
        
        for item_data in data['items']:
            product = Product.query.get(item_data['product_id'])
            quantity = item_data['quantity']
            batch_id = None

            if product.batch_management_enabled:
                batch_id = item_data.get('batch_id')
                if not batch_id:
                    return jsonify({'success': False, 'error': f'Batch ID is required for product {product.name}'}), 400
                
                batch = ProductBatch.query.get(batch_id)
                if not batch or batch.product_id != product.id:
                    return jsonify({'success': False, 'error': f'Invalid batch ID {batch_id} for product {product.name}'}), 400
                
                unit_price = batch.sale_price if batch.sale_price is not None else product.price
                batch.stock_quantity -= quantity
            else:
                unit_price = item_data.get('unit_price', product.price)
                product.stock_quantity -= quantity

            total_price = unit_price * quantity
            
            sale_item = SaleItem(
                sale_id=sale.id, product_id=item_data['product_id'],
                quantity=quantity, unit_price=unit_price,
                total_price=total_price, batch_id=batch_id
            )
            db.session.add(sale_item)
            product.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': sale.to_dict(),
            'message': 'Sale created successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/sales/<int:sale_id>', methods=['PUT'])
def update_sale(sale_id):
    """Updates a recent sale. This will adjust stock and update sale details."""
    try:
        sale = Sale.query.get_or_404(sale_id)
        data = request.get_json()

        # Security check: only allow updates for recent sales
        time_since_creation = datetime.utcnow() - sale.created_at
        if time_since_creation > timedelta(hours=1, minutes=5): # 5 min grace period
             return jsonify({
                'success': False, 
                'error': 'Sale is too old to be updated directly. Please void and create a new sale.'
            }), 403

        # --- Stock Adjustment Logic ---
        old_items = {item.product_id: item.quantity for item in sale.items}
        new_items_data = data.get('items', [])
        new_items = {item['product_id']: item['quantity'] for item in new_items_data}
        
        all_product_ids = set(old_items.keys()) | set(new_items.keys())

        for product_id in all_product_ids:
            product = Product.query.get(product_id)
            if not product: continue
            
            old_qty = old_items.get(product_id, 0)
            new_qty = new_items.get(product_id, 0)
            stock_diff = old_qty - new_qty
            
            if stock_diff < 0 and product.stock_quantity < abs(stock_diff):
                 return jsonify({
                    'success': False, 
                    'error': f'Insufficient stock for {product.name}. Available: {product.stock_quantity}, needed: {abs(stock_diff)}'
                }), 400

            product.stock_quantity += stock_diff
            product.updated_at = datetime.utcnow()

        # --- Update Sale and SaleItems ---
        # Delete old items
        for item in list(sale.items):
            db.session.delete(item)
        db.session.flush()
        
        # Add new items
        for item_data in new_items_data:
            sale_item = SaleItem(
                sale_id=sale.id, 
                product_id=item_data['product_id'],
                quantity=item_data['quantity'], 
                unit_price=item_data['price'],
                total_price=item_data['price'] * item_data['quantity']
            )
            db.session.add(sale_item)

        # Update sale details
        sale.customer_id = data.get('customer_id')
        sale.subtotal = data['subtotal']
        sale.tax_amount = data.get('tax_amount', 0)
        sale.discount_amount = data.get('discount_amount', 0)
        sale.total_amount = data['total_amount']
        sale.payment_method = data.get('payment_method', sale.payment_method)

        db.session.commit()
        return jsonify({'success': True, 'data': sale.to_dict(), 'message': 'Sale updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/sales/<int:sale_id>/void', methods=['POST'])
def void_sale(sale_id):
    """Void a sale and restore stock"""
    try:
        sale = Sale.query.get_or_404(sale_id)
        
        if sale.status == 'voided':
            return jsonify({
                'success': False,
                'error': 'Sale is already voided'
            }), 400
        
        # Restore stock for all items
        for item in sale.items:
            if item.product:
                item.product.stock_quantity += item.quantity
                item.product.updated_at = datetime.utcnow()
        
        # Update sale status
        sale.status = 'voided'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': sale.to_dict(),
            'message': 'Sale voided successfully and stock restored'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/sales/<int:sale_id>/refund', methods=['POST'])
def refund_sale(sale_id):
    """Process a full or partial refund"""
    try:
        sale = Sale.query.get_or_404(sale_id)
        data = request.get_json()
        
        refund_amount = data.get('refund_amount', sale.total_amount)
        refund_items = data.get('refund_items', [])  # List of {product_id, quantity}
        reason = data.get('reason', '')
        
        if refund_amount > sale.total_amount:
            return jsonify({
                'success': False,
                'error': 'Refund amount cannot exceed sale total'
            }), 400
        
        # If specific items are being refunded, restore their stock
        if refund_items:
            for refund_item in refund_items:
                product_id = refund_item['product_id']
                refund_quantity = refund_item['quantity']
                
                # Find the original sale item
                sale_item = next((item for item in sale.items if item.product_id == product_id), None)
                if not sale_item:
                    return jsonify({
                        'success': False,
                        'error': f'Product {product_id} not found in original sale'
                    }), 400
                
                if refund_quantity > sale_item.quantity:
                    return jsonify({
                        'success': False,
                        'error': f'Cannot refund more than originally sold for product {product_id}'
                    }), 400
                
                # Restore stock
                if sale_item.product:
                    sale_item.product.stock_quantity += refund_quantity
                    sale_item.product.updated_at = datetime.utcnow()
        else:
            # Full refund - restore all stock
            for item in sale.items:
                if item.product:
                    item.product.stock_quantity += item.quantity
                    item.product.updated_at = datetime.utcnow()
        
        # Update sale status
        if refund_amount == sale.total_amount:
            sale.status = 'refunded'
        else:
            sale.status = 'partially_refunded'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'sale': sale.to_dict(),
                'refund_amount': refund_amount,
                'refund_items': refund_items,
                'reason': reason
            },
            'message': f'Refund of ${refund_amount:.2f} processed successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/sales/analytics', methods=['GET'])
def get_sales_analytics():
    """Get comprehensive sales analytics"""
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Basic metrics
        total_sales = Sale.query.filter(Sale.created_at >= start_date).count()
        total_revenue = db.session.query(func.sum(Sale.total_amount)).filter(
            Sale.created_at >= start_date
        ).scalar() or 0
        
        # Compare with previous period
        prev_start = start_date - timedelta(days=days)
        prev_sales = Sale.query.filter(
            Sale.created_at >= prev_start,
            Sale.created_at < start_date
        ).count()
        prev_revenue = db.session.query(func.sum(Sale.total_amount)).filter(
            Sale.created_at >= prev_start,
            Sale.created_at < start_date
        ).scalar() or 0
        
        # Growth calculations
        sales_growth = ((total_sales - prev_sales) / prev_sales * 100) if prev_sales > 0 else 0
        revenue_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        
        # Daily sales trend
        daily_sales = db.session.query(
            func.date(Sale.created_at).label('date'),
            func.count(Sale.id).label('sales_count'),
            func.sum(Sale.total_amount).label('revenue')
        ).filter(
            Sale.created_at >= start_date
        ).group_by(func.date(Sale.created_at)).order_by('date').all()
        
        # Payment method breakdown
        payment_methods = db.session.query(
            Sale.payment_method,
            func.count(Sale.id).label('count'),
            func.sum(Sale.total_amount).label('total')
        ).filter(
            Sale.created_at >= start_date
        ).group_by(Sale.payment_method).all()
        
        # Hourly sales pattern
        hourly_sales = db.session.query(
            func.extract('hour', Sale.created_at).label('hour'),
            func.count(Sale.id).label('sales_count'),
            func.sum(Sale.total_amount).label('revenue')
        ).filter(
            Sale.created_at >= start_date
        ).group_by(func.extract('hour', Sale.created_at)).order_by('hour').all()
        
        # Top selling products
        top_products = db.session.query(
            Product.name,
            Product.sku,
            func.sum(SaleItem.quantity).label('total_sold'),
            func.sum(SaleItem.total_price).label('total_revenue')
        ).join(SaleItem).join(Sale).filter(
            Sale.created_at >= start_date
        ).group_by(Product.id).order_by(desc('total_sold')).limit(10).all()
        
        # Average order value trend
        aov_trend = []
        for i in range(days):
            day = start_date + timedelta(days=i)
            day_sales = Sale.query.filter(
                func.date(Sale.created_at) == day.date()
            ).all()
            
            if day_sales:
                day_revenue = sum(sale.total_amount for sale in day_sales)
                aov = day_revenue / len(day_sales)
            else:
                aov = 0
            
            aov_trend.append({
                'date': day.strftime('%Y-%m-%d'),
                'average_order_value': aov
            })
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total_sales': total_sales,
                    'total_revenue': total_revenue,
                    'average_order_value': total_revenue / total_sales if total_sales > 0 else 0,
                    'sales_growth': sales_growth,
                    'revenue_growth': revenue_growth
                },
                'daily_trend': [
                    {
                        'date': ds.date.strftime('%Y-%m-%d'),
                        'sales_count': ds.sales_count,
                        'revenue': ds.revenue
                    } for ds in daily_sales
                ],
                'payment_methods': [
                    {
                        'method': pm.payment_method,
                        'count': pm.count,
                        'total': pm.total,
                        'percentage': (pm.total / total_revenue * 100) if total_revenue > 0 else 0
                    } for pm in payment_methods
                ],
                'hourly_pattern': [
                    {
                        'hour': int(hs.hour),
                        'sales_count': hs.sales_count,
                        'revenue': hs.revenue
                    } for hs in hourly_sales
                ],
                'top_products': [
                    {
                        'name': tp.name,
                        'sku': tp.sku,
                        'quantity_sold': tp.total_sold,
                        'revenue': tp.total_revenue
                    } for tp in top_products
                ],
                'aov_trend': aov_trend,
                'period_days': days
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/sales/summary', methods=['GET'])
def get_sales_summary():
    """Get sales summary for different time periods"""
    try:
        # Today
        today = datetime.utcnow().date()
        today_sales = Sale.query.filter(func.date(Sale.created_at) == today).all()
        today_revenue = sum(sale.total_amount for sale in today_sales)
        
        # This week
        week_start = today - timedelta(days=today.weekday())
        week_sales = Sale.query.filter(Sale.created_at >= week_start).all()
        week_revenue = sum(sale.total_amount for sale in week_sales)
        
        # This month
        month_start = today.replace(day=1)
        month_sales = Sale.query.filter(Sale.created_at >= month_start).all()
        month_revenue = sum(sale.total_amount for sale in month_sales)
        
        # This year
        year_start = today.replace(month=1, day=1)
        year_sales = Sale.query.filter(Sale.created_at >= year_start).all()
        year_revenue = sum(sale.total_amount for sale in year_sales)
        
        return jsonify({
            'success': True,
            'data': {
                'today': {
                    'sales_count': len(today_sales),
                    'revenue': today_revenue,
                    'average_order_value': today_revenue / len(today_sales) if today_sales else 0
                },
                'this_week': {
                    'sales_count': len(week_sales),
                    'revenue': week_revenue,
                    'average_order_value': week_revenue / len(week_sales) if week_sales else 0
                },
                'this_month': {
                    'sales_count': len(month_sales),
                    'revenue': month_revenue,
                    'average_order_value': month_revenue / len(month_sales) if month_sales else 0
                },
                'this_year': {
                    'sales_count': len(year_sales),
                    'revenue': year_revenue,
                    'average_order_value': year_revenue / len(year_sales) if year_sales else 0
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/sales/receipt/<int:sale_id>', methods=['GET'])
def get_receipt(sale_id):
    """Generate receipt data for a sale"""
    try:
        sale = Sale.query.get_or_404(sale_id)
        
        receipt_data = {
            'sale_number': sale.sale_number,
            'date': sale.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'customer': {
                'name': sale.customer.name if sale.customer else 'Walk-in Customer',
                'email': sale.customer.email if sale.customer else None,
                'phone': sale.customer.phone if sale.customer else None
            },
            'items': [
                {
                    'product_name': item.product.name if item.product else 'Unknown Product',
                    'sku': item.product.sku if item.product else '',
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'total_price': item.total_price
                } for item in sale.items
            ],
            'subtotal': sale.subtotal,
            'tax_amount': sale.tax_amount,
            'discount_amount': sale.discount_amount,
            'total_amount': sale.total_amount,
            'payment_method': sale.payment_method,
            'status': sale.status
        }
        
        return jsonify({
            'success': True,
            'data': receipt_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/sales/search', methods=['GET'])
def search_sales():
    """Search sales by sale number or customer name"""
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 10, type=int)
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        # Search by sale number or customer name
        sales = db.session.query(Sale).join(Customer, Sale.customer_id == Customer.id, isouter=True).filter(
            or_(
                Sale.sale_number.contains(query),
                Customer.name.contains(query)
            )
        ).limit(limit).all()
        
        return jsonify({
            'success': True,
            'data': [sale.to_dict() for sale in sales],
            'count': len(sales)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/sales/bulk-void', methods=['POST'])
def bulk_void_sales():
    """Void multiple sales at once"""
    try:
        data = request.get_json()
        sale_ids = data.get('sale_ids', [])
        reason = data.get('reason', '')
        
        if not sale_ids:
            return jsonify({
                'success': False,
                'error': 'No sale IDs provided'
            }), 400
        
        voided_sales = []
        errors = []
        
        for sale_id in sale_ids:
            try:
                sale = Sale.query.get(sale_id)
                if not sale:
                    errors.append(f'Sale {sale_id} not found')
                    continue
                
                if sale.status == 'voided':
                    errors.append(f'Sale {sale.sale_number} is already voided')
                    continue
                
                # Restore stock for all items
                for item in sale.items:
                    if item.product:
                        item.product.stock_quantity += item.quantity
                        item.product.updated_at = datetime.utcnow()
                
                # Update sale status
                sale.status = 'voided'
                voided_sales.append(sale.sale_number)
                
            except Exception as e:
                errors.append(f'Error voiding sale {sale_id}: {str(e)}')
        
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
                'voided_count': len(voided_sales),
                'voided_sales': voided_sales,
                'reason': reason
            },
            'message': f'Successfully voided {len(voided_sales)} sales'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/sales/performance', methods=['GET'])
def get_sales_performance():
    """Get sales performance metrics"""
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Sales by day of week
        dow_sales = db.session.query(
            func.extract('dow', Sale.created_at).label('day_of_week'),
            func.count(Sale.id).label('sales_count'),
            func.sum(Sale.total_amount).label('revenue')
        ).filter(
            Sale.created_at >= start_date
        ).group_by(func.extract('dow', Sale.created_at)).all()
        
        # Convert day of week numbers to names
        dow_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        dow_performance = [
            {
                'day': dow_names[int(dow.day_of_week)],
                'sales_count': dow.sales_count,
                'revenue': dow.revenue
            } for dow in dow_sales
        ]
        
        # Monthly performance (last 12 months)
        monthly_performance = []
        for i in range(12):
            month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=31)
            month_end = month_end.replace(day=1) - timedelta(days=1)
            
            month_sales = Sale.query.filter(
                Sale.created_at >= month_start,
                Sale.created_at <= month_end
            ).all()
            
            monthly_performance.append({
                'month': month_start.strftime('%Y-%m'),
                'sales_count': len(month_sales),
                'revenue': sum(sale.total_amount for sale in month_sales)
            })
        
        monthly_performance.reverse()  # Chronological order
        
        # Best and worst performing days
        daily_performance = db.session.query(
            func.date(Sale.created_at).label('date'),
            func.count(Sale.id).label('sales_count'),
            func.sum(Sale.total_amount).label('revenue')
        ).filter(
            Sale.created_at >= start_date
        ).group_by(func.date(Sale.created_at)).all()
        
        if daily_performance:
            best_day = max(daily_performance, key=lambda x: x.revenue)
            worst_day = min(daily_performance, key=lambda x: x.revenue)
        else:
            best_day = worst_day = None
        
        return jsonify({
            'success': True,
            'data': {
                'day_of_week_performance': dow_performance,
                'monthly_performance': monthly_performance,
                'best_day': {
                    'date': best_day.date.strftime('%Y-%m-%d'),
                    'sales_count': best_day.sales_count,
                    'revenue': best_day.revenue
                } if best_day else None,
                'worst_day': {
                    'date': worst_day.date.strftime('%Y-%m-%d'),
                    'sales_count': worst_day.sales_count,
                    'revenue': worst_day.revenue
                } if worst_day else None,
                'period_days': days
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/sales/export', methods=['POST'])
def export_sales():
    """Export sales data (placeholder for CSV/Excel export)"""
    try:
        data = request.get_json()
        format_type = data.get('format', 'json')  # json, csv, excel
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        include_items = data.get('include_items', False)
        
        query = Sale.query
        
        if start_date:
            query = query.filter(Sale.created_at >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(Sale.created_at <= datetime.fromisoformat(end_date))
        
        sales = query.all()
        
        export_data = []
        for sale in sales:
            sale_data = sale.to_dict()
            
            if include_items:
                sale_data['detailed_items'] = [
                    {
                        **item.to_dict(),
                        'product_name': item.product.name if item.product else 'Unknown',
                        'product_sku': item.product.sku if item.product else ''
                    } for item in sale.items
                ]
            
            export_data.append(sale_data)
        
        return jsonify({
            'success': True,
            'data': export_data,
            'metadata': {
                'total_sales': len(export_data),
                'total_revenue': sum(sale['total_amount'] for sale in export_data),
                'export_format': format_type,
                'include_items': include_items,
                'exported_at': datetime.utcnow().isoformat(),
                'date_range': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            },
            'message': f'Sales data exported successfully ({len(export_data)} sales)'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/sales/trends', methods=['GET'])
def get_sales_trends():
    """Get sales trends and forecasting data"""
    try:
        days = request.args.get('days', 90, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Weekly trends
        weekly_trends = []
        current_date = start_date
        while current_date < datetime.utcnow():
            week_end = current_date + timedelta(days=7)
            week_sales = Sale.query.filter(
                Sale.created_at >= current_date,
                Sale.created_at < week_end
            ).all()
            
            weekly_trends.append({
                'week_start': current_date.strftime('%Y-%m-%d'),
                'sales_count': len(week_sales),
                'revenue': sum(sale.total_amount for sale in week_sales),
                'average_order_value': sum(sale.total_amount for sale in week_sales) / len(week_sales) if week_sales else 0
            })
            
            current_date = week_end
        
        # Calculate trend direction
        if len(weekly_trends) >= 2:
            recent_avg = sum(w['revenue'] for w in weekly_trends[-4:]) / min(4, len(weekly_trends))
            older_avg = sum(w['revenue'] for w in weekly_trends[:-4]) / max(1, len(weekly_trends) - 4)
            trend_direction = 'up' if recent_avg > older_avg else 'down' if recent_avg < older_avg else 'stable'
            trend_percentage = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
        else:
            trend_direction = 'stable'
            trend_percentage = 0
        
        return jsonify({
            'success': True,
            'data': {
                'weekly_trends': weekly_trends,
                'trend_analysis': {
                    'direction': trend_direction,
                    'percentage_change': trend_percentage,
                    'period_analyzed': f'{days} days'
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500