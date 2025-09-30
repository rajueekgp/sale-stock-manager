
from flask import Blueprint, request, jsonify
from database import db
from models import Category, Product
from sqlalchemy import func

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all categories with their product counts"""
    try:
        # Query categories and join with products to get counts efficiently
        categories_with_counts = db.session.query(
            Category, func.count(Product.id).label('product_count')
        ).outerjoin(Product, Category.id == Product.category_id).group_by(Category.id).order_by(Category.name).all()

        categories_list = []
        for category, product_count in categories_with_counts:
            # Use the to_dict() method from the model and update the product_count
            cat_dict = category.to_dict()
            cat_dict['product_count'] = product_count
            categories_list.append(cat_dict)

        return jsonify({
            'success': True,
            'data': categories_list
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@categories_bp.route('/categories/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """Get a single category by its ID"""
    try:
        category = Category.query.get_or_404(category_id)
        return jsonify({
            'success': True,
            'data': category.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@categories_bp.route('/categories', methods=['POST'])
def create_category():
    """Create a new category"""
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({'success': False, 'error': 'Category name is required'}), 400
        
        name = data['name'].strip()
        
        # Check if category name already exists (case-insensitive)
        existing_category = Category.query.filter(func.lower(Category.name) == func.lower(name)).first()
        if existing_category:
            return jsonify({
                'success': False, 
                'error': 'A category with this name already exists.'
            }), 409 # 409 Conflict is suitable here
        
        new_category = Category(
            name=name,
            description=data.get('description', '').strip()
        )
        
        db.session.add(new_category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': new_category.to_dict(),
            'message': 'Category created successfully.'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@categories_bp.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """Update an existing category"""
    try:
        category = Category.query.get_or_404(category_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No update data provided.'}), 400
            
        if 'name' in data:
            name = data['name'].strip()
            if name.lower() != category.name.lower():
                # Check if the new name already exists in another category
                existing_category = Category.query.filter(func.lower(Category.name) == func.lower(name)).first()
                if existing_category:
                    return jsonify({
                        'success': False, 
                        'error': 'A category with this name already exists.'
                    }), 409
                category.name = name
        
        if 'description' in data:
            category.description = data.get('description', '').strip()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': category.to_dict(),
            'message': 'Category updated successfully.'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@categories_bp.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Delete a category"""
    try:
        category = Category.query.get_or_404(category_id)
        
        # Prevent deletion if the category is associated with any products
        if category.products:
            return jsonify({
                'success': False, 
                'error': f'Cannot delete category. It is associated with {len(category.products)} product(s).'
            }), 400
        
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Category deleted successfully.'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
