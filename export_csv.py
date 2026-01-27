#!/usr/bin/env python3
"""
Export SQLite data to DynamoDB-compatible CSV format.
Schema-consistent with actual database structure.
"""

import sqlite3
import csv
import os

SQLITE_DB = 'instance/bookstore.db'
conn = sqlite3.connect(SQLITE_DB)
conn.row_factory = sqlite3.Row

def export_books():
    """Export books table to CSV - matching actual schema."""
    print("📚 Exporting books...")
    
    cursor = conn.execute('SELECT * FROM books')
    
    with open('export/books.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header - matching actual schema
        writer.writerow([
            'isbn13', 'isbn10', 'title', 'subtitle', 'authors',
            'categories', 'thumbnail', 'description', 'published_year',
            'average_rating', 'num_pages', 'ratings_count', 'price',
            'stock'
        ])
        
        # Write data
        count = 0
        for row in cursor.fetchall():
            writer.writerow([
                row['isbn13'],
                row['isbn10'] or '',
                row['title'],
                row['subtitle'] or '',
                row['authors'] or '',
                row['categories'] or '',
                row['thumbnail'] or '',
                (row['description'] or '').replace('\n', ' ').replace('\r', '').replace('"', '""'),
                float(row['published_year']) if row['published_year'] else 0.0,
                float(row['average_rating']) if row['average_rating'] else 0.0,
                float(row['num_pages']) if row['num_pages'] else 0.0,
                float(row['ratings_count']) if row['ratings_count'] else 0.0,
                float(row['price']) if row['price'] else 0.0,
                int(row['stock']) if row['stock'] else 10,
            ])
            count += 1
    
    print(f"✅ Exported {count} books to export/books.csv")
    return count

def export_users():
    """Export users table to CSV."""
    print("👥 Exporting users...")
    
    cursor = conn.execute('SELECT * FROM users')
    
    with open('export/users.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        writer.writerow([
             'username', 'email', 'password_hash',
            'full_name', 'role', 'created_at', 'last_login'
        ])
        
        count = 0
        for row in cursor.fetchall():
            writer.writerow([
                row['username'],
                row['email'],
                row['password_hash'],
                row['full_name'] or '',
                row['role'] or 'customer',
                str(row['created_at']) if row['created_at'] else '',
                str(row['last_login']) if row['last_login'] else ''
            ])
            count += 1
    
    print(f"✅ Exported {count} users to export/users.csv")
    return count

def export_admins():
    """Export admins table to CSV."""
    print("👨‍💼 Exporting admins...")
    
    cursor = conn.execute('SELECT * FROM admins')
    
    with open('export/admins.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        writer.writerow([
            'id', 'username', 'email', 'password_hash',
            'full_name', 'created_at', 'last_login'
        ])
        
        count = 0
        for row in cursor.fetchall():
            writer.writerow([
                int(row['id']),
                row['username'],
                row['email'] or '',
                row['password_hash'],
                row['full_name'] or '',
                str(row['created_at']) if row['created_at'] else '',
                str(row['last_login']) if row['last_login'] else ''
            ])
            count += 1
    
    print(f"✅ Exported {count} admins to export/admins.csv")
    return count

def export_orders():
    """Export orders table to CSV."""
    print("🛒 Exporting orders...")
    
    cursor = conn.execute('SELECT * FROM orders')
    
    with open('export/orders.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        writer.writerow([
            'id', 'order_id', 'user_id', 'guest_email', 'guest_name', 'guest_phone',
            'subtotal', 'discount', 'shipping', 'tax', 'total',
            'coupon_code', 'status', 'created_at'
        ])
        
        count = 0
        for row in cursor.fetchall():
            writer.writerow([
                int(row['id']),
                row['order_id'],
                int(row['user_id']) if row['user_id'] else 0,
                row['guest_email'] or '',
                row['guest_name'] or '',
                row['guest_phone'] or '',
                float(row['subtotal']) if row['subtotal'] else 0.0,
                float(row['discount']) if row['discount'] else 0.0,
                float(row['shipping']) if row['shipping'] else 0.0,
                float(row['tax']) if row['tax'] else 0.0,
                float(row['total']) if row['total'] else 0.0,
                row['coupon_code'] or '',
                row['status'] or 'pending',
                str(row['created_at']) if row['created_at'] else ''
            ])
            count += 1
    
    print(f"✅ Exported {count} orders to export/orders.csv")
    return count

def export_order_items():
    """Export order_items table to CSV."""
    print("📦 Exporting order items...")
    
    cursor = conn.execute('SELECT * FROM order_items')
    
    with open('export/order_items.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        writer.writerow([
            'id', 'order_id', 'isbn13', 'title', 'author',
            'price', 'quantity', 'subtotal'
        ])
        
        count = 0
        for row in cursor.fetchall():
            writer.writerow([
                int(row['id']),
                row['order_id'],
                row['isbn13'],
                row['title'],
                row['author'] or '',
                float(row['price']) if row['price'] else 0.0,
                int(row['quantity']),
                float(row['subtotal']) if row['subtotal'] else 0.0
            ])
            count += 1
    
    print(f"✅ Exported {count} order items to export/order_items.csv")
    return count

def export_delivery_addresses():
    """Export delivery_addresses table to CSV."""
    print("📍 Exporting delivery addresses...")
    
    cursor = conn.execute('SELECT * FROM delivery_addresses')
    
    with open('export/delivery_addresses.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        writer.writerow([
            'id', 'order_id', 'full_name', 'phone', 'address_line1',
            'address_line2', 'city', 'state', 'pincode', 'landmark'
        ])
        
        count = 0
        for row in cursor.fetchall():
            writer.writerow([
                int(row['id']),
                row['order_id'],
                row['full_name'],
                row['phone'],
                row['address_line1'],
                row['address_line2'] or '',
                row['city'],
                row['state'],
                row['pincode'],
                row['landmark'] or ''
            ])
            count += 1
    
    print(f"✅ Exported {count} delivery addresses to export/delivery_addresses.csv")
    return count

if __name__ == '__main__':
    # Create export directory
    os.makedirs('export', exist_ok=True)
    
    print("=" * 60)
    print("🚀 EXPORTING DATA TO CSV (Schema-Consistent)")
    print("=" * 60)
    print()
    
    total_books = export_books()
    total_users = export_users()
    total_admins = export_admins()
    total_orders = export_orders()
    total_items = export_order_items()
    total_addresses = export_delivery_addresses()
    
    conn.close()
    
    print()
    print("=" * 60)
    print("✅ ALL DATA EXPORTED SUCCESSFULLY!")
    print("=" * 60)
    print(f"""
📊 Summary:
   - Books: {total_books}
   - Users: {total_users}
   - Admins: {total_admins}
   - Orders: {total_orders}
   - Order Items: {total_items}
   - Delivery Addresses: {total_addresses}

📁 Files created in 'export/' directory:
   - books.csv
   - users.csv
   - admins.csv
   - orders.csv
   - order_items.csv
   - delivery_addresses.csv

📤 Next step: Upload to S3
   python upload_to_s3.py
""")
