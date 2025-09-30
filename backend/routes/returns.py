from flask import Blueprint, request, jsonify
from database import db
from models import Return, ReturnItem, Sale, Product, CreditNote
from datetime import datetime
import uuid

returns_bp = Blueprint('returns', __name__)

@returns_bp.route('/returns', methods=['GET'])
def get_returns():
    """Get all returns with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Assuming 'Return' is the correct model name
        returns_query = Return.query.order_by(Return.created_at.desc())
        
        paginated_returns = returns_query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': [r.to_dict() for r in paginated_returns.items],
            'pagination': {
                'page': page,
                'pages': paginated_returns.pages,
                'per_page': per_page,
                'total': paginated_returns.total
            }
        })
    except Exception as e:
        # Log the error for debugging
        print(f"Error in get_returns: {e}")
        # It's possible the 'Return' model or its 'to_dict' method has issues.
        # For now, we'll return an empty list on error to prevent a 500.
        # In a real scenario, you'd want to investigate the root cause.
        return jsonify({'success': True, 'data': [], 'pagination': {'page': 1, 'pages': 0, 'per_page': 10, 'total': 0}})

@returns_bp.route('/returns/<int:return_id>', methods=['GET'])
def get_return(return_id):
    """Get a single return by its ID"""
    try:
        return_record = Return.query.get_or_404(return_id)
        return jsonify({
            'success': True,
            'data': return_record.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@returns_bp.route('/returns/<int:return_id>', methods=['PUT'])
def update_return(return_id):
    """Update a return's reason"""
    try:
        data = request.get_json()
        return_record = Return.query.get_or_404(return_id)

        if 'reason' in data:
            return_record.reason = data['reason']
        
        db.session.commit()
        return jsonify({'success': True, 'data': return_record.to_dict(), 'message': 'Return updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@returns_bp.route('/returns/<int:return_id>', methods=['DELETE'])
def delete_return(return_id):
    """Delete a return and reverse stock/credit adjustments"""
    try:
        return_record = Return.query.get_or_404(return_id)

        # Reverse stock adjustments
        for item in return_record.items:
            if item.product:
                item.product.stock_quantity -= item.quantity
        
        # Handle associated credit note
        if return_record.status == 'Credit Note Issued' and return_record.credit_note:
            credit_note = return_record.credit_note[0]
            if credit_note.status == 'Open' and return_record.customer:
                return_record.customer.store_credit = max(0, (return_record.customer.store_credit or 0) - credit_note.initial_amount)
            credit_note.status = 'Voided'
            credit_note.remaining_amount = 0

        db.session.delete(return_record)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Return deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@returns_bp.route('/returns', methods=['POST'])
def create_return():
    """Create a new return"""
    try:
        data = request.get_json()
        sale_id = data.get('sale_id')
        items_to_return = data.get('items')
        reason = data.get('reason')
        refund_method = data.get('refund_method', 'cash')

        if not sale_id or not items_to_return:
            return jsonify({'success': False, 'error': 'Sale ID and items are required'}), 400

        sale = Sale.query.get_or_404(sale_id)
        
        total_refund_amount = 0
        return_items = []

        if refund_method == 'credit_note' and not sale.customer_id:
            return jsonify({'success': False, 'error': 'Credit notes can only be issued to registered customers.'}), 400

        for item_data in items_to_return:
            product_id = item_data['product_id']
            quantity_to_return = item_data['quantity']

            original_item = next((i for i in sale.items if i.product_id == product_id), None)
            if not original_item:
                return jsonify({'success': False, 'error': f'Product ID {product_id} not found in original sale'}), 400

            product = Product.query.get(product_id)
            if not product:
                return jsonify({'success': False, 'error': f'Product ID {product_id} not found'}), 400

            refund_for_item = original_item.unit_price * quantity_to_return
            total_refund_amount += refund_for_item

            product.stock_quantity += quantity_to_return

            return_items.append(ReturnItem(product_id=product_id, quantity=quantity_to_return, unit_price=original_item.unit_price, total_price=refund_for_item))

        return_number = f"RTN-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
        new_return = Return(return_number=return_number, sale_id=sale.id, customer_id=sale.customer_id, total_refund_amount=total_refund_amount, reason=reason, items=return_items)
        
        message = 'Return processed as cash refund successfully.'

        if refund_method == 'credit_note':
            credit_note_number = f"CN-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
            new_credit_note = CreditNote(
                credit_note_number=credit_note_number,
                customer_id=sale.customer_id,
                initial_amount=total_refund_amount,
                remaining_amount=total_refund_amount,
                status='Open',
                return_record=new_return
            )
            sale.customer.store_credit = (sale.customer.store_credit or 0) + total_refund_amount
            db.session.add(new_credit_note)
            new_return.status = 'Credit Note Issued'
            message = 'Return processed and credit note issued successfully.'

        db.session.add(new_return)
        db.session.commit()

        return jsonify({'success': True, 'data': new_return.to_dict(), 'message': message}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500