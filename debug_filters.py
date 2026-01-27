
import sqlite3
from utils.category_mapper import get_sql_conditions_for_category

def debug_filters():
    db_path = 'instance/bookstore.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("--- DEBUGGING FILTERS ---")
    
    # 1. Check Category Mapping
    cat = 'Mystery & Thriller'
    print(f"\n1. Testing Category: '{cat}'")
    query_part, params = get_sql_conditions_for_category(cat)
    print(f"   Query Part: {query_part}")
    print(f"   Params: {params}")
    
    full_query = f"SELECT count(*) FROM books WHERE {query_part}"
    cursor.execute(full_query, params)
    count = cursor.fetchone()[0]
    print(f"   Matches in DB: {count}")
    
    # 2. Check Price Filter
    print(f"\n2. Testing Price Filter")
    # Check max price in DB
    cursor.execute("SELECT MAX(price) FROM books")
    max_price = cursor.fetchone()[0]
    print(f"   Max price in DB: {max_price}")
    
    # Check null prices
    cursor.execute("SELECT count(*) FROM books WHERE price IS NULL")
    null_prices = cursor.fetchone()[0]
    print(f"   Books with NULL price: {null_prices}")
    
    # Check filter
    limit = 2000
    cursor.execute("SELECT count(*) FROM books WHERE price <= ?", (limit,))
    matches = cursor.fetchone()[0]
    print(f"   Books with price <= {limit}: {matches}")
    
    # 3. Check Author Filter
    print(f"\n3. Testing Author Filter")
    term = "Rowling"
    cursor.execute("SELECT count(*) FROM books WHERE LOWER(authors) LIKE ?", (f'%{term.lower()}%',))
    matches = cursor.fetchone()[0]
    print(f"   Books matching '{term}': {matches}")
    
    cursor.execute("SELECT title, authors FROM books WHERE LOWER(authors) LIKE ? LIMIT 3", (f'%{term.lower()}%',))
    for row in cursor.fetchall():
        print(f"     - {row['title']} by {row['authors']}")

    conn.close()

if __name__ == "__main__":
    debug_filters()
