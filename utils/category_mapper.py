
"""
Category Mapping Logic
Maps messy database categories to clean display categories on the fly.
"""

# Define category mappings: Display Category -> List of Raw DB Categories (substrings or exact matches)
# The order matters for precedence if logic uses it.
CATEGORY_MAPPING = {
    'Fiction': [
        'fiction', 'stories', 'tales', 'novels', 'literary collections', 'literature'
    ],
    'Mystery & Thriller': [
        'detective', 'mystery', 'thriller', 'suspense', 'crime', 'investigation', 'murder', 
        'spies', 'espionage', 'conspiracies', 'holmes', 'poirot', 'marple', 'legal'
    ],
    'Science Fiction & Fantasy': [
        'science fiction', 'fantasy', 'sci-fi', 'dragons', 'magic', 'wizards', 'elves', 
        'vampires', 'horror', 'ghost', 'undead', 'dystopia', 'aliens', 'space'
    ],
    'Children\'s & YA': [
        'children', 'juvenile', 'young adult', 'fairy tales', 'animals', 'boys', 'girls', 
        'harry potter', 'disney', 'picture book'
    ],
    'Biography & Memoir': [
        'biography', 'autobiography', 'memoir', 'diaries', 'letters', 'journal'
    ],
    'History': [
        'history', 'war', 'civilization', 'ancient', 'world', 'past', 'century', 'historical'
    ],
    'Science & Tech': [
        'science', 'technology', 'mathematics', 'physics', 'computers', 'chemistry', 
        'biology', 'astronomy', 'engineering', 'programming', 'software'
    ],
    'Arts & Literature': [
        'art', 'music', 'performing arts', 'drama', 'poetry', 'design', 'architecture', 
        'photography', 'humor', 'comics', 'graphic novels'
    ],
    'Business & Economics': [
        'business', 'economics', 'finance', 'management', 'marketing', 'leadership', 'money'
    ],
    'Health & Wellness': [
        'health', 'fitness', 'medical', 'psychology', 'self-help', 'cooking', 'food', 
        'wellness', 'diet'
    ],
    'Non-Fiction': [
        'non-fiction', 'religion', 'philosophy', 'education', 'travel', 'reference', 
        'social science', 'political science', 'family', 'relationships'
    ]
}

def get_display_categories():
    """Return a list of clean display categories."""
    return list(CATEGORY_MAPPING.keys())

def get_normalized_category(raw_category):
    """
    Given a raw category string from DB, return the normalized Display Category.
    """
    if not raw_category:
        return 'Other'
        
    raw_lower = raw_category.lower()
    
    # Check specific mappings
    for display_cat, keywords in CATEGORY_MAPPING.items():
        for keyword in keywords:
            # Check for word boundary or direct inclusion? 
            # Substring is safer for this messy data.
            if keyword in raw_lower:
                return display_cat
                
    # Fallback to Title Case of raw if not found, or generic 'Other'
    # Actually, if it contains 'fiction' but missed above, catch-all
    if 'fiction' in raw_lower: 
        return 'Fiction'
    if 'history' in raw_lower:
        return 'History'
        
    return 'General' # or return raw_category.title() if you want to keep odd ones

def get_sql_conditions_for_category(display_category):
    """
    Returns a list of SQL conditions and params to filter by a Display Category.
    Since we don't have a simple list of exact matches, we need to use LIKE operators for the keywords.
    """
    if display_category not in CATEGORY_MAPPING:
        return None, []
        
    keywords = CATEGORY_MAPPING[display_category]
    # Construct "OR" clauses for LIKE
    # query_part: "(LOWER(categories) LIKE ? OR LOWER(categories) LIKE ? ...)"
    # params: ['%keyword1%', '%keyword2%', ...]
    
    conditions = []
    params = []
    
    for word in keywords:
        conditions.append("LOWER(categories) LIKE ?")
        params.append(f"%{word.lower()}%")
        
    query_part = f"({' OR '.join(conditions)})"
    return query_part, params
