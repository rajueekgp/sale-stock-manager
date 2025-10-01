from flask import Blueprint, request, jsonify
from database import db
from models import Customer, Sale, SaleItem, Product
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, desc, asc
from collections import defaultdict

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/customers', methods=['GET'])
def get_customers():
    """Get all customers with pagination and search"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        sort_by = request.args.get('sort_by', 'name')  # name, email, created_at, total_spent
        sort_order = request.args.get('sort_order', 'asc')  # asc, desc
        
        query = Customer.query
        
        # Search filter
        if search:
            query = query.filter(
                or_(
                    Customer.name.contains(search),
                    Customer.email.contains(search),
                    Customer.phone.contains(search)
                )
            )
        
        # Sorting
        if sort_by == 'name':
            order_column = Customer.name
        elif sort_by == 'email':
            order_column = Customer.email
        elif sort_by == 'created_at':
            order_column = Customer.created_at
        else:
            order_column = Customer.name
        
        if sort_order == 'desc':
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))
        
        customers = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Enhance customer data with purchase statistics
        enhanced_customers = []
        for customer in customers.items:
            customer_dict = customer.to_dict()
            
            # Get purchase statistics
            total_orders = Sale.query.filter_by(customer_id=customer.id).count()
            total_spent = db.session.query(func.sum(Sale.total_amount)).filter_by(customer_id=customer.id).scalar() or 0
            last_purchase = db.session.query(func.max(Sale.created_at)).filter_by(customer_id=customer.id).scalar()
            
            customer_dict.update({
                'total_orders': total_orders,
                'total_spent': total_spent,
                'average_order_value': total_spent / total_orders if total_orders > 0 else 0,
                'last_purchase': last_purchase.isoformat() if last_purchase else None,
                'days_since_last_purchase': (datetime.utcnow() - last_purchase).days if last_purchase else None
            })
            
            enhanced_customers.append(customer_dict)
        
        return jsonify({
            'success': True,
            'data': enhanced_customers,
            'pagination': {
                'page': page,
                'pages': customers.pages,
                'per_page': per_page,
                'total': customers.total
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@customers_bp.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Get single customer with detailed information"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        customer_dict = customer.to_dict()
        
        # Get detailed purchase history
        sales = Sale.query.filter_by(customer_id=customer_id).order_by(desc(Sale.created_at)).all()
        
        # Calculate statistics
        total_orders = len(sales)
        total_spent = sum(sale.total_amount for sale in sales)
        total_items_purchased = sum(sum(item.quantity for item in sale.items) for sale in sales)
        
        # Get favorite products
        product_purchases = defaultdict(lambda: {'quantity': 0, 'total_spent': 0})
        for sale in sales:
            for item in sale.items:
                if item.product:
                    product_purchases[item.product.name]['quantity'] += item.quantity
                    product_purchases[item.product.name]['total_spent'] += item.total_price
        
        favorite_products = sorted(
            [
                {
                    'product_name': name,
                    'quantity_purchased': data['quantity'],
                    'total_spent': data['total_spent']
                }
                for name, data in product_purchases.items()
            ],
            key=lambda x: x['quantity_purchased'],
            reverse=True
        )[:5]
        
        # Purchase frequency analysis
        if len(sales) > 1:
            first_purchase = min(sale.created_at for sale in sales)
            last_purchase = max(sale.created_at for sale in sales)
            customer_lifetime_days = (last_purchase - first_purchase).days
            purchase_frequency = total_orders / max(customer_lifetime_days, 1) if customer_lifetime_days > 0 else 0
        else:
            purchase_frequency = 0
            customer_lifetime_days = 0
        
        # Recent purchases (last 5)
        recent_purchases = [sale.to_dict() for sale in sales[:5]]
        
        customer_dict.update({
            'statistics': {
                'total_orders': total_orders,
                'total_spent': total_spent,
                'total_items_purchased': total_items_purchased,
                'average_order_value': total_spent / total_orders if total_orders > 0 else 0,
                'customer_lifetime_days': customer_lifetime_days,
                'purchase_frequency': purchase_frequency,
                'first_purchase': sales[-1].created_at.isoformat() if sales else None,
                'last_purchase': sales[0].created_at.isoformat() if sales else None
            },
            'favorite_products': favorite_products,
            'recent_purchases': recent_purchases
        })
        
        return jsonify({
            'success': True,
            'data': customer_dict
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@customers_bp.route('/customers', methods=['POST'])
def create_customer():
    """Create a new customer"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'{field} is required'
                }), 400
        
        # Check if email already exists
        if data.get('email'):
            existing_customer = Customer.query.filter_by(email=data['email']).first()
            if existing_customer:
                return jsonify({
                    'success': False,
                    'error': 'Customer with this email already exists'
                }), 400
        
        # Check if GST number already exists
        if data.get('gst_number'):
            existing_customer_gst = Customer.query.filter_by(gst_number=data['gst_number']).first()
            if existing_customer_gst:
                return jsonify({
                    'success': False,
                    'error': 'Customer with this GST number already exists'
                }), 400

        # Validate email format (basic validation)
        if data.get('email') and '@' not in data['email']:
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400
        
        customer = Customer(
            name=data['name'].strip(),
            email=data.get('email', '').strip() if data.get('email') else None,
            phone=data.get('phone', '').strip() if data.get('phone') else None,
            address=data.get('address', '').strip() if data.get('address') else None,
            gst_number=data.get('gst_number', '').strip() if data.get('gst_number') else None,
            opening_balance=data.get('opening_balance'),
            created_at=datetime.fromisoformat(data['opening_balance_as_on']) if data.get('opening_balance_as_on') else None,
        )
        
        db.session.add(customer)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': customer.to_dict(),
            'message': 'Customer created successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@customers_bp.route('/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """Update customer information"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        data = request.get_json()
        
        # Check if email already exists (excluding current customer)
        if 'email' in data and data['email'] and data['email'] != customer.email:
            existing_customer = Customer.query.filter_by(email=data['email']).first()
            if existing_customer:
                return jsonify({
                    'success': False,
                    'error': 'Customer with this email already exists'
                }), 400
        
        # Check if GST number already exists (excluding current customer)
        if 'gst_number' in data and data['gst_number'] and data['gst_number'] != customer.gst_number:
            existing_customer_gst = Customer.query.filter_by(gst_number=data['gst_number']).first()
            if existing_customer_gst:
                return jsonify({
                    'success': False,
                    'error': 'Customer with this GST number already exists'
                }), 400

        # Validate email format (basic validation)
        if data.get('email') and '@' not in data['email']:
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400
        
        # Update fields
        if 'name' in data:
            customer.name = data['name'].strip()
        if 'email' in data:
            customer.email = data['email'].strip() if data['email'] else None
        if 'phone' in data:
            customer.phone = data['phone'].strip() if data['phone'] else None
        if 'address' in data:
            customer.address = data['address'].strip() if data['address'] else None
        if 'gst_number' in data:
            customer.gst_number = data['gst_number'].strip() if data['gst_number'] else None
        # Note: Opening balance is typically set only at creation and not updated.
        # However, if you need to allow updates, you can uncomment the following lines.
        if 'opening_balance' in data:
            customer.opening_balance = data['opening_balance']
        # if 'opening_balance_as_on' in data and data['opening_balance_as_on']:
        #     customer.opening_balance_as_on = datetime.fromisoformat(data['opening_balance_as_on'])

        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': customer.to_dict(),
            'message': 'Customer updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@customers_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Delete customer (soft delete by checking for existing sales)"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        
        # Check if customer has sales
        sales_count = Sale.query.filter_by(customer_id=customer_id).count()
        if sales_count > 0:
            return jsonify({
                'success': False,
                'error': f'Cannot delete customer with existing sales records ({sales_count} sales found). Consider archiving instead.'
            }), 400
        
        db.session.delete(customer)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Customer deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@customers_bp.route('/customers/<int:customer_id>/purchases', methods=['GET'])
def get_customer_purchases(customer_id):
    """Get customer's purchase history"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Sale.query.filter_by(customer_id=customer_id)
        
        # Date filters
        if start_date:
            query = query.filter(Sale.created_at >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(Sale.created_at <= datetime.fromisoformat(end_date))
        
        sales = query.order_by(desc(Sale.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'customer': customer.to_dict(),
                'purchases': [sale.to_dict() for sale in sales.items]
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

@customers_bp.route('/customers/analytics', methods=['GET'])
def get_customer_analytics():
    """Get customer analytics and insights"""
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total customers
        total_customers = Customer.query.count()
        
        # New customers in period
        new_customers = Customer.query.filter(Customer.created_at >= start_date).count()
        
        # Active customers (made purchases in period)
        active_customers = db.session.query(Customer.id).join(Sale).filter(
            Sale.created_at >= start_date
        ).distinct().count()
        
        # Customer lifetime value analysis
        customer_values = db.session.query(
            Customer.id,
            Customer.name,
            func.sum(Sale.total_amount).label('total_spent'),
            func.count(Sale.id).label('total_orders'),
            func.max(Sale.created_at).label('last_purchase'),
            func.min(Sale.created_at).label('first_purchase')
        ).join(Sale).group_by(Customer.id).all()
        
        # Segment customers by value
        if customer_values:
            spending_amounts = [cv.total_spent for cv in customer_values]
            spending_amounts.sort(reverse=True)
            
            # Define segments (top 20%, middle 30%, bottom 50%)
            high_value_threshold = spending_amounts[int(len(spending_amounts) * 0.2)] if len(spending_amounts) > 5 else 0
            medium_value_threshold = spending_amounts[int(len(spending_amounts) * 0.5)] if len(spending_amounts) > 2 else 0
            
            segments = {'high_value': 0, 'medium_value': 0, 'low_value': 0}
            total_clv = 0
            
            for cv in customer_values:
                total_clv += cv.total_spent
                if cv.total_spent >= high_value_threshold:
                    segments['high_value'] += 1
                elif cv.total_spent >= medium_value_threshold:
                    segments['medium_value'] += 1
                else:
                    segments['low_value'] += 1
            
            average_clv = total_clv / len(customer_values)
        else:
            segments = {'high_value': 0, 'medium_value': 0, 'low_value': 0}
            average_clv = 0
        
        # Customer acquisition trend (last 12 months)
        acquisition_trend = []
        for i in range(12):
            month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=31)
            month_end = month_end.replace(day=1) - timedelta(days=1)  # Last day of month
            
            new_customers_month = Customer.query.filter(
                Customer.created_at >= month_start,
                Customer.created_at <= month_end
            ).count()
            
            acquisition_trend.append({
                'month': month_start.strftime('%Y-%m'),
                'new_customers': new_customers_month
            })
        
        acquisition_trend.reverse()  # Chronological order
        
        # Top customers by spending
        top_customers = db.session.query(
            Customer.name,
            Customer.email,
            func.sum(Sale.total_amount).label('total_spent'),
            func.count(Sale.id).label('total_orders')
        ).join(Sale).group_by(Customer.id).order_by(desc('total_spent')).limit(10).all()
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total_customers': total_customers,
                    'new_customers_period': new_customers,
                    'active_customers_period': active_customers,
                    'customer_retention_rate': (active_customers / total_customers * 100) if total_customers > 0 else 0,
                    'average_customer_lifetime_value': average_clv
                },
                'segments': segments,
                'acquisition_trend': acquisition_trend,
                'top_customers': [
                    {
                        'name': tc.name,
                        'email': tc.email,
                        'total_spent': tc.total_spent,
                        'total_orders': tc.total_orders,
                        'average_order_value': tc.total_spent / tc.total_orders if tc.total_orders > 0 else 0
                    } for tc in top_customers
                ],
                'period_days': days
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@customers_bp.route('/customers/search', methods=['GET'])
def search_customers():
    """Search customers by name, email, or phone"""
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 10, type=int)
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        customers = Customer.query.filter(
            or_(
                Customer.name.contains(query),
                Customer.email.contains(query),
                Customer.phone.contains(query)
            )
        ).limit(limit).all()
        
        return jsonify({
            'success': True,
            'data': [customer.to_dict() for customer in customers],
            'count': len(customers)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@customers_bp.route('/customers/bulk-import', methods=['POST'])
def bulk_import_customers():
    """Bulk import customers from JSON data"""
    try:
        data = request.get_json()
        customers_data = data.get('customers', [])
        
        if not customers_data:
            return jsonify({
                'success': False,
                'error': 'No customer data provided'
            }), 400
        
        created_customers = []
        errors = []
        
        for i, customer_data in enumerate(customers_data):
            try:
                # Validate required fields
                if not customer_data.get('name'):
                    errors.append(f'Row {i+1}: Name is required')
                    continue
                
                # Check for duplicate email
                if customer_data.get('email'):
                    existing = Customer.query.filter_by(email=customer_data['email']).first()
                    if existing:
                        errors.append(f'Row {i+1}: Email {customer_data["email"]} already exists')
                        continue
                
                customer = Customer(
                    name=customer_data['name'].strip(),
                    email=customer_data.get('email', '').strip() if customer_data.get('email') else None,
                    phone=customer_data.get('phone', '').strip() if customer_data.get('phone') else None,
                    address=customer_data.get('address', '').strip() if customer_data.get('address') else None
                )
                
                db.session.add(customer)
                created_customers.append(customer_data['name'])
                
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
                'created_count': len(created_customers),
                'created_customers': created_customers
            },
            'message': f'Successfully imported {len(created_customers)} customers'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@customers_bp.route('/customers/<int:customer_id>/loyalty-points', methods=['GET'])
def get_customer_loyalty_points(customer_id):
    """Get customer loyalty points (placeholder for future loyalty program)"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        
        # Calculate points based on total spending (1 point per dollar spent)
        total_spent = db.session.query(func.sum(Sale.total_amount)).filter_by(customer_id=customer_id).scalar() or 0
        points = int(total_spent)  # Simple 1:1 ratio
        
        # Points history (based on sales)
        sales = Sale.query.filter_by(customer_id=customer_id).order_by(desc(Sale.created_at)).limit(10).all()
        points_history = [
            {
                'date': sale.created_at.isoformat(),
                'points_earned': int(sale.total_amount),
                'transaction_id': sale.sale_number,
                'description': f'Purchase - {sale.sale_number}'
            } for sale in sales
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'customer': customer.to_dict(),
                'loyalty_points': {
                    'current_points': points,
                    'total_earned': points,
                    'points_redeemed': 0,  # Placeholder for future redemption tracking
                    'tier': 'Bronze' if points < 1000 else 'Silver' if points < 5000 else 'Gold',
                    'next_tier_threshold': 1000 if points < 1000 else 5000 if points < 5000 else None
                },
                'points_history': points_history
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@customers_bp.route('/customers/<int:customer_id>/recommendations', methods=['GET'])
def get_customer_recommendations(customer_id):
    """Get product recommendations for customer based on purchase history"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        
        # Get customer's purchase history
        purchased_products = db.session.query(
            Product.id,
            Product.name,
            Product.category_id,
            func.sum(SaleItem.quantity).label('total_purchased')
        ).join(SaleItem).join(Sale).filter(
            Sale.customer_id == customer_id
        ).group_by(Product.id).all()
        
        if not purchased_products:
            # If no purchase history, recommend popular products
            popular_products = db.session.query(
                Product.id,
                Product.name,
                Product.price,
                Product.category_id,
                func.sum(SaleItem.quantity).label('popularity')
            ).join(SaleItem).join(Sale).filter(
                Product.is_active == True
            ).group_by(Product.id).order_by(desc('popularity')).limit(5).all()
            
            recommendations = [
                {
                    'product_id': p.id,
                    'product_name': p.name,
                    'price': p.price,
                    'reason': 'Popular product',
                    'confidence': 0.5
                } for p in popular_products
            ]
        else:
            # Get categories customer has purchased from
            purchased_categories = list(set(p.category_id for p in purchased_products if p.category_id))
            
            # Find products in same categories that customer hasn't bought
            purchased_product_ids = [p.id for p in purchased_products]
            
            category_recommendations = db.session.query(
                Product.id,
                Product.name,
                Product.price,
                Product.category_id,
                Category.name.label('category_name')
            ).join(Category).filter(
                Product.category_id.in_(purchased_categories),
                ~Product.id.in_(purchased_product_ids),
                Product.is_active == True
            ).limit(5).all()
            
            recommendations = [
                {
                    'product_id': p.id,
                    'product_name': p.name,
                    'price': p.price,
                    'category': p.category_name,
                    'reason': f'Similar to your {p.category_name} purchases',
                    'confidence': 0.8
                } for p in category_recommendations
            ]
        
        return jsonify({
            'success': True,
            'data': {
                'customer': customer.to_dict(),
                'recommendations': recommendations,
                'recommendation_count': len(recommendations)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@customers_bp.route('/customers/export', methods=['POST'])
def export_customers():
    """Export customer data (placeholder for CSV/Excel export)"""
    try:
        data = request.get_json()
        format_type = data.get('format', 'json')  # json, csv, excel
        include_analytics = data.get('include_analytics', False)
        
        # Get all customers
        customers = Customer.query.all()
        
        export_data = []
        for customer in customers:
            customer_data = customer.to_dict()
            
            if include_analytics:
                # Add analytics data
                total_orders = Sale.query.filter_by(customer_id=customer.id).count()
                total_spent = db.session.query(func.sum(Sale.total_amount)).filter_by(customer_id=customer.id).scalar() or 0
                last_purchase = db.session.query(func.max(Sale.created_at)).filter_by(customer_id=customer.id).scalar()
                
                customer_data.update({
                    'total_orders': total_orders,
                    'total_spent': total_spent,
                    'average_order_value': total_spent / total_orders if total_orders > 0 else 0,
                    'last_purchase': last_purchase.isoformat() if last_purchase else None
                })
            
            export_data.append(customer_data)
        
        return jsonify({
            'success': True,
            'data': export_data,
            'metadata': {
                'total_customers': len(export_data),
                'export_format': format_type,
                'include_analytics': include_analytics,
                'exported_at': datetime.utcnow().isoformat()
            },
            'message': f'Customer data exported successfully ({len(export_data)} customers)'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@customers_bp.route('/customers/<int:customer_id>/merge', methods=['POST'])
def merge_customers(customer_id):
    """Merge duplicate customers"""
    try:
        data = request.get_json()
        target_customer_id = data.get('target_customer_id')
        
        if not target_customer_id:
            return jsonify({
                'success': False,
                'error': 'Target customer ID is required'
            }), 400
        
        if customer_id == target_customer_id:
            return jsonify({
                'success': False,
                'error': 'Cannot merge customer with itself'
            }), 400
        
        source_customer = Customer.query.get_or_404(customer_id)
        target_customer = Customer.query.get_or_404(target_customer_id)
        
        # Move all sales from source to target customer
        Sale.query.filter_by(customer_id=customer_id).update({'customer_id': target_customer_id})
        
        # Update target customer info if source has more complete data
        if not target_customer.email and source_customer.email:
            target_customer.email = source_customer.email
        if not target_customer.phone and source_customer.phone:
            target_customer.phone = source_customer.phone
        if not target_customer.address and source_customer.address:
            target_customer.address = source_customer.address
        
        # Delete source customer
        db.session.delete(source_customer)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': target_customer.to_dict(),
            'message': f'Successfully merged customer {source_customer.name} into {target_customer.name}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@customers_bp.route('/customers/duplicates', methods=['GET'])
def find_duplicate_customers():
    """Find potential duplicate customers based on name, email, or phone"""
    try:
        # Find customers with same email
        email_duplicates = db.session.query(
            Customer.email,
            func.count(Customer.id).label('count'),
            func.group_concat(Customer.id).label('customer_ids')
        ).filter(
            Customer.email.isnot(None),
            Customer.email != ''
        ).group_by(Customer.email).having(func.count(Customer.id) > 1).all()
        
        # Find customers with same phone
        phone_duplicates = db.session.query(
            Customer.phone,
            func.count(Customer.id).label('count'),
            func.group_concat(Customer.id).label('customer_ids')
        ).filter(
            Customer.phone.isnot(None),
            Customer.phone != ''
        ).group_by(Customer.phone).having(func.count(Customer.id) > 1).all()
        
        # Find customers with similar names (basic similarity)
        name_groups = defaultdict(list)
        customers = Customer.query.all()
        for customer in customers:
            # Simple name similarity - group by first word of name
            first_word = customer.name.split()[0].lower() if customer.name else ''
            if len(first_word) > 2:  # Only consider names longer than 2 characters
                name_groups[first_word].append(customer)
        
        name_duplicates = [
            {
                'similar_name': key,
                'customers': [c.to_dict() for c in customers_list]
            }
            for key, customers_list in name_groups.items() 
            if len(customers_list) > 1
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'email_duplicates': [
                    {
                        'email': dup.email,
                        'count': dup.count,
                        'customer_ids': [int(id) for id in dup.customer_ids.split(',')]
                    } for dup in email_duplicates
                ],
                'phone_duplicates': [
                    {
                        'phone': dup.phone,
                        'count': dup.count,
                        'customer_ids': [int(id) for id in dup.customer_ids.split(',')]
                    } for dup in phone_duplicates
                ],
                'name_duplicates': name_duplicates[:10]  # Limit to 10 groups
            },
            'summary': {
                'email_duplicate_groups': len(email_duplicates),
                'phone_duplicate_groups': len(phone_duplicates),
                'name_duplicate_groups': len([g for g in name_groups.values() if len(g) > 1])
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
