# check_schema.py
import sqlite3

conn = sqlite3.connect('instance/bookstore.db')
cursor = conn.cursor()

print("📊 Checking 'admins' table schema...")
try:
    schema = cursor.execute("PRAGMA table_info(admins)").fetchall()
    
    if schema:
        print("\n✅ Admins table exists with columns:")
        for col in schema:
            print(f"   - {col[1]} ({col[2]})")
    else:
        print("\n❌ Admins table doesn't exist!")
        
except sqlite3.OperationalError:
    print("\n❌ Admins table doesn't exist!")

print("\n📊 Checking 'users' table schema...")
try:
    schema = cursor.execute("PRAGMA table_info(users)").fetchall()
    
    if schema:
        print("\n✅ Users table exists with columns:")
        for col in schema:
            print(f"   - {col[1]} ({col[2]})")
    else:
        print("\n❌ Users table doesn't exist!")
        
except sqlite3.OperationalError:
    print("\n❌ Users table doesn't exist!")
    
print("\n📊 Checking 'books' table schema...")
try:
    schema = cursor.execute("PRAGMA table_info(books)").fetchall()
    
    if schema:
        print("\n✅ Books table exists with columns:")
        for col in schema:
            print(f"   - {col[1]} ({col[2]})")
    else:
        print("\n❌ Books table doesn't exist!")
        
except sqlite3.OperationalError:
    print("\n❌ Books table doesn't exist!")

conn.close()
