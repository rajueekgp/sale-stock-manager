from flask import Blueprint, request, jsonify
from database import db
from models import Product, Sale, SaleItem, Purchase, PurchaseItem, Customer, Category
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, desc, asc
from collections import defaultdict
import calendar

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports/dashboard', methods=['GET'])
def get_dashboard_report():
    """Get comprehensive dashboard report"""
    try:
        # Date range parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = datetime.utcnow().isoformat()
        
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # Sales metrics
        sales_query = Sale.query.filter(
            Sale.created_at >= start_dt,
            Sale.created_at <= end_dt
        )
        
        total_sales = sales_query.count()
        total_revenue = db.session.query(func.sum(Sale.total_amount)).filter(
            Sale.created_at >= start_dt,
            Sale.created_at <= end_dt
        ).scalar() or 0
        
        avg_order_value = total_revenue / total_sales if total_sales > 0 else 0
        
        # Compare with previous period
        period_days = (end_dt - start_dt).days
        prev_start = start_dt - timedelta(days=period_days)
        prev_end = start_dt
        
        prev_sales = Sale.query.filter(
            Sale.created_at >= prev_start,
            Sale.created_at < prev_end
        ).count()
        
        prev_revenue = db.session.query(func.sum(Sale.total_amount)).filter(
            Sale.created_at >= prev_start,
            Sale.created_at < prev_end
        ).scalar() or 0
        
        # Calculate growth rates
        sales_growth = ((total_sales - prev_sales) / prev_sales * 100) if prev_sales > 0 else 0
        revenue_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        
        # Top selling products
        top_products = db.session.query(
            Product.name,
            func.sum(SaleItem.quantity).label('total_sold'),
            func.sum(SaleItem.total_price).label('total_revenue')
        ).join(SaleItem).join(Sale).filter(
            Sale.created_at >= start_dt,
            Sale.created_at <= end_dt
        ).group_by(Product.id).order_by(desc('total_sold')).limit(5).all()
        
        # Low stock alerts
        low_stock_count = Product.query.filter(
            Product.stock_quantity <= Product.min_stock_level,
            Product.is_active == True
        ).count()
        
        return jsonify({
            'success': True,
            'data': {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'days': period_days
                },
                'sales_metrics': {
                    'total_sales': total_sales,
                    'total_revenue': total_revenue,
                    'average_order_value': avg_order_value,
                    'sales_growth': sales_growth,
                    'revenue_growth': revenue_growth
                },
                'top_products': [
                    {
                        'name': p.name,
                        'quantity_sold': p.total_sold,
                        'revenue': p.total_revenue
                    } for p in top_products
                ],
                'inventory_alerts': {
                    'low_stock_count': low_stock_count
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/reports/sales', methods=['GET'])
def get_sales_report():
    """Get detailed sales report"""
    try:
        # Parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        group_by = request.args.get('group_by', 'day')  # day, week, month
        customer_id = request.args.get('customer_id', type=int)
        category_id = request.args.get('category_id', type=int)
        
        # Default date range
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = datetime.utcnow().isoformat()
        
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # Base query
        query = Sale.query.filter(
            Sale.created_at >= start_dt,
            Sale.created_at <= end_dt
        )
        
        if customer_id:
            query = query.filter(Sale.customer_id == customer_id)
        
        sales = query.all()
        
        # Filter by category if specified
        if category_id:
            filtered_sales = []
            for sale in sales:
                has_category_items = any(
                    item.product.category_id == category_id 
                    for item in sale.items if item.product
                )
                if has_category_items:
                    filtered_sales.append(sale)
            sales = filtered_sales
        
        # Group sales by time period
        grouped_data = defaultdict(lambda: {
            'sales_count': 0,
            'total_revenue': 0,
            'total_tax': 0,
            'total_discount': 0,
            'items_sold': 0
        })
        
        for sale in sales:
            if group_by == 'day':
                key = sale.created_at.strftime('%Y-%m-%d')
            elif group_by == 'week':
                key = sale.created_at.strftime('%Y-W%U')
            elif group_by == 'month':
                key = sale.created_at.strftime('%Y-%m')
            else:
                key = sale.created_at.strftime('%Y-%m-%d')
            
            grouped_data[key]['sales_count'] += 1
            grouped_data[key]['total_revenue'] += sale.total_amount
            grouped_data[key]['total_tax'] += sale.tax_amount
            grouped_data[key]['total_discount'] += sale.discount_amount
            grouped_data[key]['items_sold'] += sum(item.quantity for item in sale.items)
        
        # Convert to list and sort
        time_series = [
            {
                'period': key,
                **values
            }
            for key, values in sorted(grouped_data.items())
        ]
        
        # Calculate totals
        total_sales = len(sales)
        total_revenue = sum(sale.total_amount for sale in sales)
        total_tax = sum(sale.tax_amount for sale in sales)
        total_discount = sum(sale.discount_amount for sale in sales)
        total_items = sum(sum(item.quantity for item in sale.items) for sale in sales)
        
        # Payment method breakdown
        payment_methods = defaultdict(lambda: {'count': 0, 'total': 0})
        for sale in sales:
            payment_methods[sale.payment_method]['count'] += 1
            payment_methods[sale.payment_method]['total'] += sale.total_amount
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total_sales': total_sales,
                    'total_revenue': total_revenue,
                    'total_tax': total_tax,
                    'total_discount': total_discount,
                    'total_items_sold': total_items,
                    'average_order_value': total_revenue / total_sales if total_sales > 0 else 0
                },
                'time_series': time_series,
                'payment_methods': dict(payment_methods),
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'group_by': group_by
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/reports/products', methods=['GET'])
def get_product_report():
    """Get product performance report"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        sort_by = request.args.get('sort_by', 'revenue')  # revenue, quantity, profit
        category_id = request.args.get('category_id', type=int)
        
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = datetime.utcnow().isoformat()
        
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # Query product sales data
        query = db.session.query(
            Product.id,
            Product.name,
            Product.sku,
            Product.price,
            Product.cost_price,
            Product.stock_quantity,
            Product.category_id,
            Category.name.label('category_name'),
            func.sum(SaleItem.quantity).label('total_sold'),
            func.sum(SaleItem.total_price).label('total_revenue'),
            func.count(Sale.id).label('transaction_count')
        ).join(SaleItem).join(Sale).join(Category, Product.category_id == Category.id).filter(
            Sale.created_at >= start_dt,
            Sale.created_at <= end_dt,
            Product.is_active == True
        )
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        products_data = query.group_by(Product.id).all()
        
        # Calculate additional metrics
        product_reports = []
        for product in products_data:
            profit = (product.price - product.cost_price) * product.total_sold
            profit_margin = ((product.price - product.cost_price) / product.price * 100) if product.price > 0 else 0
            
            product_reports.append({
                'product_id': product.id,
                'name': product.name,
                'sku': product.sku,
                'category': product.category_name,
                'price': product.price,
                'cost_price': product.cost_price,
                'current_stock': product.stock_quantity,
                'quantity_sold': product.total_sold,
                'revenue': product.total_revenue,
                'profit': profit,
                'profit_margin': profit_margin,
                'transaction_count': product.transaction_count,
                'average_quantity_per_sale': product.total_sold / product.transaction_count if product.transaction_count > 0 else 0
            })
        
        # Sort products
        if sort_by == 'revenue':
            product_reports.sort(key=lambda x: x['revenue'], reverse=True)
        elif sort_by == 'quantity':
            product_reports.sort(key=lambda x: x['quantity_sold'], reverse=True)
        elif sort_by == 'profit':
            product_reports.sort(key=lambda x: x['profit'], reverse=True)
        
        # Category summary
        category_summary = defaultdict(lambda: {
            'revenue': 0,
            'quantity_sold': 0,
            'profit': 0,
            'product_count': 0
        })
        
        for product in product_reports:
            cat = product['category']
            category_summary[cat]['revenue'] += product['revenue']
            category_summary[cat]['quantity_sold'] += product['quantity_sold']
            category_summary[cat]['profit'] += product['profit']
            category_summary[cat]['product_count'] += 1
        
        return jsonify({
            'success': True,
            'data': {
                'products': product_reports,
                'category_summary': dict(category_summary),
                'summary': {
                    'total_products': len(product_reports),
                    'total_revenue': sum(p['revenue'] for p in product_reports),
                    'total_quantity_sold': sum(p['quantity_sold'] for p in product_reports),
                    'total_profit': sum(p['profit'] for p in product_reports)
                },
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'sort_by': sort_by
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/reports/customers', methods=['GET'])
def get_customer_report():
    """Get customer analysis report"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        sort_by = request.args.get('sort_by', 'revenue')  # revenue, frequency, recent
        
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=90)).isoformat()
        if not end_date:
            end_date = datetime.utcnow().isoformat()
        
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # Query customer data
        customer_data = db.session.query(
            Customer.id,
            Customer.name,
            Customer.email,
            Customer.phone,
            func.count(Sale.id).label('total_orders'),
            func.sum(Sale.total_amount).label('total_spent'),
            func.max(Sale.created_at).label('last_purchase'),
            func.min(Sale.created_at).label('first_purchase')
        ).join(Sale).filter(
            Sale.created_at >= start_dt,
            Sale.created_at <= end_dt
        ).group_by(Customer.id).all()
        
        customer_reports = []
        for customer in customer_data:
            avg_order_value = customer.total_spent / customer.total_orders if customer.total_orders > 0 else 0
            days_since_last_purchase = (datetime.utcnow() - customer.last_purchase).days if customer.last_purchase else None
            
            # Customer lifetime (in days)
            customer_lifetime = (customer.last_purchase - customer.first_purchase).days if customer.first_purchase and customer.last_purchase else 0
            
            customer_reports.append({
                'customer_id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone,
                'total_orders': customer.total_orders,
                'total_spent': customer.total_spent,
                'average_order_value': avg_order_value,
                'last_purchase': customer.last_purchase.isoformat() if customer.last_purchase else None,
                'first_purchase': customer.first_purchase.isoformat() if customer.first_purchase else None,
                'days_since_last_purchase': days_since_last_purchase,
                'customer_lifetime_days': customer_lifetime,
                'purchase_frequency': customer.total_orders / max(customer_lifetime, 1) if customer_lifetime > 0 else 0
            })
        
        # Sort customers
        if sort_by == 'revenue':
            customer_reports.sort(key=lambda x: x['total_spent'], reverse=True)
        elif sort_by == 'frequency':
            customer_reports.sort(key=lambda x: x['total_orders'], reverse=True)
        elif sort_by == 'recent':
            customer_reports.sort(key=lambda x: x['days_since_last_purchase'] or float('inf'))
        
        # Customer segmentation
        if customer_reports:
            revenue_threshold_high = sorted([c['total_spent'] for c in customer_reports], reverse=True)[len(customer_reports)//3] if len(customer_reports) >= 3 else 0
            revenue_threshold_low = sorted([c['total_spent'] for c in customer_reports], reverse=True)[2*len(customer_reports)//3] if len(customer_reports) >= 3 else 0
            
            for customer in customer_reports:
                if customer['total_spent'] >= revenue_threshold_high:
                    customer['segment'] = 'High Value'
                elif customer['total_spent'] >= revenue_threshold_low:
                    customer['segment'] = 'Medium Value'
                else:
                    customer['segment'] = 'Low Value'
        
        return jsonify({
            'success': True,
            'data': {
                'customers': customer_reports,
                'summary': {
                    'total_customers': len(customer_reports),
                    'total_revenue': sum(c['total_spent'] for c in customer_reports),
                    'average_customer_value': sum(c['total_spent'] for c in customer_reports) / len(customer_reports) if customer_reports else 0,
                    'high_value_customers': len([c for c in customer_reports if c.get('segment') == 'High Value']),
                    'medium_value_customers': len([c for c in customer_reports if c.get('segment') == 'Medium Value']),
                    'low_value_customers': len([c for c in customer_reports if c.get('segment') == 'Low Value'])
                },
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'sort_by': sort_by
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/reports/inventory', methods=['GET'])
def get_inventory_report():
    """Get inventory analysis report"""
    try:
        include_inactive = request.args.get('include_inactive', False, type=bool)
        category_id = request.args.get('category_id', type=int)
        
        query = Product.query
        if not include_inactive:
            query = query.filter(Product.is_active == True)
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        products = query.all()
        
        total_products = len(products)
        total_stock_value = sum(product.stock_quantity * product.cost_price for product in products)
        total_retail_value = sum(product.stock_quantity * product.price for product in products)
        potential_profit = total_retail_value - total_stock_value
        
        # Stock status analysis
        out_of_stock = [p for p in products if p.stock_quantity == 0]
        low_stock = [p for p in products if 0 < p.stock_quantity <= p.min_stock_level]
        normal_stock = [p for p in products if p.stock_quantity > p.min_stock_level]
        
        # Category breakdown
        category_breakdown = defaultdict(lambda: {
            'product_count': 0,
            'total_stock_value': 0,
            'total_retail_value': 0,
            'total_units': 0
        })
        
        for product in products:
            category_name = product.category.name if product.category else 'Uncategorized'
            category_breakdown[category_name]['product_count'] += 1
            category_breakdown[category_name]['total_stock_value'] += product.stock_quantity * product.cost_price
            category_breakdown[category_name]['total_retail_value'] += product.stock_quantity * product.price
            category_breakdown[category_name]['total_units'] += product.stock_quantity
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total_products': total_products,
                    'total_stock_value': total_stock_value,
                    'total_retail_value': total_retail_value,
                    'potential_profit': potential_profit,
                    'profit_margin': (potential_profit / total_retail_value * 100) if total_retail_value > 0 else 0
                },
                'stock_status': {
                    'out_of_stock_count': len(out_of_stock),
                    'low_stock_count': len(low_stock),
                    'normal_stock_count': len(normal_stock),
                    'out_of_stock_products': [p.to_dict() for p in out_of_stock[:10]],  # Limit to 10
                    'low_stock_products': [p.to_dict() for p in low_stock[:10]]  # Limit to 10
                },
                'category_breakdown': dict(category_breakdown),
                'top_value_products': sorted(
                    [
                        {
                            'name': p.name,
                            'sku': p.sku,
                            'stock_value': p.stock_quantity * p.cost_price,
                            'stock_quantity': p.stock_quantity
                        }
                        for p in products
                    ],
                    key=lambda x: x['stock_value'],
                    reverse=True
                )[:10]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/reports/financial', methods=['GET'])
def get_financial_report():
    """Get financial analysis report"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = datetime.utcnow().isoformat()
        
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # Sales data
        sales = Sale.query.filter(
            Sale.created_at >= start_dt,
            Sale.created_at <= end_dt
        ).all()
        
        # Purchase data
        purchases = Purchase.query.filter(
            Purchase.created_at >= start_dt,
            Purchase.created_at <= end_dt,
            Purchase.status == 'completed'
        ).all()
        
        # Calculate financial metrics
        total_revenue = sum(sale.total_amount for sale in sales)
        total_tax_collected = sum(sale.tax_amount for sale in sales)
        total_discounts_given = sum(sale.discount_amount for sale in sales)
        gross_sales = total_revenue + total_discounts_given
        
        total_cogs = 0  # Cost of Goods Sold
        for sale in sales:
            for item in sale.items:
                if item.product:
                    total_cogs += item.quantity * item.product.cost_price
        
        gross_profit = total_revenue - total_cogs
        gross_profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        total_purchase_cost = sum(purchase.total_amount for purchase in purchases)
        
        # Monthly breakdown
        monthly_data = defaultdict(lambda: {
            'revenue': 0,
            'cogs': 0,
            'purchases': 0,
            'profit': 0,
            'sales_count': 0
        })
        
        for sale in sales:
            month_key = sale.created_at.strftime('%Y-%m')
            monthly_data[month_key]['revenue'] += sale.total_amount
            monthly_data[month_key]['sales_count'] += 1
            
            # Calculate COGS for this sale
            sale_cogs = 0
            for item in sale.items:
                if item.product:
                    sale_cogs += item.quantity * item.product.cost_price
            monthly_data[month_key]['cogs'] += sale_cogs
            monthly_data[month_key]['profit'] += sale.total_amount - sale_cogs
        
        for purchase in purchases:
            month_key = purchase.created_at.strftime('%Y-%m')
            monthly_data[month_key]['purchases'] += purchase.total_amount
        
        # Convert to list and sort
        monthly_breakdown = [
            {
                'month': key,
                **values,
                'profit_margin': (values['profit'] / values['revenue'] * 100) if values['revenue'] > 0 else 0
            }
            for key, values in sorted(monthly_data.items())
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total_revenue': total_revenue,
                    'total_cogs': total_cogs,
                    'gross_profit': gross_profit,
                    'gross_profit_margin': gross_profit_margin,
                    'total_tax_collected': total_tax_collected,
                    'total_discounts_given': total_discounts_given,
                    'gross_sales': gross_sales,
                    'total_purchase_cost': total_purchase_cost,
                    'net_profit': gross_profit - total_purchase_cost
                },
                'monthly_breakdown': monthly_breakdown,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/reports/tax', methods=['GET'])
def get_tax_report():
    """Get tax collection report"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = datetime.utcnow().isoformat()
        
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # Get sales with tax data
        sales = Sale.query.filter(
            Sale.created_at >= start_dt,
            Sale.created_at <= end_dt
        ).all()
        
        total_tax_collected = sum(sale.tax_amount for sale in sales)
        total_taxable_amount = sum(sale.subtotal for sale in sales)
        
        # Daily tax breakdown
        daily_tax = defaultdict(lambda: {
            'tax_collected': 0,
            'taxable_amount': 0,
            'sales_count': 0
        })
        
        for sale in sales:
            day_key = sale.created_at.strftime('%Y-%m-%d')
            daily_tax[day_key]['tax_collected'] += sale.tax_amount
            daily_tax[day_key]['taxable_amount'] += sale.subtotal
            daily_tax[day_key]['sales_count'] += 1
        
        daily_breakdown = [
            {
                'date': key,
                **values,
                'average_tax_rate': (values['tax_collected'] / values['taxable_amount'] * 100) if values['taxable_amount'] > 0 else 0
            }
            for key, values in sorted(daily_tax.items())
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total_tax_collected': total_tax_collected,
                    'total_taxable_amount': total_taxable_amount,
                    'average_tax_rate': (total_tax_collected / total_taxable_amount * 100) if total_taxable_amount > 0 else 0,
                    'total_sales': len(sales)
                },
                'daily_breakdown': daily_breakdown,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/reports/profit-loss', methods=['GET'])
def get_profit_loss_report():
    """Get profit and loss statement"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = datetime.utcnow().isoformat()
        
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # Revenue
        sales = Sale.query.filter(
            Sale.created_at >= start_dt,
            Sale.created_at <= end_dt
        ).all()
        
        gross_revenue = sum(sale.total_amount for sale in sales)
        discounts = sum(sale.discount_amount for sale in sales)
        net_revenue = gross_revenue - discounts
        
        # Cost of Goods Sold
        total_cogs = 0
        for sale in sales:
            for item in sale.items:
                if item.product:
                    total_cogs += item.quantity * item.product.cost_price
        
        gross_profit = net_revenue - total_cogs
        
        # Operating Expenses (simplified - could be expanded)
        # For now, we'll use purchase costs as operating expenses
        purchases = Purchase.query.filter(
            Purchase.created_at >= start_dt,
            Purchase.created_at <= end_dt,
            Purchase.status == 'completed'
        ).all()
        
        operating_expenses = sum(purchase.total_amount for purchase in purchases)
        
        # Net Profit
        net_profit = gross_profit - operating_expenses
        
        return jsonify({
            'success': True,
            'data': {
                'revenue': {
                    'gross_revenue': gross_revenue,
                    'discounts': discounts,
                    'net_revenue': net_revenue
                },
                'costs': {
                    'cost_of_goods_sold': total_cogs,
                    'operating_expenses': operating_expenses,
                    'total_costs': total_cogs + operating_expenses
                },
                'profit': {
                    'gross_profit': gross_profit,
                    'gross_profit_margin': (gross_profit / net_revenue * 100) if net_revenue > 0 else 0,
                    'net_profit': net_profit,
                    'net_profit_margin': (net_profit / net_revenue * 100) if net_revenue > 0 else 0
                },
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/reports/top-performers', methods=['GET'])
def get_top_performers():
    """Get top performing products, customers, and categories"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 10, type=int)
        
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = datetime.utcnow().isoformat()
        
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # Top products by revenue
        top_products_revenue = db.session.query(
            Product.name,
            Product.sku,
            func.sum(SaleItem.total_price).label('total_revenue'),
            func.sum(SaleItem.quantity).label('total_sold')
        ).join(SaleItem).join(Sale).filter(
            Sale.created_at >= start_dt,
            Sale.created_at <= end_dt
        ).group_by(Product.id).order_by(desc('total_revenue')).limit(limit).all()
        
        # Top products by quantity
        top_products_quantity = db.session.query(
            Product.name,
            Product.sku,
            func.sum(SaleItem.quantity).label('total_sold'),
            func.sum(SaleItem.total_price).label('total_revenue')
        ).join(SaleItem).join(Sale).filter(
            Sale.created_at >= start_dt,
            Sale.created_at <= end_dt
        ).group_by(Product.id).order_by(desc('total_sold')).limit(limit).all()
        
        # Top customers
        top_customers = db.session.query(
            Customer.name,
            Customer.email,
            func.sum(Sale.total_amount).label('total_spent'),
            func.count(Sale.id).label('total_orders')
        ).join(Sale).filter(
            Sale.created_at >= start_dt,
            Sale.created_at <= end_dt
        ).group_by(Customer.id).order_by(desc('total_spent')).limit(limit).all()
        
        # Top categories
        top_categories = db.session.query(
            Category.name,
            func.sum(SaleItem.total_price).label('total_revenue'),
            func.sum(SaleItem.quantity).label('total_sold')
        ).join(Product).join(SaleItem).join(Sale).filter(
            Sale.created_at >= start_dt,
            Sale.created_at <= end_dt
        ).group_by(Category.id).order_by(desc('total_revenue')).limit(limit).all()
        
        return jsonify({
            'success': True,
            'data': {
                'top_products_by_revenue': [
                    {
                        'name': p.name,
                        'sku': p.sku,
                        'revenue': p.total_revenue,
                        'quantity_sold': p.total_sold
                    } for p in top_products_revenue
                ],
                'top_products_by_quantity': [
                    {
                        'name': p.name,
                        'sku': p.sku,
                        'quantity_sold': p.total_sold,
                        'revenue': p.total_revenue
                    } for p in top_products_quantity
                ],
                'top_customers': [
                    {
                        'name': c.name,
                        'email': c.email,
                        'total_spent': c.total_spent,
                        'total_orders': c.total_orders,
                        'average_order_value': c.total_spent / c.total_orders if c.total_orders > 0 else 0
                    } for c in top_customers
                ],
                'top_categories': [
                    {
                        'name': c.name,
                        'revenue': c.total_revenue,
                        'quantity_sold': c.total_sold
                    } for c in top_categories
                ],
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'limit': limit
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/reports/export', methods=['POST'])
def export_report():
    """Export report data (placeholder for future CSV/PDF export functionality)"""
    try:
        data = request.get_json()
        report_type = data.get('report_type')
        format_type = data.get('format', 'json')  # json, csv, pdf
        
        # This is a placeholder - in a real implementation, you would:
        # 1. Generate the requested report
        # 2. Format it according to the requested format
        # 3. Return a download link or the formatted data
        
        return jsonify({
            'success': True,
            'message': f'Export functionality for {report_type} in {format_type} format is not yet implemented',
            'data': {
                'report_type': report_type,
                'format': format_type,
                'status': 'pending'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500        
