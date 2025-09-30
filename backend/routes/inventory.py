from flask import Blueprint, request, jsonify
from database import db
from models import Product, Purchase, PurchaseItem, Sale, SaleItem
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import uuid

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory', methods=['GET'])
def get_inventory():
    """Get all inventory items with stock levels"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        category_id = request.args.get('category_id', type=int)
        stock_status = request.args.get('stock_status', '')  # 'low', 'out', 'normal'
        
        query = Product.query.filter_by(is_active=True)
        
        # Search filter
        if search:
            query = query.filter(
                or_(
                    Product.name.contains(search),
                    Product.sku.contains(search),
                    Product.barcode.contains(search)
                )
            )
        
        # Category filter
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        # Stock status filter
        if stock_status == 'low':
            query = query.filter(
                and_(
                    Product.stock_quantity <= Product.min_stock_level,
                    Product.stock_quantity > 0
                )
            )
        elif stock_status == 'out':
            query = query.filter(Product.stock_quantity == 0)
        elif stock_status == 'normal':
            query = query.filter(Product.stock_quantity > Product.min_stock_level)
        
        products = query.order_by(Product.name).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Calculate inventory summary
        total_products = Product.query.filter_by(is_active=True).count()
        low_stock_count = Product.query.filter(
            Product.stock_quantity <= Product.min_stock_level,
            Product.stock_quantity > 0,
            Product.is_active == True
        ).count()
        out_of_stock_count = Product.query.filter(
            Product.stock_quantity == 0,
            Product.is_active == True
        ).count()
        total_stock_value = db.session.query(
            func.sum(Product.stock_quantity * Product.cost_price)
        ).filter(Product.is_active == True).scalar() or 0
        
        return jsonify({
            'success': True,
            'data': [product.to_dict() for product in products.items],
            'summary': {
                'total_products': total_products,
                'low_stock_count': low_stock_count,
                'out_of_stock_count': out_of_stock_count,
                'total_stock_value': total_stock_value
            },
            'pagination': {
                'page': page,
                'pages': products.pages,
                'per_page': per_page,
                'total': products.total
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/inventory/low-stock', methods=['GET'])
def get_low_stock():
    """Get products with low stock levels"""
    try:
        products = Product.query.filter(
            Product.stock_quantity <= Product.min_stock_level,
            Product.stock_quantity > 0,
            Product.is_active == True
        ).order_by(Product.stock_quantity.asc()).all()
        
        return jsonify({
            'success': True,
            'data': [product.to_dict() for product in products],
            'count': len(products)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/inventory/out-of-stock', methods=['GET'])
def get_out_of_stock():
    """Get products that are out of stock"""
    try:
        products = Product.query.filter(
            Product.stock_quantity == 0,
            Product.is_active == True
        ).order_by(Product.name).all()
        
        return jsonify({
            'success': True,
            'data': [product.to_dict() for product in products],
            'count': len(products)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/inventory/adjustments', methods=['POST'])
def create_inventory_adjustment():
    """Create inventory adjustment (increase/decrease stock)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['product_id', 'type', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'{field} is required'
                }), 400
        
        product = Product.query.get_or_404(data['product_id'])
        adjustment_type = data['type']  # 'increase' or 'decrease'
        quantity = int(data['quantity'])
        reason = data.get('reason', '')
        
        if quantity <= 0:
            return jsonify({
                'success': False,
                'error': 'Quantity must be greater than 0'
            }), 400
        
        old_quantity = product.stock_quantity
        
        if adjustment_type == 'increase':
            product.stock_quantity += quantity
        elif adjustment_type == 'decrease':
            if product.stock_quantity < quantity:
                return jsonify({
                    'success': False,
                    'error': f'Cannot decrease stock below zero. Current stock: {product.stock_quantity}'
                }), 400
            product.stock_quantity -= quantity
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid adjustment type. Use "increase" or "decrease"'
            }), 400
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'product': product.to_dict(),
                'adjustment': {
                    'type': adjustment_type,
                    'quantity': quantity,
                    'old_quantity': old_quantity,
                    'new_quantity': product.stock_quantity,
                    'reason': reason
                }
            },
            'message': f'Inventory adjusted successfully. {adjustment_type.title()}d by {quantity} units'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/inventory/bulk-update', methods=['POST'])
def bulk_update_inventory():
    """Bulk update inventory for multiple products"""
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
        
        for update in updates:
            try:
                product_id = update.get('product_id')
                new_quantity = update.get('quantity')
                
                if not product_id or new_quantity is None:
                    errors.append(f'Missing product_id or quantity in update: {update}')
                    continue
                
                product = Product.query.get(product_id)
                if not product:
                    errors.append(f'Product with ID {product_id} not found')
                    continue
                
                if new_quantity < 0:
                    errors.append(f'Quantity cannot be negative for product {product.name}')
                    continue
                
                product.stock_quantity = int(new_quantity)
                product.updated_at = datetime.utcnow()
                updated_products.append(product.to_dict())
                
            except Exception as e:
                errors.append(f'Error updating product {product_id}: {str(e)}')
        
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

@inventory_bp.route('/inventory/valuation', methods=['GET'])
def get_inventory_valuation():
    """Get inventory valuation report"""
    try:
        products = Product.query.filter_by(is_active=True).all()
        
        total_cost_value = 0
        total_retail_value = 0
        category_breakdown = {}
        
        for product in products:
            cost_value = product.stock_quantity * product.cost_price
            retail_value = product.stock_quantity * product.price
            
            total_cost_value += cost_value
            total_retail_value += retail_value
            
            # Category breakdown
            category_name = product.category.name if product.category else 'Uncategorized'
            if category_name not in category_breakdown:
                category_breakdown[category_name] = {
                    'cost_value': 0,
                    'retail_value': 0,
                    'product_count': 0,
                    'total_units': 0
                }
            
            category_breakdown[category_name]['cost_value'] += cost_value
            category_breakdown[category_name]['retail_value'] += retail_value
            category_breakdown[category_name]['product_count'] += 1
            category_breakdown[category_name]['total_units'] += product.stock_quantity
        
        potential_profit = total_retail_value - total_cost_value
        profit_margin = (potential_profit / total_retail_value * 100) if total_retail_value > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'total_cost_value': total_cost_value,
                'total_retail_value': total_retail_value,
                'potential_profit': potential_profit,
                'profit_margin': profit_margin,
                'category_breakdown': category_breakdown,
                'total_products': len(products),
                'total_units': sum(p.stock_quantity for p in products)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/inventory/movement', methods=['GET'])
def get_inventory_movement():
    """Get inventory movement report (sales and purchases)"""
    try:
        days = request.args.get('days', 30, type=int)
        product_id = request.args.get('product_id', type=int)
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Base queries
        sales_query = db.session.query(
            SaleItem.product_id,
            Product.name.label('product_name'),
            func.sum(SaleItem.quantity).label('sold_quantity'),
            func.sum(SaleItem.total_price).label('sales_value')
        ).join(Product).join(Sale).filter(
            Sale.created_at >= start_date
        )
        
        purchases_query = db.session.query(
            PurchaseItem.product_id,
            Product.name.label('product_name'),
            func.sum(PurchaseItem.quantity).label('purchased_quantity'),
            func.sum(PurchaseItem.total_cost).label('purchase_value')
        ).join(Product).join(Purchase).filter(
            Purchase.created_at >= start_date,
            Purchase.status == 'completed'
        )
        
        # Filter by product if specified
        if product_id:
            sales_query = sales_query.filter(SaleItem.product_id == product_id)
            purchases_query = purchases_query.filter(PurchaseItem.product_id == product_id)
        
        # Group by product
        sales_data = sales_query.group_by(SaleItem.product_id, Product.name).all()
        purchases_data = purchases_query.group_by(PurchaseItem.product_id, Product.name).all()
        
        # Combine data
        movement_data = {}
        
        # Add sales data
        for sale in sales_data:
            movement_data[sale.product_id] = {
                'product_id': sale.product_id,
                'product_name': sale.product_name,
                'sold_quantity': sale.sold_quantity or 0,
                'sales_value': sale.sales_value or 0,
                'purchased_quantity': 0,
                'purchase_value': 0
            }
        
        # Add purchase data
        for purchase in purchases_data:
            if purchase.product_id in movement_data:
                movement_data[purchase.product_id]['purchased_quantity'] = purchase.purchased_quantity or 0
                movement_data[purchase.product_id]['purchase_value'] = purchase.purchase_value or 0
            else:
                movement_data[purchase.product_id] = {
                    'product_id': purchase.product_id,
                    'product_name': purchase.product_name,
                    'sold_quantity': 0,
                    'sales_value': 0,
                    'purchased_quantity': purchase.purchased_quantity or 0,
                    'purchase_value': purchase.purchase_value or 0
                }
        
        # Calculate net movement
        for product_data in movement_data.values():
            product_data['net_movement'] = product_data['purchased_quantity'] - product_data['sold_quantity']
            product_data['net_value'] = product_data['purchase_value'] - product_data['sales_value']
        
        return jsonify({
            'success': True,
            'data': list(movement_data.values()),
            'period': f'Last {days} days',
            'summary': {
                'total_products_moved': len(movement_data),
                'total_sold': sum(p['sold_quantity'] for p in movement_data.values()),
                'total_purchased': sum(p['purchased_quantity'] for p in movement_data.values()),
                'total_sales_value': sum(p['sales_value'] for p in movement_data.values()),
                'total_purchase_value': sum(p['purchase_value'] for p in movement_data.values())
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/inventory/reorder-suggestions', methods=['GET'])
def get_reorder_suggestions():
    """Get reorder suggestions based on sales velocity and current stock"""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Get products with low stock
        low_stock_products = Product.query.filter(
            Product.stock_quantity <= Product.min_stock_level,
            Product.is_active == True
        ).all()
        
        suggestions = []
        start_date = datetime.utcnow() - timedelta(days=days)
        
        for product in low_stock_products:
            # Calculate sales velocity
            total_sold = db.session.query(
                func.sum(SaleItem.quantity)
            ).join(Sale).filter(
                SaleItem.product_id == product.id,
                Sale.created_at >= start_date
            ).scalar() or 0
            
            daily_velocity = total_sold / days if days > 0 else 0
            days_of_stock = product.stock_quantity / daily_velocity if daily_velocity > 0 else float('inf')
            
            # Suggest reorder quantity (30 days worth + safety stock)
            suggested_quantity = max(
                int(daily_velocity * 30) + product.min_stock_level - product.stock_quantity,
                product.min_stock_level
            )
            
            suggestions.append({
                'product': product.to_dict(),
                'sales_velocity': {
                    'total_sold_period': total_sold,
                    'daily_average': daily_velocity,
                    'days_of_stock_remaining': days_of_stock if days_of_stock != float('inf') else None
                },
                'suggestion': {
                    'reorder_quantity': suggested_quantity,
                    'estimated_cost': suggested_quantity * product.cost_price,
                    'priority': 'high' if days_of_stock < 7 else 'medium' if days_of_stock < 14 else 'low'
                }
            })
        
        # Sort by priority (high first)
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        suggestions.sort(key=lambda x: priority_order.get(x['suggestion']['priority'], 3))
        
        return jsonify({
            'success': True,
            'data': suggestions,
            'summary': {
                'total_suggestions': len(suggestions),
                'high_priority': len([s for s in suggestions if s['suggestion']['priority'] == 'high']),
                'medium_priority': len([s for s in suggestions if s['suggestion']['priority'] == 'medium']),
                'low_priority': len([s for s in suggestions if s['suggestion']['priority'] == 'low']),
                'total_estimated_cost': sum(s['suggestion']['estimated_cost'] for s in suggestions)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/inventory/abc-analysis', methods=['GET'])
def get_abc_analysis():
    """Get ABC analysis of inventory (based on sales value)"""
    try:
        days = request.args.get('days', 90, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get sales data for each product
        product_sales = db.session.query(
            Product.id,
            Product.name,
            Product.sku,
            Product.stock_quantity,
            Product.price,
            Product.cost_price,
            func.sum(SaleItem.quantity).label('total_sold'),
            func.sum(SaleItem.total_price).label('total_revenue')
        ).join(SaleItem).join(Sale).filter(
            Sale.created_at >= start_date,
            Product.is_active == True
        ).group_by(Product.id).all()
        
        if not product_sales:
            return jsonify({
                'success': True,
                'data': {'A': [], 'B': [], 'C': []},
                'message': 'No sales data found for the specified period'
            })
        
        # Sort by revenue (descending)
        sorted_products = sorted(product_sales, key=lambda x: x.total_revenue, reverse=True)
        
        total_revenue = sum(p.total_revenue for p in sorted_products)
        
        # Calculate cumulative percentages and classify
        cumulative_revenue = 0
        classified_products = {'A': [], 'B': [], 'C': []}
        
        for product in sorted_products:
            cumulative_revenue += product.total_revenue
            cumulative_percentage = (cumulative_revenue / total_revenue) * 100
            
            product_data = {
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'stock_quantity': product.stock_quantity,
                'price': product.price,
                'cost_price': product.cost_price,
                'total_sold': product.total_sold,
                'total_revenue': product.total_revenue,
                'revenue_percentage': (product.total_revenue / total_revenue) * 100,
                'cumulative_percentage': cumulative_percentage
            }
            
            # Classify products based on cumulative percentage
            if cumulative_percentage <= 80:
                classified_products['A'].append(product_data)
            elif cumulative_percentage <= 95:
                classified_products['B'].append(product_data)
            else:
                classified_products['C'].append(product_data)
        
        return jsonify({
            'success': True,
            'data': classified_products,
            'summary': {
                'total_products': len(sorted_products),
                'total_revenue': total_revenue,
                'category_counts': {
                    'A': len(classified_products['A']),
                    'B': len(classified_products['B']),
                    'C': len(classified_products['C'])
                },
                'category_percentages': {
                    'A': len(classified_products['A']) / len(sorted_products) * 100,
                    'B': len(classified_products['B']) / len(sorted_products) * 100,
                    'C': len(classified_products['C']) / len(sorted_products) * 100
                }
            },
            'period': f'Last {days} days'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/inventory/turnover', methods=['GET'])
def get_inventory_turnover():
    """Get inventory turnover analysis"""
    try:
        days = request.args.get('days', 365, type=int)  # Default to 1 year
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get products with their sales data
        products_with_sales = db.session.query(
            Product.id,
            Product.name,
            Product.sku,
            Product.stock_quantity,
            Product.cost_price,
            func.sum(SaleItem.quantity).label('total_sold'),
            func.sum(SaleItem.total_price).label('total_revenue')
        ).join(SaleItem).join(Sale).filter(
            Sale.created_at >= start_date,
            Product.is_active == True
        ).group_by(Product.id).all()
        
        turnover_data = []
        
        for product in products_with_sales:
            # Calculate average inventory (simplified - using current stock)
            avg_inventory = product.stock_quantity
            
            # Calculate Cost of Goods Sold (COGS)
            cogs = product.total_sold * product.cost_price
            
            # Calculate turnover ratio
            turnover_ratio = cogs / (avg_inventory * product.cost_price) if avg_inventory > 0 else 0
            
            # Calculate days in inventory
            days_in_inventory = days / turnover_ratio if turnover_ratio > 0 else float('inf')
            
            turnover_data.append({
                'product_id': product.id,
                'product_name': product.name,
                'sku': product.sku,
                'current_stock': product.stock_quantity,
                'total_sold': product.total_sold,
                'total_revenue': product.total_revenue,
                'cogs': cogs,
                'turnover_ratio': turnover_ratio,
                'days_in_inventory': days_in_inventory if days_in_inventory != float('inf') else None,
                'turnover_category': (
                    'Fast' if turnover_ratio > 12 else
                    'Medium' if turnover_ratio > 4 else
                    'Slow'
                )
            })
        
        # Sort by turnover ratio (descending)
        turnover_data.sort(key=lambda x: x['turnover_ratio'], reverse=True)
        
        # Calculate summary statistics
        total_products = len(turnover_data)
        fast_movers = len([p for p in turnover_data if p['turnover_category'] == 'Fast'])
        medium_movers = len([p for p in turnover_data if p['turnover_category'] == 'Medium'])
        slow_movers = len([p for p in turnover_data if p['turnover_category'] == 'Slow'])
        
        avg_turnover = sum(p['turnover_ratio'] for p in turnover_data) / total_products if total_products > 0 else 0
        
        return jsonify({
            'success': True,
            'data': turnover_data,
            'summary': {
                'total_products': total_products,
                'average_turnover_ratio': avg_turnover,
                'fast_movers': fast_movers,
                'medium_movers': medium_movers,
                'slow_movers': slow_movers,
                'fast_movers_percentage': (fast_movers / total_products * 100) if total_products > 0 else 0,
                'medium_movers_percentage': (medium_movers / total_products * 100) if total_products > 0 else 0,
                'slow_movers_percentage': (slow_movers / total_products * 100) if total_products > 0 else 0
            },
            'period': f'Last {days} days'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/inventory/stock-alerts', methods=['GET'])
def get_stock_alerts():
    """Get comprehensive stock alerts"""
    try:
        # Get all active products
        products = Product.query.filter_by(is_active=True).all()
        
        alerts = {
            'critical': [],  # Out of stock
            'warning': [],   # Low stock
            'overstocked': [] # Overstocked items
        }
        
        for product in products:
            if product.stock_quantity == 0:
                alerts['critical'].append({
                    'product': product.to_dict(),
                    'alert_type': 'out_of_stock',
                    'message': f'{product.name} is out of stock'
                })
            elif product.stock_quantity <= product.min_stock_level:
                alerts['warning'].append({
                    'product': product.to_dict(),
                    'alert_type': 'low_stock',
                    'message': f'{product.name} is running low (Current: {product.stock_quantity}, Min: {product.min_stock_level})'
                })
            elif product.stock_quantity > (product.min_stock_level * 10):  # Arbitrary overstocked threshold
                alerts['overstocked'].append({
                    'product': product.to_dict(),
                    'alert_type': 'overstocked',
                    'message': f'{product.name} may be overstocked (Current: {product.stock_quantity})'
                })
        
        total_alerts = len(alerts['critical']) + len(alerts['warning']) + len(alerts['overstocked'])
        
        return jsonify({
            'success': True,
            'data': alerts,
            'summary': {
                'total_alerts': total_alerts,
                'critical_count': len(alerts['critical']),
                'warning_count': len(alerts['warning']),
                'overstocked_count': len(alerts['overstocked'])
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/inventory/forecast', methods=['GET'])
def get_inventory_forecast():
    """Get inventory forecast based on historical sales"""
    try:
        days_history = request.args.get('days_history', 90, type=int)
        forecast_days = request.args.get('forecast_days', 30, type=int)
        product_id = request.args.get('product_id', type=int)
        
        start_date = datetime.utcnow() - timedelta(days=days_history)
        
        # Base query for sales data
        query = db.session.query(
            Product.id,
            Product.name,
            Product.sku,
            Product.stock_quantity,
            Product.min_stock_level,
            func.sum(SaleItem.quantity).label('total_sold')
        ).join(SaleItem).join(Sale).filter(
            Sale.created_at >= start_date,
            Product.is_active == True
        )
        
        if product_id:
            query = query.filter(Product.id == product_id)
        
        sales_data = query.group_by(Product.id).all()
        
        forecasts = []
        
        for product_data in sales_data:
            # Calculate daily average sales
            daily_avg_sales = product_data.total_sold / days_history
            
            # Forecast demand for the specified period
            forecasted_demand = daily_avg_sales * forecast_days
            
            # Calculate when stock will run out
            days_until_stockout = product_data.stock_quantity / daily_avg_sales if daily_avg_sales > 0 else float('inf')
            
            # Determine if reorder is needed
            needs_reorder = days_until_stockout < forecast_days
            
            # Calculate suggested order quantity
            if needs_reorder:
                shortage = forecasted_demand - product_data.stock_quantity
                suggested_order = max(shortage + product_data.min_stock_level, product_data.min_stock_level)
            else:
                suggested_order = 0
            
            forecasts.append({
                'product_id': product_data.id,
                'product_name': product_data.name,
                'sku': product_data.sku,
                'current_stock': product_data.stock_quantity,
                'min_stock_level': product_data.min_stock_level,
                'historical_sales': product_data.total_sold,
                'daily_avg_sales': daily_avg_sales,
                'forecasted_demand': forecasted_demand,
                'days_until_stockout': days_until_stockout if days_until_stockout != float('inf') else None,
                'needs_reorder': needs_reorder,
                'suggested_order_quantity': suggested_order,
                'forecast_accuracy': 'Medium'  # This could be calculated based on historical variance
            })
        
        return jsonify({
            'success': True,
            'data': forecasts,
            'parameters': {
                'history_period_days': days_history,
                'forecast_period_days': forecast_days,
                'total_products_analyzed': len(forecasts)
            },
            'summary': {
                'products_needing_reorder': len([f for f in forecasts if f['needs_reorder']]),
                'total_suggested_orders': sum(f['suggested_order_quantity'] for f in forecasts)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500