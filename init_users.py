import sqlite3
from werkzeug.security import generate_password_hash

def init_users_database():
    """Initialize users tables and create default admin."""
    conn = sqlite3.connect('instance/bookstore.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'customer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Create admins table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Create default admin if not exists
    try:
        admin_password = generate_password_hash('admin123')
        cursor.execute(
            'INSERT INTO admins (username, email, password_hash, full_name) VALUES (?, ?, ?, ?)',
            ('admin', 'admin@bookstore.com', admin_password, 'System Administrator')
        )
        print("✅ Default admin created (username: admin, email: admin@bookstore.com, password: admin123)")
    except sqlite3.IntegrityError:
        print("ℹ️  Default admin already exists")
    
    conn.commit()
    conn.close()
    print("✅ Users database initialized successfully!")

if __name__ == '__main__':
    init_users_database()
