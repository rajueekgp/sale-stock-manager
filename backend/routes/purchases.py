
from flask import Blueprint, request, jsonify
from database import db
from models import Purchase, PurchaseItem, Product
from sqlalchemy import func, desc
import uuid
from datetime import datetime

purchases_bp = Blueprint('purchases', __name__)

@purchases_bp.route('/purchases', methods=['GET'])
def get_purchases():
    """Get all purchase orders"""
    try:
        purchases = Purchase.query.order_by(desc(Purchase.created_at)).all()
        return jsonify({
            'success': True,
            'data': [p.to_dict() for p in purchases]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@purchases_bp.route('/purchases', methods=['POST'])
def create_purchase():
    """Create a new purchase order"""
    try:
        data = request.get_json()

        if not data or not data.get('supplier_name') or not data.get('items'):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        purchase_number = f"PUR-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

        new_purchase = Purchase(
            purchase_number=purchase_number,
            supplier_name=data['supplier_name'],
            total_amount=data['total_amount'],
            status=data.get('status', 'Pending')
        )
        db.session.add(new_purchase)
        db.session.flush() # To get the new_purchase.id

        for item_data in data['items']:
            product = Product.query.get(item_data['product_id'])
            if not product:
                db.session.rollback()
                return jsonify({'success': False, 'error': f"Product with ID {item_data['product_id']} not found"}), 404

            purchase_item = PurchaseItem(
                purchase_id=new_purchase.id,
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                unit_cost=item_data['unit_cost'],
                total_cost=item_data['quantity'] * item_data['unit_cost']
            )
            db.session.add(purchase_item)

            # If purchase is received, update stock
            if new_purchase.status.lower() in ['received', 'completed']:
                product.stock_quantity += item_data['quantity']

        db.session.commit()
        return jsonify({
            'success': True,
            'data': new_purchase.to_dict(),
            'message': 'Purchase order created successfully.'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500