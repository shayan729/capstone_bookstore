import boto3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
books_table = dynamodb.Table('Books')

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

def normalize_dynamodb():
    print("Starting DynamoDB Category Normalization...")
    
    count = 0
    # Create lookup map for faster processing
    lookup = {}
    for standard_cat, variants in MAPPING.items():
        for v in variants:
            lookup[v.lower()] = standard_cat
        lookup[standard_cat.lower()] = standard_cat  # Ensure exact matches work

    try:
        # Scan all books
        response = books_table.scan()
        items = response.get('Items', [])
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = books_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
        
        print(f"Scanned {len(items)} books.")

        for item in items:
            isbn13 = item.get('isbn13')
            original = item.get('categories')
            
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
                # Update DynamoDB
                # We update 'categories' field. 
                # Note: This updates the item one by one. For large datasets, batch writer is better but requires deleting and re-putting or correct logic.
                # Since update_item is atomic, it is safer here.
                
                try:
                    books_table.update_item(
                        Key={'isbn13': isbn13},
                        UpdateExpression='SET categories = :n',
                        ExpressionAttributeValues={':n': normalized}
                    )
                    count += 1
                    # print(f"Updated {isbn13}: '{original}' -> '{normalized}'")
                except Exception as e:
                    print(f"Failed to update {isbn13}: {e}")

        print(f"Successfully normalized {count} records in DynamoDB.")
        
    except Exception as e:
        print(f"Error during normalization: {e}")

if __name__ == '__main__':
    normalize_dynamodb()
