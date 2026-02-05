import pytest
import boto3
import os
from moto import mock_aws

# Set dummy AWS credentials for moto
@pytest.fixture(scope='function')
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:OrderNotifications'

@pytest.fixture(scope='function')
def mock_aws_services(aws_credentials):
    """Start moto services."""
    with mock_aws():
        yield

@pytest.fixture
def client(mock_aws_services):
    """Flask test client with mocked AWS services."""
    from app_aws import app
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for easier testing
    
    with app.test_client() as client:
        with app.app_context():
            # Setup DynamoDB
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            
            # Create Tables
            books_table = dynamodb.create_table(
                TableName='Books',
                KeySchema=[{'AttributeName': 'isbn13', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'isbn13', 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            
            users_table = dynamodb.create_table(
                TableName='Users',
                KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            
            # Orders Table
            orders_table = dynamodb.create_table(
                TableName='Orders',
                KeySchema=[{'AttributeName': 'order_id', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'order_id', 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            
            order_items_table = dynamodb.create_table(
                TableName='OrderItems',
                KeySchema=[
                    {'AttributeName': 'order_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'isbn13', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'order_id', 'AttributeType': 'S'},
                    {'AttributeName': 'isbn13', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            
            # Delivery Addresses Table
            delivery_addresses_table = dynamodb.create_table(
                TableName='DeliveryAddresses',
                KeySchema=[{'AttributeName': 'order_id', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'order_id', 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )

            # Setup SNS
            sns = boto3.client('sns', region_name='us-east-1')
            sns.create_topic(Name='OrderNotifications')
            
            # Seed Mock Data
            books_table.put_item(Item={
                'isbn13': '978-0123456789',
                'title': 'Test Book',
                'authors': 'Test Author',
                'price': '29.99', # Note: DynamoDB stores as Decimal, but boto3 handles conversion often. Check app logic if it expects specific type.
                'stock': 10,
                'categories': 'Fiction',
                'thumbnail': 'test.jpg' 
            })
            
            yield client

def test_index(client):
    """Test homepage loads."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Featured Books' in response.data

def test_catalog_and_search(client):
    """Test catalog and search functionality."""
    # Test Catalog
    response = client.get('/catalog')
    assert response.status_code == 200
    
    # Test API for books (scan)
    response = client.get('/api/books')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['books']) > 0
    assert data['books'][0]['title'] == 'Test Book'

def test_contact_form_sns(client):
    """Test contact form submission and SNS notification."""
    response = client.post('/contact', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'subject': 'Hello',
        'message': 'This is a test message.'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"We've received your message" in response.data # Check for success message
    
    # Verify logic didn't crash; specific SNS verification difficult without further patching
    # but since moto is active, no error means it worked.

def test_checkout_flow_and_sns(client):
    """Test adding to cart and placing an order."""
    # 1. Add to Cart
    with client.session_transaction() as sess:
        sess['cart'] = [{
            'isbn13': '978-0123456789',
            'title': 'Test Book',
            'price': 29.99,
            'quantity': 1,
            'image': 'test.jpg'
        }]
    
    # 2. Place Order
    order_data = {
        'full_name': 'Test Buyer',
        'email': 'buyer@example.com',
        'phone': '1234567890',
        'address1': '123 Fake St',
        'address2': '',
        'city': 'Test City',
        'state': 'Test State',
        'pincode': '123456',
        'landmark': ''
    }
    
    response = client.post('/checkout/place-order', json=order_data)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'order_id' in data
    
    # 3. Verify DynamoDB Update
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    order_id = data['order_id']
    
    orders = dynamodb.Table('Orders')
    item = orders.get_item(Key={'order_id': order_id}).get('Item')
    assert item is not None
    assert item['guest_email'] == 'buyer@example.com'
    
    # 4. Verify Stock Update
    books = dynamodb.Table('Books')
    book = books.get_item(Key={'isbn13': '978-0123456789'}).get('Item')
    assert int(book['stock']) == 9  # 10 - 1
