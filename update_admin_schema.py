import sqlite3
from werkzeug.security import generate_password_hash

def migrate_admin_table():
    db_path = 'instance/bookstore.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("1. Dropping old admins table...")
        cursor.execute('DROP TABLE IF EXISTS admins')
        
        print("2. Creating new admins table with full_name and email...")
        cursor.execute('''
        CREATE TABLE admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
        ''')
        
        print("3. Re-creating index...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_admins_username ON admins(username)')
        
        print("4. Creating default admin user...")
        admin_password = generate_password_hash('admin123')
        cursor.execute(
            'INSERT INTO admins (username, email, password_hash, full_name) VALUES (?, ?, ?, ?)',
            ('admin', 'admin@bookstore.com', admin_password, 'System Administrator')
        )
        
        conn.commit()
        print("✅ Admin schema updated successfully!")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    migrate_admin_table()
