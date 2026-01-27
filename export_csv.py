# export_to_csv.py
import sqlite3
import csv

conn = sqlite3.connect('instance/bookstore.db')

# Export books
cursor = conn.execute('SELECT * FROM books')
with open('books.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow([desc[0] for desc in cursor.description])  # Headers
    writer.writerows(cursor.fetchall())

# Export users
cursor = conn.execute('SELECT * FROM users')
with open('users.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow([desc[0] for desc in cursor.description])
    writer.writerows(cursor.fetchall())

print("✅ CSV files created!")
