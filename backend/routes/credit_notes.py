
from flask import Blueprint, jsonify

credit_notes_bp = Blueprint('credit_notes', __name__)

@credit_notes_bp.route('/credit-notes', methods=['GET'])
def get_credit_notes():
    """Get all credit notes"""
    # In a real implementation, you would query the database.
    # from models import CreditNote
    # credit_notes = CreditNote.query.all()
    # data = [cn.to_dict() for cn in credit_notes]
    return jsonify({'success': True, 'data': []})