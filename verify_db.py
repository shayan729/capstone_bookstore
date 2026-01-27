# verify_db.py
import sqlite3

conn = sqlite3.connect('instance/bookstore.db')
cursor = conn.cursor()

print("📊 Database Structure:")
print("-" * 50)
cursor.execute("PRAGMA table_info(books)")
for col in cursor.fetchall():
    print(f"  {col[1]:20} {col[2]:10}")

print("\n📈 Sample Data:")
print("-" * 50)
cursor.execute("SELECT title, authors, average_rating, published_year FROM books LIMIT 3")
for row in cursor.fetchall():
    print(f"  {row}")

conn.close()
