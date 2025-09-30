from flask import Blueprint, jsonify
from database import db
from sqlalchemy import inspect, text

database_viewer_bp = Blueprint('database_viewer', __name__)

@database_viewer_bp.route('/database/tables', methods=['GET'])
def get_all_tables_data():
    """
    Dynamically fetches all columns and rows from every table in the database.
    """
    try:
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        
        all_tables_data = {}
        
        for table_name in table_names:
            # Skip internal sqlite tables
            if table_name.startswith('sqlite_'):
                continue
            
            # Using raw SQL for simplicity and to avoid model dependency
            query = text(f"SELECT * FROM {table_name} LIMIT 500") # Limit to 500 rows per table for performance
            result_proxy = db.session.execute(query)
            
            columns = list(result_proxy.keys())
            rows = [dict(row) for row in result_proxy.mappings()]
            
            all_tables_data[table_name] = {
                'columns': columns,
                'rows': rows
            }
            
        return jsonify({'success': True, 'data': all_tables_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500