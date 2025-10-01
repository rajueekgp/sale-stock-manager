"""
Database Setup Script for POS System
Creates pos_system.db with sample data
"""

import sqlite3
from datetime import datetime, timedelta
import random
import uuid

def create_database():
    """Create the database and all tables"""
    conn = sqlite3.connect('pos_system.db')
    cursor = conn.cursor()
    
    # Create Categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            cost_price REAL DEFAULT 0.0,
            stock_quantity INTEGER DEFAULT 0,
            min_stock_level INTEGER DEFAULT 5,
            sku VARCHAR(50) UNIQUE NOT NULL,
            barcode VARCHAR(100),
            category_id INTEGER NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            batch_management_enabled BOOLEAN DEFAULT 0 NOT NULL,
            gst_rate REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    ''')
    
    # Create Product Batches table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            batch_number VARCHAR(100) NOT NULL,
            stock_quantity INTEGER DEFAULT 0,
            barcode VARCHAR(100),
            purchase_price REAL,
            sale_price REAL,
            gst_rate REAL,
            expiry_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id),
            UNIQUE (product_id, batch_number)
        )
    ''')
    
    # Create Customers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(200) NOT NULL,
            email VARCHAR(120) UNIQUE,
            phone VARCHAR(20),
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Sales table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_number VARCHAR(50) UNIQUE NOT NULL,
            customer_id INTEGER,
            subtotal REAL NOT NULL,
            tax_amount REAL DEFAULT 0.0,
            discount_amount REAL DEFAULT 0.0,
            total_amount REAL NOT NULL,
            payment_method VARCHAR(50) DEFAULT 'cash',
            status VARCHAR(20) DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    
    # Create Sale Items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            batch_id INTEGER,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales (id),
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (batch_id) REFERENCES product_batches (id)
        )
    ''')
    
    # Create Purchases table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_number VARCHAR(50) UNIQUE NOT NULL,
            supplier_name VARCHAR(200) NOT NULL,
            total_amount REAL NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Purchase Items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchase_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            batch_id INTEGER,
            quantity INTEGER NOT NULL,
            unit_cost REAL NOT NULL,
            total_cost REAL NOT NULL,
            FOREIGN KEY (purchase_id) REFERENCES purchases (id),
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (batch_id) REFERENCES product_batches (id)
        )
    ''')
    
    conn.commit()
    return conn

def insert_sample_data(conn):
    """Insert sample data into all tables"""
    cursor = conn.cursor()
    
    print("Inserting sample data...")
    
    # Insert Categories
    categories = [
        ('Electronics', 'Electronic devices and accessories'),
        ('Clothing', 'Clothing and fashion accessories'),
        ('Food & Beverages', 'Food items and beverages'),
        ('Books & Media', 'Books, magazines, and media'),
        ('Home & Garden', 'Home improvement and garden supplies'),
        ('Sports & Outdoors', 'Sports equipment and outdoor gear'),
        ('Health & Beauty', 'Health and beauty products'),
        ('Toys & Games', 'Toys and gaming products')
    ]
    
    cursor.executemany(
        'INSERT INTO categories (name, description) VALUES (?, ?)',
        categories
    )
    
    # Insert Products
    products = [
        # Electronics
        ('Laptop Computer', 'High-performance laptop for work and gaming', 999.99, 750.00, 15, 5, 'LAP001', '1234567890123', 1, 1),
        ('Smartphone', 'Latest model smartphone with advanced features', 699.99, 500.00, 25, 10, 'PHN001', '1234567890124', 1, 1),
        ('Wireless Headphones', 'Noise-cancelling wireless headphones', 199.99, 120.00, 30, 15, 'HDP001', '1234567890125', 1, 1),
        ('Tablet', '10-inch tablet with high-resolution display', 399.99, 280.00, 20, 8, 'TAB001', '1234567890126', 1, 1),
        ('Smart Watch', 'Fitness tracking smartwatch', 299.99, 180.00, 35, 12, 'WAT001', '1234567890127', 1, 1),
        
        # Clothing
        ('T-Shirt', 'Cotton crew neck t-shirt', 19.99, 8.00, 100, 20, 'TSH001', '2234567890123', 2, 1),
        ('Jeans', 'Classic blue denim jeans', 59.99, 25.00, 50, 15, 'JNS001', '2234567890124', 2, 1),
        ('Sneakers', 'Comfortable running sneakers', 89.99, 45.00, 40, 12, 'SNK001', '2234567890125', 2, 1),
        ('Jacket', 'Waterproof outdoor jacket', 129.99, 65.00, 25, 8, 'JCK001', '2234567890126', 2, 1),
        ('Cap', 'Baseball cap with adjustable strap', 24.99, 10.00, 75, 20, 'CAP001', '2234567890127', 2, 1),
        
        # Food & Beverages
        ('Coffee Beans', 'Premium arabica coffee beans', 12.99, 6.00, 200, 50, 'COF001', '3234567890123', 3, 1),
        ('Energy Drink', 'High-caffeine energy drink', 2.99, 1.20, 150, 30, 'ENR001', '3234567890124', 3, 1),
        ('Chocolate Bar', 'Dark chocolate bar 70% cocoa', 4.99, 2.00, 100, 25, 'CHO001', '3234567890125', 3, 1),
        ('Protein Powder', 'Whey protein powder supplement', 49.99, 25.00, 30, 10, 'PRO001', '3234567890126', 3, 1),
        ('Green Tea', 'Organic green tea bags', 8.99, 4.00, 80, 20, 'TEA001', '3234567890127', 3, 1),
        
        # Books & Media
        ('Programming Book', 'Learn Python programming', 39.99, 20.00, 25, 5, 'BOK001', '4234567890123', 4, 1),
        ('Magazine', 'Monthly tech magazine', 5.99, 2.50, 50, 15, 'MAG001', '4234567890124', 4, 1),
        ('DVD Movie', 'Latest blockbuster movie', 14.99, 8.00, 40, 10, 'DVD001', '4234567890125', 4, 1),
        ('Board Game', 'Strategy board game for family', 34.99, 18.00, 20, 5, 'GAM001', '4234567890126', 4, 1),
        ('Notebook', 'Lined notebook for writing', 7.99, 3.00, 60, 15, 'NOT001', '4234567890127', 4, 1),
        
        # Home & Garden
        ('Plant Pot', 'Ceramic plant pot with drainage', 15.99, 7.00, 45, 12, 'POT001', '5234567890123', 5, 1),
        ('LED Bulb', 'Energy-efficient LED light bulb', 9.99, 4.50, 100, 25, 'BUL001', '5234567890124', 5, 1),
        ('Garden Tool Set', 'Complete gardening tool set', 79.99, 40.00, 15, 5, 'TOL001', '5234567890125', 5, 1),
        ('Candle', 'Scented aromatherapy candle', 12.99, 5.00, 70, 20, 'CAN001', '5234567890126', 5, 1),
        ('Picture Frame', 'Wooden picture frame 8x10', 18.99, 8.00, 35, 10, 'FRM001', '5234567890127', 5, 1)
    ]
    
    cursor.executemany('''
        INSERT INTO products (name, description, price, cost_price, stock_quantity, 
                            min_stock_level, sku, barcode, category_id, is_active) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', products)
    
    # Insert Customers
    customers = [
        ('John Smith', 'john.smith@email.com', '555-0101', '123 Main St, City, State 12345'),
        ('Jane Doe', 'jane.doe@email.com', '555-0102', '456 Oak Ave, City, State 12346'),
        ('Mike Johnson', 'mike.johnson@email.com', '555-0103', '789 Pine Rd, City, State 12347'),
        ('Sarah Wilson', 'sarah.wilson@email.com', '555-0104', '321 Elm St, City, State 12348'),
        ('David Brown', 'david.brown@email.com', '555-0105', '654 Maple Dr, City, State 12349'),
        ('Lisa Davis', 'lisa.davis@email.com', '555-0106', '987 Cedar Ln, City, State 12350'),
        ('Tom Miller', 'tom.miller@email.com', '555-0107', '147 Birch Way, City, State 12351'),
        ('Amy Garcia', 'amy.garcia@email.com', '555-0108', '258 Spruce St, City, State 12352'),
        ('Chris Martinez', 'chris.martinez@email.com', '555-0109', '369 Willow Ave, City, State 12353'),
        ('Emma Taylor', 'emma.taylor@email.com', '555-0110', '741 Poplar Rd, City, State 12354')
    ]
    
    cursor.executemany(
        'INSERT INTO customers (name, email, phone, address) VALUES (?, ?, ?, ?)',
        customers
    )
    
    # Generate sample sales data
    print("Generating sample sales...")
    
    # Get product IDs and prices
    cursor.execute('SELECT id, price, cost_price FROM products WHERE is_active = 1')
    products_data = cursor.fetchall()
    
    # Get customer IDs
    cursor.execute('SELECT id FROM customers')
    customer_ids = [row[0] for row in cursor.fetchall()]
    
    # Generate sales for the last 90 days
    start_date = datetime.now() - timedelta(days=90)
    
    for day in range(90):
        current_date = start_date + timedelta(days=day)
        
        # Generate 3-8 sales per day
        daily_sales = random.randint(3, 8)
        
        for _ in range(daily_sales):
            # Generate sale
            sale_number = f"SALE-{current_date.strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            customer_id = random.choice(customer_ids) if random.random() > 0.3 else None  # 70% have customers
            
            # Generate 1-5 items per sale
            num_items = random.randint(1, 5)
            selected_products = random.sample(products_data, min(num_items, len(products_data)))
            
            subtotal = 0
            sale_items = []
            
            for product_id, price, cost_price in selected_products:
                quantity = random.randint(1, 3)
                unit_price = price
                total_price = unit_price * quantity
                subtotal += total_price
                
                sale_items.append((product_id, quantity, unit_price, total_price))
            
            # Calculate tax and discount
            tax_rate = 0.08  # 8% tax
            discount_amount = subtotal * random.uniform(0, 0.1) if random.random() > 0.7 else 0  # 30% chance of discount
            tax_amount = (subtotal - discount_amount) * tax_rate
            total_amount = subtotal + tax_amount - discount_amount
            
            payment_method = random.choice(['cash', 'card', 'mobile_payment'])
            
            # Add some random hours/minutes to the date
            sale_datetime = current_date + timedelta(
                hours=random.randint(9, 20),
                minutes=random.randint(0, 59)
            )
            
            # Insert sale
            cursor.execute('''
                INSERT INTO sales (sale_number, customer_id, subtotal, tax_amount, 
                                 discount_amount, total_amount, payment_method, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (sale_number, customer_id, subtotal, tax_amount, discount_amount, 
                  total_amount, payment_method, 'completed', sale_datetime))
            
            sale_id = cursor.lastrowid
            
            # Insert sale items
            for product_id, quantity, unit_price, total_price in sale_items:
                cursor.execute('''
                    INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?)
                ''', (sale_id, product_id, quantity, unit_price, total_price))
    
    # Insert sample purchases
    print("Generating sample purchases...")
    
    suppliers = ['Tech Supplier Inc', 'Fashion Wholesale', 'Food Distributors LLC', 
                'Book Publishers', 'Home Goods Supply', 'Sports Equipment Co']
    
    for i in range(20):  # 20 sample purchases
        purchase_date = start_date + timedelta(days=random.randint(0, 89))
        purchase_number = f"PUR-{purchase_date.strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        supplier = random.choice(suppliers)
        
        # Select 2-6 products for purchase
        num_items = random.randint(2, 6)
        selected_products = random.sample(products_data, min(num_items, len(products_data)))
        
        total_amount = 0
        purchase_items = []
        
        for product_id, price, cost_price in selected_products:
            quantity = random.randint(10, 50)  # Bulk purchase
            unit_cost = cost_price
            total_cost = unit_cost * quantity
            total_amount += total_cost
            
            purchase_items.append((product_id, quantity, unit_cost, total_cost))
        
        status = random.choice(['completed', 'pending'])
        
        # Insert purchase
        cursor.execute('''
            INSERT INTO purchases (purchase_number, supplier_name, total_amount, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (purchase_number, supplier, total_amount, status, purchase_date))
        
        purchase_id = cursor.lastrowid
        
        # Insert purchase items
        for product_id, quantity, unit_cost, total_cost in purchase_items:
            cursor.execute('''
                INSERT INTO purchase_items (purchase_id, product_id, quantity, unit_cost, total_cost, batch_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (purchase_id, product_id, quantity, unit_cost, total_cost, None))
    
    conn.commit()
    print("Sample data inserted successfully!")


def create_and_insert():
    """Main function to create database and insert sample data"""
     # Create database and tables
    print("Creating POS System Database...")
    conn = create_database()
    print("Database and tables created successfully!")
    
    # Insert sample data
    insert_sample_data(conn)
    print("Mock Data inserted into tables successfully!")
    conn.close()
    print(f"\nDatabase 'pos_system.db' created successfully!")
        

def main():
    try:
        # Connect to your SQLite database
        conn = sqlite3.connect('pos_system.db')
        cursor = conn.cursor()
        
        ##########################################
        # # Add the new column with FLOAT type and default value 0.0
        # cursor.execute('''
        #     ALTER TABLE customers
        #     ADD COLUMN store_credit FLOAT DEFAULT 0.0
        # ''')

        # # Optional: Ensure all existing rows have store_credit set to 0.0
        # cursor.execute('''
        #     UPDATE customers
        #     SET store_credit = 0.0
        #     WHERE store_credit IS NULL
        # ''')
        
        # # Add the new column 'opening_balance' to the 'customers' table
        # cursor.execute("ALTER TABLE customers ADD COLUMN opening_balance FLOAT DEFAULT 0.0")
        
        # # Commit changes and close connection
        # conn.commit()
        ##########################################

        # Verify data insertion
        cursor.execute('SELECT COUNT(*) FROM categories')
        categories_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM products')
        products_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM customers')
        customers_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sales')
        sales_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM purchases')
        purchases_count = cursor.fetchone()[0]
        
        print(f"\nDatabase Summary:")
        print(f"Categories: {categories_count}")
        print(f"Products: {products_count}")
        print(f"Customers: {customers_count}")
        print(f"Sales: {sales_count}")
        print(f"Purchases: {purchases_count}")
        
    except Exception as e:
        print(f"Error creating database: {e}")

if __name__ == "__main__":
    # create_and_insert()
    main()