# utils/helpers.py
import pandas as pd
from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def calculate_book_price(num_pages, base_price=299, price_per_page=0.5):
    """Calculate book price based on page count."""
    if pd.isna(num_pages) or num_pages is None:
        return base_price + 100
    return int(base_price + (num_pages * price_per_page))

def format_authors(authors_string):
    """Format authors string for display."""
    if pd.isna(authors_string) or not authors_string:
        return "Unknown Author"
    
    authors = [a.strip() for a in str(authors_string).split(',')]
    
    if len(authors) == 1:
        return authors[0]
    elif len(authors) == 2:
        return f"{authors[0]} and {authors[1]}"
    else:
        return f"{authors[0]} and {len(authors)-1} others"

def safe_thumbnail(thumbnail_url, fallback='/static/images/book-placeholder.jpg'):
    """Return thumbnail URL with fallback."""
    if pd.isna(thumbnail_url) or not thumbnail_url:
        return fallback
    return thumbnail_url

def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function
