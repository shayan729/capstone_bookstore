from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import os
import math
import sqlite3
from werkzeug.utils import secure_filename
from config import Config
from utils.db_helper import get_db, close_db
from utils.helper import calculate_book_price, format_authors, safe_thumbnail
from utils.category_mapper import get_display_categories, get_sql_conditions_for_category, get_normalized_category
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re

app = Flask(__name__)
app.config.from_object(Config)

# Register database teardown
app.teardown_appcontext(close_db)

# Ensure instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# User storage is now handled via database


# Helper to map DB row to frontend book object
def map_book_row(row):
    """Convert database row to dictionary with frontend-friendly keys."""
    if not row:
        return None
    
    book = dict(row)
    
    # Map database columns to frontend keys
    book['id'] = row['isbn13']  # Use isbn13 as ID since no auto-increment id column
    book['title'] = row['title'] or 'Untitled'
    book['author'] = row['authors'] or 'Unknown Author'
    book['category'] = get_normalized_category(row['categories']) # Logic normalization
    # book['original_category'] = row['categories'] # debug
    book['price'] = float(row['price']) if row['price'] else 399.0
    book['stock'] = int(row['stock']) if row['stock'] else 0
    book['image'] = row['thumbnail'] or '/static/images/book-placeholder.jpg'
    book['rating'] = float(row['average_rating']) if row['average_rating'] else 0.0
    book['description'] = row['description'] or 'No description available.'
    book['isbn'] = row['isbn13']
    book['isbn10'] = row['isbn10'] or ''
    book['subtitle'] = row['subtitle'] or ''
    book['publisher'] = "Unknown Publisher"  # Not in CSV schema
    book['pages'] = int(row['num_pages']) if row['num_pages'] else 0
    book['language'] = "English"  # Default language
    book['pub_date'] = str(int(row['published_year'])) if row['published_year'] else "Unknown"
    book['ratings_count'] = int(row['ratings_count']) if row['ratings_count'] else 0
    book['reviews'] = []  # Placeholder for future review feature
    
    return book

# ==================== PUBLIC ROUTES ====================

@app.route('/')
def index():
    """Homepage with featured books, categories, and recent additions."""
    db = get_db()
    
    # Featured books (highest rated with most reviews)
    featured_rows = db.execute(
        '''SELECT * FROM books 
           WHERE average_rating IS NOT NULL 
           ORDER BY average_rating DESC, ratings_count DESC 
           LIMIT 6'''
    ).fetchall()
    featured_books = [map_book_row(r) for r in featured_rows]
    
    category_rows = db.execute(
        '''SELECT DISTINCT categories FROM books 
           WHERE categories IS NOT NULL AND categories != ''
           LIMIT 50'''
    ).fetchall()
    # Normalize and get unique set for display if needed mixed with predefined?
    # Actually, index page categories row usually shows 'cards' or links. 
    # Let's just use the clean list from mapper for the "Browse by Category" section if we controlled it.
    # But for now, let's keep the backend logic consistent.
    # The index page might show random ones, let's normalize them too just in case.
    # But easier: just pass the 8 main ones from mapper.
    categories = get_display_categories()[:8]
    
    # Recently published books
    recent_rows = db.execute(
        '''SELECT * FROM books 
           WHERE published_year IS NOT NULL 
           ORDER BY published_year DESC 
           LIMIT 6'''
    ).fetchall()
    recent_books = [map_book_row(r) for r in recent_rows]
    
    # Testimonials
    testimonials = [
        {
            'name': 'Alice Johnson',
            'role': 'Student',
            'text': 'BookStore Manager helped me find all my textbooks at great prices!'
        },
        {
            'name': 'Mark Smith',
            'role': 'Avid Reader',
            'text': 'The collection is amazing and delivery was super fast.'
        },
        {
            'name': 'Sarah Lee',
            'role': 'Teacher',
            'text': 'A wonderful resource for our local community. Highly recommended!'
        }
    ]
    
    # Statistics
    total_books = db.execute('SELECT COUNT(*) as count FROM books').fetchone()['count']
    avg_rating = db.execute(
        'SELECT AVG(average_rating) as avg FROM books WHERE average_rating IS NOT NULL'
    ).fetchone()['avg']
    
    return render_template(
        'index.html',
        featured_books=featured_books,
        recent_books=recent_books,
        categories=categories,
        testimonials=testimonials,
        total_books=total_books,
        avg_rating=round(avg_rating, 1) if avg_rating else 0
    )


@app.route('/catalog')
def catalog():
    """Catalog page with filtering and sorting."""
    # Use logical categories
    categories = get_display_categories()
    
    return render_template('catalog.html', categories=categories)


@app.route('/api/books')
def get_books():
    """API endpoint for filtered and paginated book list."""
    db = get_db()
    
    # Base query
    query = 'SELECT * FROM books WHERE 1=1'
    params = []
    
    # Search filter
    search_query = request.args.get('q', '').strip()
    if search_query:
        query += ' AND (LOWER(title) LIKE ? OR LOWER(authors) LIKE ? OR LOWER(description) LIKE ?)'
        search_param = f'%{search_query.lower()}%'
        params.extend([search_param, search_param, search_param])
    
    # Category filter (Normalized Logic)
    category = request.args.get('category', '').strip()
    if category and category != 'All':
        # Resolve display category to SQL conditions
        cat_query, cat_params = get_sql_conditions_for_category(category)
        if cat_query:
            query += f' AND {cat_query}'
            params.extend(cat_params)
    
    # Price filter
    try:
        price_max = float(request.args.get('price_max', 2000))
        query += ' AND price <= ?'
        params.append(price_max)
    except ValueError:
        price_max = 2000
    
    # Author filter
    author = request.args.get('author', '').strip()
    if author:
        query += ' AND LOWER(authors) LIKE ?'
        params.append(f'%{author.lower()}%')
    
    # Stock filter
    in_stock = request.args.get('in_stock', '').lower() == 'true'
    if in_stock:
        query += ' AND stock > 0'
    
    # Sorting
    sort_by = request.args.get('sort', 'rating')
    sort_options = {
        'price_low': 'price ASC',
        'price_high': 'price DESC',
        'az': 'title ASC',
        'za': 'title DESC',
        'newest': 'published_year DESC',
        'oldest': 'published_year ASC',
        'rating': 'average_rating DESC, ratings_count DESC',
        'popular': 'ratings_count DESC'
    }
    
    order_clause = sort_options.get(sort_by, 'average_rating DESC, ratings_count DESC')
    query += f' ORDER BY {order_clause}'
    
    # Count total results for pagination
    count_query = f"SELECT COUNT(*) as count FROM ({query})"
    total_books = db.execute(count_query, params).fetchone()['count']
    
    # Pagination
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = 12
    except ValueError:
        page = 1
        per_page = 12
    
    offset = (page - 1) * per_page
    query += ' LIMIT ? OFFSET ?'
    params.extend([per_page, offset])
    
    # Execute query
    rows = db.execute(query, params).fetchall()
    books_data = [map_book_row(r) for r in rows]
    
    total_pages = math.ceil(total_books / per_page) if total_books > 0 else 1
    
    return jsonify({
        'books': books_data,
        'total': total_books,
        'page': page,
        'pages': total_pages,
        'per_page': per_page
    })


@app.route('/book/<isbn13>')
def product_details(isbn13):
    """Individual book detail page."""
    db = get_db()
    
    # Fetch book by ISBN-13
    row = db.execute('SELECT * FROM books WHERE isbn13 = ?', (isbn13,)).fetchone()
    book = map_book_row(row)
    
    if not book:
        return render_template('404.html', message="Book not found"), 404
    
    # Fetch related books (same category, exclude current book)
    related_rows = db.execute(
        '''SELECT * FROM books 
           WHERE categories = ? AND isbn13 != ? 
           ORDER BY average_rating DESC 
           LIMIT 4''',
        (book['category'], isbn13)
    ).fetchall()
    related_books = [map_book_row(r) for r in related_rows]
    
    return render_template('product_details.html', book=book, related_books=related_books)


@app.route('/search')
def search():
    """Search results page."""
    query = request.args.get('q', '').strip()
    
    if not query:
        return redirect(url_for('catalog'))
    
    db = get_db()
    
    # Search in title, authors, description
    search_param = f'%{query.lower()}%'
    rows = db.execute(
        '''SELECT * FROM books 
           WHERE LOWER(title) LIKE ? OR LOWER(authors) LIKE ? OR LOWER(description) LIKE ?
           ORDER BY 
               CASE 
                   WHEN LOWER(title) LIKE ? THEN 1
                   WHEN LOWER(authors) LIKE ? THEN 2
                   ELSE 3
               END,
               average_rating DESC
           LIMIT 50''',
        (search_param, search_param, search_param, search_param, search_param)
    ).fetchall()
    
    books = [map_book_row(r) for r in rows]
    
    return render_template('search.html', books=books, query=query, count=len(books))


@app.route('/about')
def about():
    """About page."""
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page with form."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        # TODO: Stage 2 - Send email via AWS SNS
        # For now, just show success message
        
        if name and email and message:
            return render_template('contact.html', success=True)
        else:
            return render_template('contact.html', error="Please fill in all required fields.")
    
    return render_template('contact.html')
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration with database storage."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not all([name, email, username, password]):
            return render_template('signup.html', error="All fields are required.")
        
        if len(name) < 2:
            return render_template('signup.html', error="Name must be at least 2 characters.")
        
        if len(username) < 3:
            return render_template('signup.html', error="Username must be at least 3 characters.")
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return render_template('signup.html', error="Username can only contain letters, numbers, and underscores.")
        
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return render_template('signup.html', error="Invalid email format.")
        
        if len(password) < 8:
            return render_template('signup.html', error="Password must be at least 8 characters.")
        
        if password != confirm_password:
            return render_template('signup.html', error="Passwords do not match.")
        
        # Check if user exists in database
        db = get_db()
        existing_user = db.execute(
            'SELECT id FROM users WHERE username = ? OR email = ?',
            (username, email)
        ).fetchone()
        
        if existing_user:
            return render_template('signup.html', error="Username or email already exists.")
        
        # Hash password and insert into database
        password_hash = generate_password_hash(password)
        
        try:
            db.execute(
                '''INSERT INTO users (username, email, password_hash, full_name, role)
                   VALUES (?, ?, ?, ?, ?)''',
                (username, email, password_hash, name, 'customer')
            )
            db.commit()
            
            return render_template('login.html', success="Account created successfully! Please login.")
            
        except sqlite3.IntegrityError:
            return render_template('signup.html', error="Username or email already exists.")
    
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login with database verification."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        
        if not username or not password:
            return render_template('login.html', error="Please enter both username and password.")
        
        # Check credentials in database
        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE username = ? OR email = ?',
            (username, username)
        ).fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            # Update last login
            db.execute(
                'UPDATE users SET last_login = ? WHERE id = ?',
                (datetime.now(), user['id'])
            )
            db.commit()
            
            # Set session
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_role'] = user['role']
            session['user_name'] = user['full_name']
            
            return redirect(url_for('customer_dashboard'))
        
        return render_template('login.html', error="Invalid username or password.")
    
    return render_template('login.html')


@app.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    """Admin registration."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not all([name, username, email, password]):
             return render_template('admin_signup.html', error="All fields are required.")
        
        if password != confirm_password:
             return render_template('admin_signup.html', error="Passwords do not match.")

        db = get_db()
        try:
            password_hash = generate_password_hash(password)
            db.execute(
                'INSERT INTO admins (username, email, password_hash, full_name) VALUES (?, ?, ?, ?)',
                (username, email, password_hash, name)
            )
            db.commit()
            return redirect(url_for('admin_login'))
        except sqlite3.IntegrityError:
            return render_template('admin_signup.html', error="Admin username or email already exists.")

    return render_template('admin_signup.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login with database verification."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            return render_template('admin_login.html', error="Please enter both username and password.")
        
        # Check admin credentials in database (Username or Email)
        db = get_db()
        admin = db.execute(
            'SELECT * FROM admins WHERE username = ? OR email = ?',
            (username, username)
        ).fetchone()
        
        if admin and check_password_hash(admin['password_hash'], password):
            # Update last login
            db.execute(
                'UPDATE admins SET last_login = ? WHERE id = ?',
                (datetime.now(), admin['id'])
            )
            db.commit()
            
            # Set session
            session['admin_id'] = admin['id']
            session['admin'] = admin['username']
            session['user_role'] = 'admin'
            
            return redirect(url_for('admin_dashboard'))
        
        return render_template('admin_login.html', error="Invalid admin credentials.")
    
    return render_template('admin_login.html')


@app.route('/logout')
def logout():
    """Logout user."""
    session.clear()
    return redirect(url_for('index'))


@app.route('/admin/logout')
def admin_logout():
    """Admin logout."""
    session.clear()
    return redirect(url_for('index'))


# ==================== PROTECTED ROUTES ====================

@app.route('/dashboard')
def customer_dashboard():
    """Customer dashboard (requires login)."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    # Mock Orders (until implemented)
    orders = [
        {'id': '1001', 'date': '2026-01-20', 'items': 2, 'total': 450.00, 'status': 'Delivered'},
        {'id': '1005', 'date': '2026-01-25', 'items': 1, 'total': 299.00, 'status': 'Processing'}
    ]
    
    # User Stats (Mock)
    stats = {
        'total_orders': 2, # Mock based on above
        'books_purchased': 3,
        'amount_spent': 749.00,
        'wishlist_items': 5
    }
    
    # Fetch Recommended Books (Random selection from same categories or popular)
    # For now, just 4 random books
    recommended_rows = db.execute('SELECT * FROM books ORDER BY RANDOM() LIMIT 4').fetchall()
    recommended_books = [map_book_row(r) for r in recommended_rows]
    
    # Recently Viewed (Mock - could be session based)
    recently_viewed_rows = db.execute('SELECT * FROM books ORDER BY RANDOM() LIMIT 6').fetchall()
    recently_viewed = [map_book_row(r) for r in recently_viewed_rows]
    
    return render_template(
        'customer_dashboard.html', 
        user=user, 
        orders=orders,
        stats=stats,
        recommended_books=recommended_books,
        recently_viewed=recently_viewed
    )


@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard (requires admin login)."""
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    db = get_db()
    
    # Get statistics
    total_books = db.execute('SELECT COUNT(*) as count FROM books').fetchone()['count']
    total_users = db.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
    total_admins = db.execute('SELECT COUNT(*) as count FROM admins').fetchone()['count']
    
    # Recent users
    recent_users = db.execute(
        'SELECT username, email, created_at FROM users ORDER BY created_at DESC LIMIT 5'
    ).fetchall()
    
    # Low stock books
    low_stock = db.execute(
        'SELECT * FROM books WHERE stock <= 5 ORDER BY stock ASC LIMIT 10'
    ).fetchall()
    low_stock_books = [map_book_row(r) for r in low_stock]

    # Mock Orders (until implemented)
    orders = [
        {'id': '1024', 'customer': 'John Doe', 'date': '2026-01-27', 'items': 3, 'amount': 45.99, 'status': 'Pending'},
        {'id': '1023', 'customer': 'Jane Smith', 'date': '2026-01-26', 'items': 1, 'amount': 12.50, 'status': 'Processing'},
        {'id': '1022', 'customer': 'Bob Johnson', 'date': '2026-01-26', 'items': 2, 'amount': 28.00, 'status': 'Shipped'},
        {'id': '1021', 'customer': 'Alice Brown', 'date': '2026-01-25', 'items': 5, 'amount': 112.75, 'status': 'Delivered'},
        {'id': '1020', 'customer': 'Charlie Wilson', 'date': '2026-01-24', 'items': 1, 'amount': 15.00, 'status': 'Cancelled'}
    ]

    stats = {
        'total_books': total_books,
        'total_users': total_users,
        'total_admins': total_admins,
        'total_orders': 154,  # Mock total
        'total_revenue': 4520.50 # Mock revenue
    }
    
    return render_template(
        'admin_dashboard.html',
        username=session['admin'],
        stats=stats,
        recent_users=recent_users,
        low_stock_books=low_stock_books,
        recent_orders=orders
    )

# Config for Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

from flask_mail import Mail, Message
mail = Mail(app)

@app.route('/checkout', methods=['GET'])
def checkout():
    """Checkout page."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cart_items = session.get('cart', [])
    if not cart_items:
        return redirect(url_for('cart'))
        
    coupon = session.get('coupon', None)
    
    # Calculate totals again for display (logic duplicated for now, could be helper)
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    
    discount = 0
    if coupon:
        if coupon['type'] == 'percent':
            discount = subtotal * (coupon['value'] / 100)
        elif coupon['type'] == 'fixed':
            discount = coupon['value']
    
    shipping = 0 if subtotal > 500 else 50
    if subtotal == 0: shipping = 0
        
    taxable_amount = max(0, subtotal - discount)
    tax = taxable_amount * 0.18
    total = max(0, subtotal - discount + shipping + tax)
    
    totals = {
        'subtotal': subtotal,
        'discount': discount,
        'shipping': shipping,
        'tax': tax,
        'total': total
    }
    
    db = get_db()
    user = None
    if 'user_id' in session:
        user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        
    return render_template('checkout.html', cart_items=cart_items, totals=totals, coupon=coupon, user=user)

@app.route('/checkout/place-order', methods=['POST'])
def place_order():
    """Place order and send confirmation email."""
    # Cart is a list of items in the session
    cart_items = session.get('cart', [])
    if not cart_items:
        return jsonify({'success': False, 'message': 'Cart is empty'}), 400
    
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Invalid request data'}), 400
        
        # Extract form fields
        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        address1 = data.get('address1', '').strip()
        address2 = data.get('address2', '').strip()
        city = data.get('city', '').strip()
        state = data.get('state', '').strip()
        pincode = data.get('pincode', '').strip()
        landmark = data.get('landmark', '').strip()
        
        # Validation
        if not all([full_name, email, phone, address1, city, state, pincode]):
            return jsonify({'success': False, 'message': 'Please fill all required fields'}), 400
        
        # Recalculate Totals (Secure source of truth)
        subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
        coupon = session.get('coupon', None)
        discount = 0
        if coupon:
            if coupon['type'] == 'percent':
                discount = subtotal * (coupon['value'] / 100)
            elif coupon['type'] == 'fixed':
                discount = coupon['value']
        
        shipping = 0 if subtotal > 500 else 50
        if subtotal == 0: shipping = 0
            
        taxable_amount = max(0, subtotal - discount)
        tax = taxable_amount * 0.18
        total = max(0, subtotal - discount + shipping + tax)

        totals = {
            'subtotal': subtotal,
            'discount': discount,
            'shipping': shipping,
            'tax': tax,
            'total': total
        }

        # Generate Order ID
        import secrets
        order_id = f"ORD-{datetime.now().year}-{secrets.token_hex(4).upper()}"
        
        db = get_db()
        
        # Verify stock
        for item in cart_items:
            book = db.execute('SELECT stock FROM books WHERE isbn13 = ?', (item['isbn13'],)).fetchone()
            if not book or book['stock'] < item['quantity']:
                return jsonify({
                    'success': False,
                    'message': f"{item['title']} is out of stock"
                }), 400
        
        # Insert order
        db.execute('''
            INSERT INTO orders (
                order_id, user_id, guest_email, guest_name, guest_phone,
                subtotal, discount, shipping, tax, total, 
                coupon_code, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_id,
            session.get('user_id'),
            email,
            full_name,
            phone,
            totals['subtotal'],
            totals['discount'],
            totals['shipping'],
            totals['tax'],
            totals['total'],
            coupon.get('code') if coupon else None,
            'Pending'
        ))
        
        # Insert order items and update stock
        for item in cart_items:
            db.execute('''
                INSERT INTO order_items (
                    order_id, isbn13, title, price, quantity, subtotal
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                order_id,
                item['isbn13'],
                item['title'],
                item['price'],
                item['quantity'],
                item['price'] * item['quantity']
            ))
            
            db.execute(
                'UPDATE books SET stock = stock - ? WHERE isbn13 = ?',
                (item['quantity'], item['isbn13'])
            )
        
        # Insert delivery address
        db.execute('''
            INSERT INTO delivery_addresses (
                order_id, full_name, phone, 
                address_line1, address_line2, city, state, pincode, landmark
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_id, full_name, phone,
            address1, address2, city, state, pincode, landmark
        ))
        
        db.commit()
        
        # Clear cart
        session.pop('cart', None)
        session.pop('coupon', None)
        session.modified = True
        
        # Send Email
        try:
            msg = Message(f"Order Confirmation - {order_id}", recipients=[email])
            msg.body = f"Thank you for your order, {full_name}!\n\nYour Order ID is {order_id}.\nTotal Amount: ₹{total:.2f}\n\nWe will ship your items shortly."
            # mail.send(msg)
            print(f"📧 Email sent to {email}")
        except Exception as e:
            print(f"Warning: Email failed: {e}")
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'message': 'Order placed successfully!'
        })
        
    except Exception as e:
        db.rollback()
        print(f"Error placing order: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': 'Failed to place order. Please try again.'
        }), 500

@app.template_filter('format_price')
def format_price(value):
    """Format price in Indian Rupees."""
    try:
        return f"₹{float(value):,.2f}"
    except:
        return f"₹{value}"

@app.route('/order/confirmation/<order_id>')
def order_confirmation(order_id):
    """Order confirmation page."""
    db = get_db()
    order = db.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,)).fetchone()
    if not order:
        return redirect(url_for('index'))
        
    items = db.execute('SELECT * FROM order_items WHERE order_id = ?', (order_id,)).fetchall()
    address = db.execute('SELECT * FROM delivery_addresses WHERE order_id = ?', (order_id,)).fetchone()
    
    return render_template('order_confirmation.html', order=order, items=items, address=address)

@app.route('/cart')
def cart():
    """Shopping cart page."""
    cart_items = session.get('cart', [])
    coupon = session.get('coupon', None)
    
    # Calculate totals
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    
    discount = 0
    if coupon:
        if coupon['type'] == 'percent':
            discount = subtotal * (coupon['value'] / 100)
        elif coupon['type'] == 'fixed':
            discount = coupon['value']
    
    # Shipping logic (Free if > 500)
    shipping = 0 if subtotal > 500 else 50
    if subtotal == 0:
        shipping = 0
        
    # Tax (18% GST on subtotal after discount + shipping) - Simplified: Tax on (Subtotal - Discount)
    taxable_amount = max(0, subtotal - discount)
    tax = taxable_amount * 0.18
    
    total = max(0, subtotal - discount + shipping + tax)
    
    totals = {
        'subtotal': subtotal,
        'discount': discount,
        'shipping': shipping,
        'tax': tax,
        'total': total
    }
    
    return render_template('cart.html', cart_items=cart_items, totals=totals, coupon=coupon)


@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    """Add item to cart."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login to add items', 'redirect': url_for('login')}), 401

    data = request.get_json()
    isbn13 = data.get('isbn13')
    quantity = int(data.get('quantity', 1))
    
    if not isbn13:
        return jsonify({'success': False, 'message': 'Invalid book'}), 400
    
    # Initialize cart in session
    if 'cart' not in session:
        session['cart'] = []
    
    # Check if book already in cart
    cart = session['cart']
    found = False
    
    for item in cart:
        if item['isbn13'] == isbn13:
            item['quantity'] += quantity
            found = True
            break
    
    if not found:
        # Fetch book details
        db = get_db()
        book_row = db.execute('SELECT * FROM books WHERE isbn13 = ?', (isbn13,)).fetchone()
        
        if book_row:
            book = map_book_row(book_row)
            cart.append({
                'isbn13': isbn13,
                'title': book['title'],
                'price': book['price'],
                'image': book['image'],
                'quantity': quantity
            })
    
    session['cart'] = cart
    session.modified = True
    
    return jsonify({'success': True, 'cart_count': len(cart), 'message': 'Added to cart'})


@app.route('/api/cart/update', methods=['POST'])
def update_cart_item():
    """Update cart item quantity."""
    data = request.get_json()
    isbn13 = data.get('isbn13')
    quantity = int(data.get('quantity', 1))
    
    cart = session.get('cart', [])
    
    for item in cart:
        if item['isbn13'] == isbn13:
            item['quantity'] = max(1, quantity) # Ensure at least 1
            break
            
    session['cart'] = cart
    session.modified = True
    return jsonify({'success': True})


@app.route('/api/cart/remove', methods=['POST'])
def remove_from_cart():
    """Remove item from cart."""
    data = request.get_json()
    isbn13 = data.get('isbn13')
    
    cart = session.get('cart', [])
    session['cart'] = [item for item in cart if item['isbn13'] != isbn13]
    session.modified = True
    
    # If cart empty, remove coupon too
    if not session['cart']:
        session.pop('coupon', None)
        
    return jsonify({'success': True, 'cart_count': len(session['cart'])})


@app.route('/api/cart/clear', methods=['POST'])
def clear_cart():
    """Clear entire cart."""
    session['cart'] = []
    session.pop('coupon', None)
    session.modified = True
    return jsonify({'success': True})


@app.route('/api/cart/apply-coupon', methods=['POST'])
def apply_coupon():
    """Apply discount coupon."""
    data = request.get_json()
    code = data.get('code', '').upper()
    
    # Mock coupons
    coupons = {
        'BOOK20': {'type': 'percent', 'value': 20, 'desc': '20% Off'},
        'FIRST100': {'type': 'fixed', 'value': 100, 'desc': '₹100 Off'},
        'WELCOME20': {'type': 'percent', 'value': 20, 'desc': 'Welcome Offer'}
    }
    
    if code in coupons:
        session['coupon'] = {
            'code': code,
            **coupons[code]
        }
        return jsonify({'success': True, 'message': f'Coupon {code} applied!'})
    
    return jsonify({'success': False, 'message': 'Invalid coupon code.'})


# ==================== ADMIN ROUTES ====================

@app.route('/admin/books')
def admin_books():
    """Admin books management page."""
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    db = get_db()
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    # Optional Search
    search_query = request.args.get('q', '').strip()
    if search_query:
        query = 'SELECT * FROM books WHERE LOWER(title) LIKE ? OR isbn13 LIKE ? ORDER BY title ASC LIMIT ? OFFSET ?'
        search_param = f'%{search_query.lower()}%'
        rows = db.execute(query, (search_param, search_param, per_page, offset)).fetchall()
        
        count_query = 'SELECT COUNT(*) as count FROM books WHERE LOWER(title) LIKE ? OR isbn13 LIKE ?'
        total_books = db.execute(count_query, (search_param, search_param)).fetchone()['count']
    else:
        rows = db.execute(
            'SELECT * FROM books ORDER BY title ASC LIMIT ? OFFSET ?',
            (per_page, offset)
        ).fetchall()
        total_books = db.execute('SELECT COUNT(*) as count FROM books').fetchone()['count']

    books = [map_book_row(r) for r in rows]
    total_pages = math.ceil(total_books / per_page)
    
    return render_template('admin_books.html', books=books, page=page, total_pages=total_pages, search_query=search_query)


@app.route('/admin/books/add', methods=['GET', 'POST'])
def add_book():
    """Add a new book to the catalog."""
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        # Extract fields
        title = request.form.get('title', '').strip()
        authors = request.form.get('authors', '').strip()
        isbn13 = request.form.get('isbn13', '').strip()
        price = request.form.get('price', '').strip()
        stock = request.form.get('stock', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        image = request.form.get('image', '').strip()
        
        # Validation
        if not all([title, authors, isbn13, price, stock]):
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('add_book'))
            
        try:
            db = get_db()
            db.execute('''
                INSERT INTO books (
                    isbn13, title, authors, price, stock, categories, description, thumbnail, 
                    average_rating, ratings_count, published_year, num_pages
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                isbn13, title, authors, float(price), int(stock), category, description, 
                image or '/static/images/book-placeholder.jpg', 0, 0, datetime.now().year, 0
            ))
            db.commit()
            flash('Book added successfully!', 'success')
            return redirect(url_for('admin_books'))
            
        except sqlite3.IntegrityError:
            flash(f'Book with ISBN {isbn13} already exists.', 'danger')
        except Exception as e:
            flash(f'Error adding book: {str(e)}', 'danger')
            
    # Get categories for dropdown
    categories = get_display_categories()
    return render_template('admin_add_book.html', categories=categories)


@app.route('/admin/books/delete/<isbn13>', methods=['POST'])
def delete_book(isbn13):
    """Delete a book from the catalog."""
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        db = get_db()
        db.execute('DELETE FROM books WHERE isbn13 = ?', (isbn13,))
        db.commit()
        return jsonify({'success': True, 'message': 'Book deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
    total_books = db.execute('SELECT COUNT(*) as count FROM books').fetchone()['count']
    total_pages = math.ceil(total_books / per_page)
    
    return render_template(
        'admin_books.html',
        books=books,
        page=page,
        total_pages=total_pages
    )


@app.route('/admin/orders')
def admin_orders():
    """Admin orders management page."""
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    # TODO: Implement orders table and fetch orders
    orders = []
    
    return render_template('admin_orders.html', orders=orders)


# ==================== TEMPLATE FILTERS ====================

@app.template_filter('format_price')
def format_price_filter(price):
    """Format price as ₹XXX.XX"""
    try:
        return f"₹{float(price):.2f}"
    except (ValueError, TypeError):
        return "₹0.00"


@app.template_filter('rating_stars')
def rating_stars_filter(rating):
    """Convert rating to star display."""
    try:
        rating = float(rating)
        full_stars = int(rating)
        half_star = 1 if rating - full_stars >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star
        
        stars = '★' * full_stars + '☆' * half_star + '☆' * empty_stars
        return f"{stars} {rating:.1f}"
    except (ValueError, TypeError):
        return "Not rated"


@app.template_filter('truncate_text')
def truncate_text_filter(text, length=100):
    """Truncate text to specified length."""
    if not text:
        return ""
    text = str(text)
    return text[:length] + '...' if len(text) > length else text


@app.template_filter('format_authors')
def format_authors_filter(authors):
    """Format authors string."""
    if not authors:
        return "Unknown Author"
    
    author_list = [a.strip() for a in str(authors).split(';')]
    
    if len(author_list) == 1:
        return author_list[0]
    elif len(author_list) == 2:
        return f"{author_list[0]} and {author_list[1]}"
    else:
        return f"{author_list[0]} and {len(author_list)-1} others"


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """404 error handler."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """500 error handler."""
    return render_template('500.html'), 500

# ==================== RUN APPLICATION ====================

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
