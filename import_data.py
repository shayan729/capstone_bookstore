# import_data.py - Run this ONCE to populate database
import pandas as pd
import sqlite3
import os

def calculate_price(num_pages, base_price=299, price_per_page=0.5):
    """Calculate book price based on pages."""
    if pd.isna(num_pages) or num_pages is None:
        return base_price + 100
    return round(base_price + (num_pages * price_per_page), 2)

def import_books_from_csv(csv_path='data/books.csv', db_path='instance/bookstore.db'):
    """
    Import books from CSV into SQLite database.
    This should be run ONCE during initial setup.
    """
    print("Reading CSV file...")
    df = pd.read_csv(csv_path)
    
    print(f"Found {len(df)} books in CSV")
    
    # Calculate prices for all books
    df['price'] = df['num_pages'].apply(calculate_price)
    
    # Add default stock
    df['stock'] = 10
    
    # Clean data
    df['isbn13'] = df['isbn13'].astype(str)
    df['isbn10'] = df['isbn10'].fillna('').astype(str)
    df['subtitle'] = df['subtitle'].fillna('')
    df['authors'] = df['authors'].fillna('Unknown Author')
    df['categories'] = df['categories'].fillna('General')
    df['thumbnail'] = df['thumbnail'].fillna('')
    df['description'] = df['description'].fillna('No description available.')
    
    # Connect to database
    print("Connecting to database...")
    conn = sqlite3.connect(db_path)
    
    # Import to SQLite (append mode to avoid duplicates)
    print("Importing to database...")
    df.to_sql('books', con=conn, if_exists='replace', index=False)
    
    print(f"Successfully imported {len(df)} books!")
    
    # Verify import
    cursor = conn.cursor()
    count = cursor.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    print(f"Total books in database: {count}")
    
    conn.close()

def init_database():
    """Initialize database with schema."""
    print("Initializing database...")
    
    # Create instance directory if not exists
    os.makedirs('instance', exist_ok=True)
    
    conn = sqlite3.connect('instance/bookstore.db')
    cursor = conn.cursor()
    
    # Read and execute schema
    with open('schema.sql', 'r') as f:
        cursor.executescript(f.read())
    
    conn.commit()
    conn.close()
    print("Database schema created!")

if __name__ == '__main__':
    # Step 1: Create database schema
    init_database()
    
    # Step 2: Import books from CSV
    import_books_from_csv()
    
    print("\n✅ Database setup complete!")
    print("You can now run: python app.py")
