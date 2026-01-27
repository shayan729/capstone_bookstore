import sqlite3
import os

# Define the database path
DB_PATH = os.path.join('instance', 'bookstore.db')

# Ensure instance directory exists
os.makedirs('instance', exist_ok=True)

# Mock Data to seed
books_data = [
    {
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
        'pub_date': 1925
    },
    {
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
        'pub_date': 1960
    },
    {
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
        'pub_date': 1949
    },
    {
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
        'pub_date': 1813
    },
    {
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
        'pub_date': 1951
    },
    {
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
        'pub_date': 1937
    },
    {
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
        'pub_date': 2014
    },
    {
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
        'pub_date': 1988
    },
    {
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
        'pub_date': 2018
    },
    {
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
        'pub_date': 2018
    },
    {
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
        'pub_date': 1997
    },
    {
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
        'pub_date': 1969
    },
     {
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
        'pub_date': 1965
    },
    {
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
        'pub_date': 2011
    },
    {
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
        'pub_date': 2008
    },
    {
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
        'pub_date': 2009
    }
]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    
    # Read schema
    with open('schema.sql', 'r') as f:
        schema = f.read()
    
    # Execute schema
    conn.executescript(schema)
    
    # Check if books already exist
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM books")
    count = cur.fetchone()[0]
    
    if count == 0:
        print("Seeding database...")
        for book in books_data:
            cur.execute("""
                INSERT INTO books (title, authors, categories, price, stock, thumbnail, description, isbn13, published_year, average_rating, num_pages)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                book['title'], 
                book['author'], 
                book['category'], 
                book['price'], 
                book['stock'], 
                book['image'], 
                book['description'], 
                book['isbn'], 
                book.get('pub_date', 2000), 
                book['rating'],
                book.get('pages', 200)
            ))
        print("Database seeded successfully.")
    else:
        print("Database already contains data.")
        
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
