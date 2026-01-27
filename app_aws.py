from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import os
import math
import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
from werkzeug.utils import secure_filename
from config import Config
from utils.category_mapper import get_display_categories, get_normalized_category
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# DynamoDB Configuration
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

# Table references
books_table = dynamodb.Table('Books')
users_table = dynamodb.Table('Users')
admins_table = dynamodb.Table('Admins')
orders_table = dynamodb.Table('Orders')
order_items_table = dynamodb.Table('OrderItems')
addresses_table = dynamodb.Table('DeliveryAddresses')

# Ensure instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# ==================== HELPER FUNCTIONS ====================

def decimal_to_float(obj):
    """Convert Decimal to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    return obj

def map_book_row(item):
    """Convert DynamoDB item to dictionary with frontend-friendly keys."""
    if not item:
        return None
    
    # Convert Decimals to floats
    item = decimal_to_float(item)
    
    book = dict(item)
    book['id'] = item.get('isbn13', '')
    book['title'] = item.get('title', 'Untitled')
    book['author'] = item.get('authors', 'Unknown Author')
    book['category'] = get_normalized_category(item.get('categories', ''))
    book['price'] = float(item.get('price', 399.0))
    book['stock'] = int(item.get('stock', 0))
    book['image'] = item.get('thumbnail', '/static/images/book-placeholder.jpg')
    book['rating'] = float(item.get('average_rating', 0.0))
    book['description'] = item.get('description', 'No description available.')
    book['isbn'] = item.get('isbn13', '')
    book['isbn10'] = item.get('isbn10', '')
    book['subtitle'] = item.get('subtitle', '')
    book['publisher'] = "Unknown Publisher"
    book['pages'] = int(item.get('num_pages', 0))
    book['language'] = "English"
    book['pub_date'] = str(int(item.get('published_year', 0))) if item.get('published_year') else "Unknown"
    book['ratings_count'] = int(item.get('ratings_count', 0))
    book['reviews'] = []
    
    return book

def scan_books_with_filter(filter_expression=None, limit=None):
    """Scan books table with optional filter."""
    scan_kwargs = {}
    
    if filter_expression:
        scan_kwargs['FilterExpression'] = filter_expression
    
    if limit:
        scan_kwargs['Limit'] = limit
    
    response = books_table.scan(**scan_kwargs)
    items = response.get('Items', [])
    
    # Handle pagination if needed
    while 'LastEvaluatedKey' in response and (not limit or len(items) < limit):
        scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
        response = books_table.scan(**scan_kwargs)
        items.extend(response.get('Items', []))
        
        if limit and len(items) >= limit:
            items = items[:limit]
            break
    
    return items

# ==================== PUBLIC ROUTES ====================

@app.route('/')
def index():
    """Homepage with featured books, categories, and recent additions."""
    
    # Featured books (scan and sort in memory - DynamoDB doesn't support ORDER BY on scan)
    all_books = scan_books_with_filter(
        filter_expression=Attr('average_rating').exists()
    )
    
    # Sort by rating and count
    featured_books = sorted(
        all_books,
        key=lambda x: (float(x.get('average_rating', 0)), int(x.get('ratings_count', 0))),
        reverse=True
    )[:6]
    featured_books = [map_book_row(b) for b in featured_books]
    
    # Categories
    categories = get_display_categories()[:8]
    
    # Recent books (sort by published year)
    all_books_pub = scan_books_with_filter(
        filter_expression=Attr('published_year').exists()
    )
    recent_books = sorted(
        all_books_pub,
        key=lambda x: float(x.get('published_year', 0)),
        reverse=True
    )[:6]
    recent_books = [map_book_row(b) for b in recent_books]
    
    # Testimonials
    testimonials = [
        {'name': 'Alice Johnson', 'role': 'Student', 'text': 'BookStore Manager helped me find all my textbooks at great prices!'},
        {'name': 'Mark Smith', 'role': 'Avid Reader', 'text': 'The collection is amazing and delivery was super fast.'},
        {'name': 'Sarah Lee', 'role': 'Teacher', 'text': 'A wonderful resource for our local community. Highly recommended!'}
    ]
    
    # Statistics
    response = books_table.scan(Select='COUNT')
    total_books = response['Count']
    
    # Average rating calculation
    all_rated = scan_books_with_filter(filter_expression=Attr('average_rating').exists())
    avg_rating = sum(float(b.get('average_rating', 0)) for b in all_rated) / len(all_rated) if all_rated else 0
    
    return render_template(
        'index.html',
        featured_books=featured_books,
        recent_books=recent_books,
        categories=categories,
        testimonials=testimonials,
        total_books=total_books,
        avg_rating=round(avg_rating, 1)
    )

@app.route('/catalog')
def catalog():
    """Catalog page with filtering and sorting."""
    categories = get_display_categories()
    return render_template('catalog.html', categories=categories)

@app.route('/api/books')
def get_books():
    """API endpoint for filtered and paginated book list."""
    
    # Get all books (we'll filter in Python due to DynamoDB limitations)
    all_books = scan_books_with_filter()
    
    # Search filter
    search_query = request.args.get('q', '').strip().lower()
    if search_query:
        all_books = [
            b for b in all_books
            if search_query in str(b.get('title', '')).lower() or
               search_query in str(b.get('authors', '')).lower() or
               search_query in str(b.get('description', '')).lower()
        ]
    
    # Category filter
    category = request.args.get('category', '').strip()
    if category and category != 'All':
        all_books = [
            b for b in all_books
            if get_normalized_category(b.get('categories', '')) == category
        ]
    
    # Price filter
    try:
        price_max = float(request.args.get('price_max', 2000))
        all_books = [b for b in all_books if float(b.get('price', 0)) <= price_max]
    except ValueError:
        pass
    
    # Author filter
    author = request.args.get('author', '').strip().lower()
    if author:
        all_books = [
            b for b in all_books
            if author in str(b.get('authors', '')).lower()
        ]
    
    # Stock filter
    in_stock = request.args.get('in_stock', '').lower() == 'true'
    if in_stock:
        all_books = [b for b in all_books if int(b.get('stock', 0)) > 0]
    
    # Sorting
    sort_by = request.args.get('sort', 'rating')
    if sort_by == 'price_low':
        all_books.sort(key=lambda x: float(x.get('price', 0)))
    elif sort_by == 'price_high':
        all_books.sort(key=lambda x: float(x.get('price', 0)), reverse=True)
    elif sort_by == 'az':
        all_books.sort(key=lambda x: str(x.get('title', '')))
    elif sort_by == 'za':
        all_books.sort(key=lambda x: str(x.get('title', '')), reverse=True)
    elif sort_by == 'newest':
        all_books.sort(key=lambda x: float(x.get('published_year', 0)), reverse=True)
    elif sort_by == 'oldest':
        all_books.sort(key=lambda x: float(x.get('published_year', 0)))
    elif sort_by == 'rating':
        all_books.sort(key=lambda x: (float(x.get('average_rating', 0)), int(x.get('ratings_count', 0))), reverse=True)
    elif sort_by == 'popular':
        all_books.sort(key=lambda x: int(x.get('ratings_count', 0)), reverse=True)
    
    # Count total
    total_books = len(all_books)
    
    # Pagination
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = 12
    except ValueError:
        page = 1
        per_page = 12
    
    offset = (page - 1) * per_page
    paginated_books = all_books[offset:offset + per_page]
    
    books_data = [map_book_row(b) for b in paginated_books]
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
    
    try:
        response = books_table.get_item(Key={'isbn13': isbn13})
        book_item = response.get('Item')
        
        if not book_item:
            return render_template('404.html', message="Book not found"), 404
        
        book = map_book_row(book_item)
        
        # Fetch related books (same category)
        category = book_item.get('categories', '')
        related_items = scan_books_with_filter(
            filter_expression=Attr('categories').eq(category) & Attr('isbn13').ne(isbn13),
            limit=20
        )
        
        # Sort by rating and limit to 4
        related_items.sort(key=lambda x: float(x.get('average_rating', 0)), reverse=True)
        related_books = [map_book_row(r) for r in related_items[:4]]
        
        return render_template('product_details.html', book=book, related_books=related_books)
        
    except Exception as e:
        print(f"Error fetching book: {e}")
        return render_template('404.html', message="Book not found"), 404

@app.route('/search')
def search():
    """Search results page."""
    query = request.args.get('q', '').strip().lower()
    
    if not query:
        return redirect(url_for('catalog'))
    
    # Search in all books
    all_books = scan_books_with_filter()
    
    # Filter and rank results
    results = []
    for book in all_books:
        title_match = query in str(book.get('title', '')).lower()
        author_match = query in str(book.get('authors', '')).lower()
        desc_match = query in str(book.get('description', '')).lower()
        
        if title_match or author_match or desc_match:
            rank = 1 if title_match else (2 if author_match else 3)
            results.append((rank, book))
    
    # Sort by rank then rating
    results.sort(key=lambda x: (x[0], -float(x[1].get('average_rating', 0))))
    books = [map_book_row(r[1]) for r in results[:50]]
    
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
        
        # TODO: Send email via AWS SNS
        if name and email and message:
            return render_template('contact.html', success=True)
        else:
            return render_template('contact.html', error="Please fill in all required fields.")
    
    return render_template('contact.html')

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration."""
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
        
        # Check if user exists using GSI
        try:
            # Check username
            username_response = users_table.query(
                IndexName='UsernameIndex',
                KeyConditionExpression=Key('username').eq(username)
            )
            
            if username_response.get('Items'):
                return render_template('signup.html', error="Username already exists.")
            
            # Check email
            email_response = users_table.query(
                IndexName='EmailIndex',
                KeyConditionExpression=Key('email').eq(email)
            )
            
            if email_response.get('Items'):
                return render_template('signup.html', error="Email already exists.")
            
            # Generate new user ID (get max ID + 1)
            all_users = users_table.scan(ProjectionExpression='id')
            user_ids = [int(u['id']) for u in all_users.get('Items', [])]
            new_user_id = max(user_ids) + 1 if user_ids else 1
            
            # Hash password and insert
            password_hash = generate_password_hash(password)
            
            users_table.put_item(Item={
                'id': new_user_id,
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'full_name': name,
                'role': 'customer',
                'created_at': datetime.now().isoformat(),
                'last_login': ''
            })
            
            return render_template('login.html', success="Account created successfully! Please login.")
            
        except Exception as e:
            print(f"Error creating user: {e}")
            return render_template('signup.html', error="An error occurred. Please try again.")
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        
        if not username or not password:
            return render_template('login.html', error="Please enter both username and password.")
        
        try:
            # Try username first
            response = users_table.query(
                IndexName='UsernameIndex',
                KeyConditionExpression=Key('username').eq(username)
            )
            
            user = response.get('Items', [None])[0] if response.get('Items') else None
            
            # If not found, try email
            if not user:
                response = users_table.query(
                    IndexName='EmailIndex',
                    KeyConditionExpression=Key('email').eq(username)
                )
                user = response.get('Items', [None])[0] if response.get('Items') else None
            
            if user and check_password_hash(user['password_hash'], password):
                # Update last login
                users_table.update_item(
                    Key={'id': int(user['id'])},
                    UpdateExpression='SET last_login = :login_time',
                    ExpressionAttributeValues={':login_time': datetime.now().isoformat()}
                )
                
                # Set session
                session['user_id'] = int(user['id'])
                session['username'] = user['username']
                session['user_role'] = user['role']
                session['user_name'] = user['full_name']
                
                return redirect(url_for('customer_dashboard'))
            
            return render_template('login.html', error="Invalid username or password.")
            
        except Exception as e:
            print(f"Login error: {e}")
            return render_template('login.html', error="An error occurred. Please try again.")
    
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
        
        try:
            # Check if admin exists
            response = admins_table.query(
                IndexName='UsernameIndex',
                KeyConditionExpression=Key('username').eq(username)
            )
            
            if response.get('Items'):
                return render_template('admin_signup.html', error="Admin username already exists.")
            
            # Generate new admin ID
            all_admins = admins_table.scan(ProjectionExpression='id')
            admin_ids = [int(a['id']) for a in all_admins.get('Items', [])]
            new_admin_id = max(admin_ids) + 1 if admin_ids else 1
            
            password_hash = generate_password_hash(password)
            
            admins_table.put_item(Item={
                'id': new_admin_id,
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'full_name': name,
                'created_at': datetime.now().isoformat(),
                'last_login': ''
            })
            
            return redirect(url_for('admin_login'))
            
        except Exception as e:
            print(f"Error creating admin: {e}")
            return render_template('admin_signup.html', error="An error occurred.")
    
    return render_template('admin_signup.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            return render_template('admin_login.html', error="Please enter both username and password.")
        
        try:
            response = admins_table.query(
                IndexName='UsernameIndex',
                KeyConditionExpression=Key('username').eq(username)
            )
            
            admin = response.get('Items', [None])[0] if response.get('Items') else None
            
            if admin and check_password_hash(admin['password_hash'], password):
                # Update last login
                admins_table.update_item(
                    Key={'id': int(admin['id'])},
                    UpdateExpression='SET last_login = :login_time',
                    ExpressionAttributeValues={':login_time': datetime.now().isoformat()}
                )
                
                session['admin_id'] = int(admin['id'])
                session['admin'] = admin['username']
                session['user_role'] = 'admin'
                
                return redirect(url_for('admin_dashboard'))
            
            return render_template('admin_login.html', error="Invalid admin credentials.")
            
        except Exception as e:
            print(f"Admin login error: {e}")
            return render_template('admin_login.html', error="An error occurred.")
    
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
    """Customer dashboard."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        # Get user
        response = users_table.get_item(Key={'id': session['user_id']})
        user = response.get('Item')
        
        # Mock orders (until fully implemented)
        orders = [
            {'id': '1001', 'date': '2026-01-20', 'items': 2, 'total': 450.00, 'status': 'Delivered'},
            {'id': '1005', 'date': '2026-01-25', 'items': 1, 'total': 299.00, 'status': 'Processing'}
        ]
        
        stats = {
            'total_orders': 2,
            'books_purchased': 3,
            'amount_spent': 749.00,
            'wishlist_items': 5
        }
        
        # Random recommendations
        all_books = scan_books_with_filter(limit=50)
        import random
        recommended_books = [map_book_row(b) for b in random.sample(all_books, min(4, len(all_books)))]
        recently_viewed = [map_book_row(b) for b in random.sample(all_books, min(6, len(all_books)))]
        
        return render_template(
            'customer_dashboard.html',
            user=user,
            orders=orders,
            stats=stats,
            recommended_books=recommended_books,
            recently_viewed=recently_viewed
        )
        
    except Exception as e:
        print(f"Dashboard error: {e}")
        return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard."""
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    try:
        # Statistics
        books_count = books_table.scan(Select='COUNT')['Count']
        users_count = users_table.scan(Select='COUNT')['Count']
        admins_count = admins_table.scan(Select='COUNT')['Count']
        
        # Recent users
        all_users = users_table.scan()
        recent_users = sorted(
            all_users.get('Items', []),
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )[:5]
        
        # Low stock books
        all_books = scan_books_with_filter()
        low_stock_items = [b for b in all_books if int(b.get('stock', 0)) <= 5]
        low_stock_items.sort(key=lambda x: int(x.get('stock', 0)))
        low_stock_books = [map_book_row(b) for b in low_stock_items[:10]]
        
        # Mock orders
        orders = [
            {'id': '1024', 'customer': 'John Doe', 'date': '2026-01-27', 'items': 3, 'amount': 45.99, 'status': 'Pending'},
            {'id': '1023', 'customer': 'Jane Smith', 'date': '2026-01-26', 'items': 1, 'amount': 12.50, 'status': 'Processing'}
        ]
        
        stats = {
            'total_books': books_count,
            'total_users': users_count,
            'total_admins': admins_count,
            'total_orders': 154,
            'total_revenue': 4520.50
        }
        
        return render_template(
            'admin_dashboard.html',
            username=session['admin'],
            stats=stats,
            recent_users=recent_users,
            low_stock_books=low_stock_books,
            recent_orders=orders
        )
        
    except Exception as e:
        print(f"Admin dashboard error: {e}")
        return redirect(url_for('admin_login'))

# ==================== CART & CHECKOUT ====================

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
    
    shipping = 0 if subtotal > 500 else 50
    if subtotal == 0:
        shipping = 0
    
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
    
    # Initialize cart
    if 'cart' not in session:
        session['cart'] = []
    
    cart = session['cart']
    found = False
    
    for item in cart:
        if item['isbn13'] == isbn13:
            item['quantity'] += quantity
            found = True
            break
    
    if not found:
        # Fetch book from DynamoDB
        try:
            response = books_table.get_item(Key={'isbn13': isbn13})
            book_item = response.get('Item')
            
            if book_item:
                book = map_book_row(book_item)
                cart.append({
                    'isbn13': isbn13,
                    'title': book['title'],
                    'price': book['price'],
                    'image': book['image'],
                    'quantity': quantity
                })
        except Exception as e:
            print(f"Error fetching book: {e}")
            return jsonify({'success': False, 'message': 'Book not found'}), 404
    
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
            item['quantity'] = max(1, quantity)
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
    
    coupons = {
        'BOOK20': {'type': 'percent', 'value': 20, 'desc': '20% Off'},
        'FIRST100': {'type': 'fixed', 'value': 100, 'desc': '₹100 Off'},
        'WELCOME20': {'type': 'percent', 'value': 20, 'desc': 'Welcome Offer'}
    }
    
    if code in coupons:
        session['coupon'] = {'code': code, **coupons[code]}
        return jsonify({'success': True, 'message': f'Coupon {code} applied!'})
    
    return jsonify({'success': False, 'message': 'Invalid coupon code.'})

@app.route('/checkout', methods=['GET'])
def checkout():
    """Checkout page."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cart_items = session.get('cart', [])
    
    if not cart_items:
        return redirect(url_for('cart'))
    
    coupon = session.get('coupon', None)
    
    # Calculate totals
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    discount = 0
    
    if coupon:
        if coupon['type'] == 'percent':
            discount = subtotal * (coupon['value'] / 100)
        elif coupon['type'] == 'fixed':
            discount = coupon['value']
    
    shipping = 0 if subtotal > 500 else 50
    if subtotal == 0:
        shipping = 0
    
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
    
    # Get user
    user = None
    if 'user_id' in session:
        try:
            response = users_table.get_item(Key={'id': session['user_id']})
            user = response.get('Item')
        except:
            pass
    
    return render_template('checkout.html', cart_items=cart_items, totals=totals, coupon=coupon, user=user)

@app.route('/checkout/place-order', methods=['POST'])
def place_order():
    """Place order and send confirmation email."""
    cart_items = session.get('cart', [])
    
    if not cart_items:
        return jsonify({'success': False, 'message': 'Cart is empty'}), 400
    
    try:
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
        
        # Calculate totals
        subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
        coupon = session.get('coupon', None)
        discount = 0
        
        if coupon:
            if coupon['type'] == 'percent':
                discount = subtotal * (coupon['value'] / 100)
            elif coupon['type'] == 'fixed':
                discount = coupon['value']
        
        shipping = 0 if subtotal > 500 else 50
        if subtotal == 0:
            shipping = 0
        
        taxable_amount = max(0, subtotal - discount)
        tax = taxable_amount * 0.18
        total = max(0, subtotal - discount + shipping + tax)
        
        totals = {
            'subtotal': Decimal(str(subtotal)),
            'discount': Decimal(str(discount)),
            'shipping': Decimal(str(shipping)),
            'tax': Decimal(str(tax)),
            'total': Decimal(str(total))
        }
        
        # Generate Order ID
        import secrets
        order_id = f"ORD-{datetime.now().year}-{secrets.token_hex(4).upper()}"
        
        # Verify stock
        for item in cart_items:
            try:
                response = books_table.get_item(Key={'isbn13': item['isbn13']})
                book = response.get('Item')
                
                if not book or int(book.get('stock', 0)) < item['quantity']:
                    return jsonify({
                        'success': False,
                        'message': f"{item['title']} is out of stock"
                    }), 400
            except Exception as e:
                print(f"Stock check error: {e}")
                return jsonify({'success': False, 'message': 'Error checking stock'}), 500
        
        # Insert order
        orders_table.put_item(Item={
            'order_id': order_id,
            'user_id': session.get('user_id', 0),
            'guest_email': email,
            'guest_name': full_name,
            'guest_phone': phone,
            'subtotal': totals['subtotal'],
            'discount': totals['discount'],
            'shipping': totals['shipping'],
            'tax': totals['tax'],
            'total': totals['total'],
            'coupon_code': coupon.get('code') if coupon else '',
            'status': 'Pending',
            'created_at': datetime.now().isoformat()
        })
        
        # Insert order items and update stock
        for item in cart_items:
            order_items_table.put_item(Item={
                'order_id': order_id,
                'isbn13': item['isbn13'],
                'title': item['title'],
                'price': Decimal(str(item['price'])),
                'quantity': item['quantity'],
                'subtotal': Decimal(str(item['price'] * item['quantity']))
            })
            
            # Update stock
            try:
                books_table.update_item(
                    Key={'isbn13': item['isbn13']},
                    UpdateExpression='SET stock = stock - :qty',
                    ExpressionAttributeValues={':qty': item['quantity']}
                )
            except Exception as e:
                print(f"Stock update error: {e}")
        
        # Insert delivery address
        addresses_table.put_item(Item={
            'order_id': order_id,
            'full_name': full_name,
            'phone': phone,
            'address_line1': address1,
            'address_line2': address2 or '',
            'city': city,
            'state': state,
            'pincode': pincode,
            'landmark': landmark or ''
        })
        
        # Clear cart
        session.pop('cart', None)
        session.pop('coupon', None)
        session.modified = True
        
        # TODO: Send email via SNS
        print(f"📧 Order confirmation email would be sent to {email}")
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'message': 'Order placed successfully!'
        })
        
    except Exception as e:
        print(f"Error placing order: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': 'Failed to place order. Please try again.'
        }), 500

@app.route('/order/confirmation/<order_id>')
def order_confirmation(order_id):
    """Order confirmation page."""
    try:
        # Get order
        order_response = orders_table.get_item(Key={'order_id': order_id})
        order = order_response.get('Item')
        
        if not order:
            return redirect(url_for('index'))
        
        # Get order items
        items_response = order_items_table.query(
            KeyConditionExpression=Key('order_id').eq(order_id)
        )
        items = items_response.get('Items', [])
        
        # Get address
        address_response = addresses_table.get_item(Key={'order_id': order_id})
        address = address_response.get('Item')
        
        # Convert Decimals
        order = decimal_to_float(order)
        items = decimal_to_float(items)
        
        return render_template('order_confirmation.html', order=order, items=items, address=address)
        
    except Exception as e:
        print(f"Error fetching order: {e}")
        return redirect(url_for('index'))

# ==================== ADMIN ROUTES ====================

@app.route('/admin/books')
def admin_books():
    """Admin books management page."""
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Search
    search_query = request.args.get('q', '').strip().lower()
    
    # Get all books
    all_books = scan_books_with_filter()
    
    # Filter by search
    if search_query:
        all_books = [
            b for b in all_books
            if search_query in str(b.get('title', '')).lower() or
               search_query in str(b.get('isbn13', '')).lower()
        ]
    
    # Sort by title
    all_books.sort(key=lambda x: str(x.get('title', '')))
    
    total_books = len(all_books)
    offset = (page - 1) * per_page
    paginated_books = all_books[offset:offset + per_page]
    
    books = [map_book_row(b) for b in paginated_books]
    total_pages = math.ceil(total_books / per_page)
    
    return render_template(
        'admin_books.html',
        books=books,
        page=page,
        total_pages=total_pages,
        search_query=search_query
    )

@app.route('/admin/books/add', methods=['GET', 'POST'])
def add_book():
    """Add a new book to the catalog."""
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        authors = request.form.get('authors', '').strip()
        isbn13 = request.form.get('isbn13', '').strip()
        price = request.form.get('price', '').strip()
        stock = request.form.get('stock', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        image = request.form.get('image', '').strip()
        
        if not all([title, authors, isbn13, price, stock]):
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('add_book'))
        
        try:
            # Check if book exists
            response = books_table.get_item(Key={'isbn13': isbn13})
            
            if response.get('Item'):
                flash(f'Book with ISBN {isbn13} already exists.', 'danger')
                return redirect(url_for('add_book'))
            
            # Add book
            books_table.put_item(Item={
                'isbn13': isbn13,
                'title': title,
                'authors': authors,
                'price': Decimal(str(price)),
                'stock': int(stock),
                'categories': category,
                'description': description or '',
                'thumbnail': image or '/static/images/book-placeholder.jpg',
                'average_rating': Decimal('0'),
                'ratings_count': 0,
                'published_year': Decimal(str(datetime.now().year)),
                'num_pages': 0,
                'isbn10': '',
                'subtitle': '',
                'created_at': datetime.now().isoformat()
            })
            
            flash('Book added successfully!', 'success')
            return redirect(url_for('admin_books'))
            
        except Exception as e:
            print(f"Error adding book: {e}")
            flash(f'Error adding book: {str(e)}', 'danger')
    
    categories = get_display_categories()
    return render_template('admin_add_book.html', categories=categories)

@app.route('/admin/books/delete/<isbn13>', methods=['POST'])
def delete_book(isbn13):
    """Delete a book from the catalog."""
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        books_table.delete_item(Key={'isbn13': isbn13})
        return jsonify({'success': True, 'message': 'Book deleted successfully'})
        
    except Exception as e:
        print(f"Error deleting book: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/orders')
def admin_orders():
    """Admin orders management page."""
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    # TODO: Fetch from orders table
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
