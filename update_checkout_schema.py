import sqlite3
import os

def migrate_checkout_tables():
    db_path = 'instance/bookstore.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("1. Creating orders table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            guest_email TEXT,
            guest_name TEXT,
            guest_phone TEXT,
            subtotal REAL NOT NULL,
            discount REAL DEFAULT 0,
            shipping REAL DEFAULT 0,
            tax REAL NOT NULL,
            total REAL NOT NULL,
            coupon_code TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        ''')
        
        print("2. Creating order_items table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL,
            isbn13 TEXT NOT NULL,
            title TEXT NOT NULL,
            author TEXT,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (isbn13) REFERENCES books(isbn13)
        );
        ''')
        
        print("3. Creating delivery_addresses table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS delivery_addresses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address_line1 TEXT NOT NULL,
            address_line2 TEXT,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            pincode TEXT NOT NULL,
            landmark TEXT,
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
        );
        ''')
        
        conn.commit()
        print("✅ Checkout tables created successfully!")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    migrate_checkout_tables()
