
import sqlite3

# Define category mappings
MAPPING = {
    'Fiction': [
        'American fiction', 'English fiction', 'Domestic fiction', 'Humorous fiction', 
        'Scientific fiction', 'Short stories', 'Short stories, American', 'Short stories, English',
        'Tales', 'Stories', 'Novels', 'Historical fiction', 'General', 'Literary Collections'
    ],
    'Mystery & Thriller': [
        'Detective and mystery stories', 'Detective and mystery stories, English',
        'Detective and mystery stories, American', 'Mystery', 'Thriller', 'Suspense',
        'Crime investigation', 'Murder', 'Spies', 'Espionage', 'Conspiracies', 
        'Bond, James (Fictitious character)', 'Holmes, Sherlock (Fictitious character)',
        'Poirot, Hercule (Fictitious character)', 'Marple, Jane (Fictitious character)'
    ],
    'Science Fiction & Fantasy': [
        'Science fiction', 'Science fiction, American', 'Science fiction, English',
        'Fantasy', 'Fantasy fiction', 'Fantasy fiction, English', 'Fantasy fiction, American',
        'Dragons', 'Magic', 'Wizards', 'Elves', 'Vampires', 'Horror', 'Horror tales',
        'Horror stories', 'Ghost stories', 'Occult fiction', 'Dystopias'
    ],
    'Children\'s & Young Adult': [
        'Children\'s stories', 'Children\'s stories, English', 'Children\'s literature',
        'Juvenile Fiction', 'Juvenile Nonfiction', 'Young Adult Fiction', 'Fairy tales',
        'Animals', 'Caterpillars', 'Harry Potter', 'Toads', 'Bears', 'Boys', 'Girls'
    ],
    'Biography & Memoir': [
        'Biography & Autobiography', 'Biography', 'Autobiography', 'Memoir',
        'Diaries', 'Letters', 'Presidents', 'Artists', 'Authors', 'Musicians', 
        'Actors', 'Philosophers', 'Scientists'
    ],
    'History': [
        'History', 'History, Modern', 'World War, 1914-1918', 'World War, 1939-1945',
        'Great Britain', 'United States', 'Europe', 'Civilization', 'Ancient', 
        'Social Science', 'Political Science', 'War'
    ],
    'Science & Technology': [
        'Science', 'Mathematics', 'Physics', 'Computers', 'Technology', 'Engineering',
        'Nature', 'Biology', 'Chemistry', 'Astronomy', 'Medical', 'Health & Fitness',
        'Psychology'
    ],
    'Arts & Literature': [
        'Art', 'Music', 'Performing Arts', 'Drama', 'Poetry', 'Literary Criticism',
        'Design', 'Architecture', 'Photography', 'Humor', 'Comics & Graphic Novels'
    ],
    'Non-Fiction': [
        'Business & Economics', 'Religion', 'Philosophy', 'Education', 'Travel',
        'Cooking', 'Gardening', 'Sports & Recreation', 'Self-Help', 'Family & Relationships',
        'True Crime', 'Reference', 'Language Arts & Disciplines'
    ]
}

def normalize_db():
    conn = sqlite3.connect('instance/bookstore.db')
    cursor = conn.cursor()
    
    print("Normalizing categories...")
    
    count = 0
    # Create lookup map for faster processing
    lookup = {}
    for standard_cat, variants in MAPPING.items():
        for v in variants:
            lookup[v.lower()] = standard_cat
        lookup[standard_cat.lower()] = standard_cat  # Ensure exact matches work

    # Update logic where we try to match substrings if exact match fails
    # Get all unique categories first
    cursor.execute("SELECT DISTINCT categories FROM books")
    rows = cursor.fetchall()
    
    for row in rows:
        original = row[0]
        if not original:
            continue
            
        normalized = None
        orig_lower = original.lower()
        
        # 1. Exact or list lookup
        if orig_lower in lookup:
            normalized = lookup[orig_lower]
        
        # 2. Substring matching
        if not normalized:
            for standard_cat, variants in MAPPING.items():
                for v in variants:
                    if v.lower() in orig_lower:
                        normalized = standard_cat
                        break
                if normalized:
                    break
        
        # 3. Default fallback logic
        if not normalized:
            if 'fiction' in orig_lower:
                normalized = 'Fiction'
            elif 'history' in orig_lower:
                normalized = 'History'
            elif 'biography' in orig_lower or 'memoir' in orig_lower:
                normalized = 'Biography & Memoir'
            elif 'science' in orig_lower:
                normalized = 'Science & Technology'
            else:
                normalized = 'Non-Fiction' # Safe fallback

        if normalized and normalized != original:
            cursor.execute("UPDATE books SET categories = ? WHERE categories = ?", (normalized, original))
            count += cursor.rowcount
            # print(f"Updated '{original}' -> '{normalized}'")

    conn.commit()
    print(f"Successfully normalized {count} records.")
    
    # Verify results
    print("\nDistinct Categories after normalization:")
    cursor.execute("SELECT DISTINCT categories, COUNT(*) FROM books GROUP BY categories ORDER BY COUNT(*) DESC")
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]}")
        
    conn.close()

if __name__ == '__main__':
    normalize_db()
