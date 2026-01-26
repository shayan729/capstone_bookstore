from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import math
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Configuration for File Uploads
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Extended Mock Data
books = [
    {
        'id': 1, 
        'title': 'The Great Gatsby', 
        'author': 'F. Scott Fitzgerald', 
        'category': 'Fiction', 
        'price': 12.99, 
        'stock': 15, 
        'image': 'https://placehold.co/400x600?text=Gatsby',
        'rating': 4.5,
        'description': 'The Great Gatsby is a 1925 novel by American writer F. Scott Fitzgerald. Set in the Jazz Age on Long Island, near New York City, the novel depicts first-person narrator Nick Carraway\'s interactions with mysterious millionaire Jay Gatsby and Gatsby\'s obsession to reunite with his former lover, Daisy Buchanan.',
        'isbn': '978-0743273565',
        'publisher': 'Scribner',
        'pages': 180,
        'language': 'English',
        'pub_date': 'April 10, 1925',
        'reviews': [
            {'user': 'John Doe', 'rating': 5, 'text': 'A masterpiece of American literature.', 'date': '2025-01-15'},
            {'user': 'Jane Smith', 'rating': 4, 'text': 'Enjoyed it, but the ending was tragic.', 'date': '2025-01-20'}
        ]
    },
    {
        'id': 2, 
        'title': 'To Kill a Mockingbird', 
        'author': 'Harper Lee', 
        'category': 'Fiction', 
        'price': 14.50, 
        'stock': 8, 
        'image': 'https://placehold.co/400x600?text=Mockingbird',
        'rating': 4.8,
        'description': 'To Kill a Mockingbird is a novel by the American author Harper Lee. It was published in 1960 and was instantly successful. In the United States, it is widely read in high schools and middle schools. To Kill a Mockingbird has become a classic of modern American literature, winning the Pulitzer Prize.',
        'isbn': '978-0061120084',
        'publisher': 'Harper Perennial',
        'pages': 324,
        'language': 'English',
        'pub_date': 'July 11, 1960',
        'reviews': [
            {'user': 'Alice', 'rating': 5, 'text': 'Must read for everyone.', 'date': '2024-12-05'}
        ]
    },
    {
        'id': 3, 
        'title': '1984', 
        'author': 'George Orwell', 
        'category': 'Science Fiction', 
        'price': 11.99, 
        'stock': 0, 
        'image': 'https://placehold.co/400x600?text=1984',
        'rating': 4.7,
        'description': 'Nineteen Eighty-Four is a dystopian social science fiction novel and cautionary tale written by the English novelist George Orwell. Thematic focus of the novel includes totalitarianism, mass surveillance, and repressive regimentation of persons and behaviours within society.',
        'isbn': '978-0451524935',
        'publisher': 'Signet Classic',
        'pages': 328,
        'language': 'English',
        'pub_date': 'June 8, 1949',
        'reviews': []
    },
    {
        'id': 4, 
        'title': 'Pride and Prejudice', 
        'author': 'Jane Austen', 
        'category': 'Romance', 
        'price': 9.99, 
        'stock': 20, 
        'image': 'https://placehold.co/400x600?text=Pride',
        'rating': 4.6,
        'description': 'Pride and Prejudice is an 1813 novel of manners by Jane Austen. The novel follows the character development of Elizabeth Bennet, the dynamic protagonist of the book who learns about the repercussions of hasty judgments and comes to appreciate the difference between superficial goodness and actual goodness.',
        'isbn': '978-1503290563',
        'publisher': 'CreateSpace',
        'pages': 279,
        'language': 'English',
        'pub_date': 'January 28, 1813',
        'reviews': []
    },
    {
        'id': 5, 
        'title': 'The Catcher in the Rye', 
        'author': 'J.D. Salinger', 
        'category': 'Fiction', 
        'price': 13.00, 
        'stock': 12, 
        'image': 'https://placehold.co/400x600?text=Catcher',
        'rating': 4.0,
        'description': 'The Catcher in the Rye is a novel by J. D. Salinger, partially published in serial form in 1945–1946 and as a novel in 1951. It was originally intended for adults but is often read by adolescents for its themes of angst, alienation, and as a critique on superficiality in society.',
        'isbn': '978-0316769488',
        'publisher': 'Little, Brown and Company',
        'pages': 277,
        'language': 'English',
        'pub_date': 'July 16, 1951',
        'reviews': []
    },
    {
        'id': 6, 
        'title': 'The Hobbit', 
        'author': 'J.R.R. Tolkien', 
        'category': 'Fantasy', 
        'price': 15.99, 
        'stock': 25, 
        'image': 'https://placehold.co/400x600?text=Hobbit',
        'rating': 4.8,
        'description': 'The Hobbit, or There and Back Again is a children\'s fantasy novel by English author J. R. R. Tolkien. It was published on 21 September 1937 to wide critical acclaim, being nominated for the Carnegie Medal and awarded a prize from the New York Herald Tribune for best juvenile fiction.',
        'isbn': '978-0547928227',
        'publisher': 'Houghton Mifflin Harcourt',
        'pages': 300,
        'language': 'English',
        'pub_date': 'September 21, 1937',
        'reviews': []
    },
    {
        'id': 7, 
        'title': 'Sapiens', 
        'author': 'Yuval Noah Harari', 
        'category': 'Non-Fiction', 
        'price': 22.00, 
        'stock': 10, 
        'image': 'https://placehold.co/400x600?text=Sapiens',
        'rating': 4.6,
        'description': 'Sapiens: A Brief History of Humankind is a book by Yuval Noah Harari, first published in Hebrew in Israel in 2011 based on a series of lectures Harari taught at The Hebrew University of Jerusalem, and in English in 2014.',
        'isbn': '978-0062316097',
        'publisher': 'Harper',
        'pages': 443,
        'language': 'English',
        'pub_date': '2014',
        'reviews': []
    },
    {
        'id': 8, 
        'title': 'A Brief History of Time', 
        'author': 'Stephen Hawking', 
        'category': 'Science', 
        'price': 18.50, 
        'stock': 5, 
        'image': 'https://placehold.co/400x600?text=Time',
        'rating': 4.5,
        'description': 'A Brief History of Time: From the Big Bang to Black Holes is a book on theoretical cosmology by English physicist Stephen Hawking. It was first published in 1988. Hawking wrote the book for readers without prior knowledge of physics and people who are interested in learning something new.',
        'isbn': '978-0553380163',
        'publisher': 'Bantam',
        'pages': 212,
        'language': 'English',
        'pub_date': '1988',
        'reviews': []
    },
    {
        'id': 9, 
        'title': 'Educated', 
        'author': 'Tara Westover', 
        'category': 'Memoir', 
        'price': 16.00, 
        'stock': 14, 
        'image': 'https://placehold.co/400x600?text=Educated',
        'rating': 4.7,
        'description': 'Educated is a memoir by the American author Tara Westover. Westover chronicles her journey from scraping metal in a junkyard to seeking education at Brigham Young University, Cambridge University, and Harvard University.',
        'isbn': '978-0399590504',
        'publisher': 'Random House',
        'pages': 334,
        'language': 'English',
        'pub_date': 'February 20, 2018',
        'reviews': []
    },
    {
        'id': 10, 
        'title': 'Becoming', 
        'author': 'Michelle Obama', 
        'category': 'Memoir', 
        'price': 19.99, 
        'stock': 30, 
        'image': 'https://placehold.co/400x600?text=Becoming',
        'rating': 4.8,
        'description': 'Becoming is the memoir of former United States First Lady Michelle Obama, published in 2018. Described by the author as a deeply personal experience, the book talks about her roots and how she found her voice, as well as her time in the White House, her public health campaign, and her role as a mother.',
        'isbn': '978-1524763138',
        'publisher': 'Crown',
        'pages': 426,
        'language': 'English',
        'pub_date': 'November 13, 2018',
        'reviews': []
    },
    {
        'id': 11, 
        'title': 'Harry Potter and the Sorcerer\'s Stone', 
        'author': 'J.K. Rowling', 
        'category': 'Children\'s', 
        'price': 24.99, 
        'stock': 50, 
        'image': 'https://placehold.co/400x600?text=Potter',
        'rating': 4.9,
        'description': 'Harry Potter and the Philosopher\'s Stone is a fantasy novel written by British author J. K. Rowling. It is the first novel in the Harry Potter series and debut novel by the author. It follows Harry Potter, a young wizard who discovers his magical heritage on his eleventh birthday, when he receives a letter of acceptance to Hogwarts School of Witchcraft and Wizardry.',
        'isbn': '978-0590353427',
        'publisher': 'Scholastic',
        'pages': 309,
        'language': 'English',
        'pub_date': 'June 26, 1997',
        'reviews': []
    },
    {
        'id': 12, 
        'title': 'The Very Hungry Caterpillar', 
        'author': 'Eric Carle', 
        'category': 'Children\'s', 
        'price': 8.99, 
        'stock': 40, 
        'image': 'https://placehold.co/400x600?text=Caterpillar',
        'rating': 4.8,
        'description': 'The Very Hungry Caterpillar is a children\'s picture book designed, illustrated, and written by Eric Carle. It features a caterpillar who eats his way through a variety of different food objects before pupating and emerging as a butterfly.',
        'isbn': '978-0399226908',
        'publisher': 'Philomel Books',
        'pages': 22,
        'language': 'English',
        'pub_date': 'June 3, 1969',
        'reviews': []
    },
     {
        'id': 13, 
        'title': 'Dune', 
        'author': 'Frank Herbert', 
        'category': 'Science Fiction', 
        'price': 20.00, 
        'stock': 18, 
        'image': 'https://placehold.co/400x600?text=Dune',
        'rating': 4.6,
        'description': 'Dune is a 1965 epic science fiction novel by American author Frank Herbert. Set in the distant future amidst a feudal interstellar society in which various noble houses control planetary fiefs, it tells the story of young Paul Atreides, whose family accepts the stewardship of the planet Arrakis.',
        'isbn': '978-0441172719',
        'publisher': 'Ace',
        'pages': 412,
        'language': 'English',
        'pub_date': 'August 1965',
        'reviews': []
    },
    {
        'id': 14, 
        'title': 'Thinking, Fast and Slow', 
        'author': 'Daniel Kahneman', 
        'category': 'Non-Fiction', 
        'price': 17.50, 
        'stock': 7, 
        'image': 'https://placehold.co/400x600?text=Thinking',
        'rating': 4.4,
        'description': 'Thinking, Fast and Slow is a 2011 book by the Nobel Memorial Prize in Economic Sciences laureate Daniel Kahneman. The book summarizes research that Kahneman conducted over decades, often in collaboration with Amos Tversky.',
        'isbn': '978-0374275631',
        'publisher': 'Farrar, Straus and Giroux',
        'pages': 499,
        'language': 'English',
        'pub_date': 'October 25, 2011',
        'reviews': []
    },
    {
        'id': 15, 
        'title': 'Clean Code', 
        'author': 'Robert C. Martin', 
        'category': 'Academic', 
        'price': 45.00, 
        'stock': 11, 
        'image': 'https://placehold.co/400x600?text=Code',
        'rating': 4.7,
        'description': 'Clean Code: A Handbook of Agile Software Craftsmanship is a book by Robert C. Martin. It describes the principles and best practices of writing clean and maintainable code.',
        'isbn': '978-0132350884',
        'publisher': 'Prentice Hall',
        'pages': 464,
        'language': 'English',
        'pub_date': 'August 1, 2008',
        'reviews': []
    },
    {
        'id': 16, 
        'title': 'Introduction to Algorithms', 
        'author': 'Thomas H. Cormen', 
        'category': 'Academic', 
        'price': 85.00, 
        'stock': 3, 
        'image': 'https://placehold.co/400x600?text=Algorithms',
        'rating': 4.5,
        'description': 'Introduction to Algorithms is a book on computer programming and algorithms by Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, and Clifford Stein. The book has been widely used as the textbook for algorithms courses at many universities and is commonly cited as a reference for algorithms in published papers.',
        'isbn': '978-0262033848',
        'publisher': 'MIT Press',
        'pages': 1312,
        'language': 'English',
        'pub_date': '2009',
        'reviews': []
    }
]

# In-memory database (dictionary)
users = {}
admin_users = {}
projects = []  
enrollments = {} 

@app.route('/book/<int:book_id>')
def product_details(book_id):
    book = next((b for b in books if b['id'] == book_id), None)
    if not book:
        return "Book not found", 404
        
    related_books = [b for b in books if b['category'] == book['category'] and b['id'] != book['id']][:4]
    
    return render_template('product_details.html', book=book, related_books=related_books) 

@app.route('/catalog')
def catalog():
    return render_template('catalog.html')

@app.route('/api/books')
def get_books():
    # Filtering logic
    filtered = books.copy()
    
    query = request.args.get('q', '').lower()
    if query:
        filtered = [b for b in filtered if query in b['title'].lower() or query in b['author'].lower()]
        
    category = request.args.get('category')
    if category and category != 'All':
        filtered = [b for b in filtered if b['category'] == category]
        
    price_max = float(request.args.get('price_max', 2000))
    # Assuming price is in dollars for now, mapping loosely to user request of 2000 rupees (approx $24, but let's keep mock data scale)
    # Actually user said 0-2000 RUPEES. Mock data is $8-$85. 
    # Let's assume input is handling the scale or we treat mock prices as comparable units for now.
    # To be consistent with "Rs" symbol in UI, let's treat mock values as valid numbers and just filter numerically.
    filtered = [b for b in filtered if b['price'] <= price_max]
    
    author = request.args.get('author', '').lower()
    if author:
        filtered = [b for b in filtered if author in b['author'].lower()]
        
    in_stock = request.args.get('in_stock') == 'true'
    if in_stock:
        filtered = [b for b in filtered if b['stock'] > 0]
        
    # Sorting
    sort_by = request.args.get('sort', 'newest')
    if sort_by == 'price_low':
        filtered.sort(key=lambda x: x['price'])
    elif sort_by == 'price_high':
        filtered.sort(key=lambda x: x['price'], reverse=True)
    elif sort_by == 'az':
        filtered.sort(key=lambda x: x['title'])
    # 'newest' assumed default order or id order
        
    # Pagination
    page = int(request.args.get('page', 1))
    per_page = 8
    total_books = len(filtered)
    total_pages = math.ceil(total_books / per_page)
    
    start = (page - 1) * per_page
    end = start + per_page
    paginated_books = filtered[start:end]
    
    return jsonify({
        'books': paginated_books,
        'total': total_books,
        'page': page,
        'pages': total_pages
    }) 

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Extract form data
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Here you would typically send an email or save to DB
        # For now, we'll just flash a message (requires flash support in base.html logic if we use flash)
        # Or we can pass a success flag to the template
        
        return render_template('contact.html', success=True)
        
    return render_template('contact.html')

@app.route('/')
def index():
    if 'username' in session:
        # For the purpose of this task, we want to show the new homepage even if logged in, 
        # or maybe redirect to home. The user request didn't specify, but usually homepage is visible.
        # But existing code redirects to 'home'. Let's keep it but maybe 'home' should also use the new design?
        # The user asked for a "Homepage", which usually implies the landing page. 
        # Let's modify the index route to render the new homepage ALWAYS, but with logged-in state handling in base.html.
        pass
    
    # Mock Data for Homepage
    featured_books = [
        {'title': 'The Great Gatsby', 'author': 'F. Scott Fitzgerald', 'price': 12.99, 'image': 'https://placehold.co/200x300?text=Gatsby'},
        {'title': 'To Kill a Mockingbird', 'author': 'Harper Lee', 'price': 14.50, 'image': 'https://placehold.co/200x300?text=Mockingbird'},
        {'title': '1984', 'author': 'George Orwell', 'price': 11.99, 'image': 'https://placehold.co/200x300?text=1984'},
        {'title': 'Pride and Prejudice', 'author': 'Jane Austen', 'price': 9.99, 'image': 'https://placehold.co/200x300?text=Pride'},
        {'title': 'The Catcher in the Rye', 'author': 'J.D. Salinger', 'price': 13.00, 'image': 'https://placehold.co/200x300?text=Catcher'},
        {'title': 'The Hobbit', 'author': 'J.R.R. Tolkien', 'price': 15.99, 'image': 'https://placehold.co/200x300?text=Hobbit'}
    ]
    
    testimonials = [
        {'name': 'Alice Johnson', 'role': 'Student', 'text': 'BookStore Manager helped me find all my textbooks at great prices!'},
        {'name': 'Mark Smith', 'role': 'Avid Reader', 'text': 'The collection is amazing and delivery was super fast.'},
        {'name': 'Sarah Lee', 'role': 'Teacher', 'text': 'A wonderful resource for our local community. Highly recommended!'}
    ]
    
    return render_template('index.html', featured_books=featured_books, testimonials=testimonials)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users:
            return "User already exists!"
        
        users[username] = password
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('home'))
        return "Invalid credentials!"
    return render_template('login.html')

@app.route('/home')
def home():
    if 'username' in session:
        username = session['username']
        user_enrollments_ids = enrollments.get(username, [])
        
        my_projects = [p for p in projects if p['id'] in user_enrollments_ids]
        
        return render_template('home.html', username=username, my_projects=my_projects)
    return redirect(url_for('login'))

@app.route('/projects')
def projects_list():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    username = session['username']
    user_enrollments_ids = enrollments.get(username, [])
    
    return render_template('projects_list.html', projects=projects, user_enrollments=user_enrollments_ids)

@app.route('/enroll/<int:project_id>')
def enroll(project_id):
    if 'username' not in session:
        return redirect(url_for('login'))
        
    username = session['username']
    
    if username not in enrollments:
        enrollments[username] = []
        
    if project_id not in enrollments[username]:
        enrollments[username].append(project_id)
        
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

# Admin Routes
@app.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in admin_users:
            return "Admin already exists!"
        
        admin_users[username] = password
        return redirect(url_for('admin_login'))
    return render_template('admin_signup.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in admin_users and admin_users[username] == password:
            session['admin'] = username
            return redirect(url_for('admin_dashboard'))
        return "Invalid admin credentials!"
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html', username=session['admin'], projects=projects, users=users, enrollments=enrollments)

@app.route('/admin/create-project', methods=['GET', 'POST'])
def admin_create_project():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
        
    if request.method == 'POST':
        title = request.form['title']
        problem_statement = request.form['problem_statement']
        solution_overview = request.form['solution_overview']
        
        # Handle File Uploads
        image = request.files['image']
        document = request.files['document']
        
        image_filename = None
        doc_filename = None

        if image:
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            
        if document:
            doc_filename = secure_filename(document.filename)
            document.save(os.path.join(app.config['UPLOAD_FOLDER'], doc_filename))
            
        # Create Project ID (simple auto-increment)
        project_id = len(projects) + 1
        
        new_project = {
            'id': project_id,
            'title': title,
            'problem_statement': problem_statement,
            'solution_overview': solution_overview,
            'image': image_filename,
            'document': doc_filename
        }
        
        projects.append(new_project)
        return redirect(url_for('admin_dashboard'))
        
    return render_template('admin_create_project.html', username=session['admin'])

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)