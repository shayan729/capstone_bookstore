import boto3
import sqlite3
import os
import sys
from decimal import Decimal

# DB Configuration
SQLITE_DB_PATH = 'instance/bookstore.db'


def get_dynamodb_resource():
    region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    endpoint_url = os.getenv('AWS_ENDPOINT_URL')

    if endpoint_url:
        return boto3.resource(
            'dynamodb',
            region_name=region,
            endpoint_url=endpoint_url,
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )

    return boto3.resource('dynamodb', region_name=region)


def get_sqlite_conn():
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"SQLite database not found at {SQLITE_DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def convert_float_to_decimal(data):
    if isinstance(data, (int, float)):
        return Decimal(str(data))
    elif isinstance(data, dict):
        return {k: convert_float_to_decimal(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_float_to_decimal(v) for v in data]
    return data


def migrate_table(sqlite_conn, dynamo_table, query, mapper_func):
    print(f"Migrating table '{dynamo_table.name}'...")
    rows = sqlite_conn.execute(query).fetchall()

    if not rows:
        print(f"No data found for {dynamo_table.name}")
        return

    with dynamo_table.batch_writer() as batch:
        for row in rows:
            item = mapper_func(row)

            # CRITICAL FIX: ensure partition key exists
            if 'id' in item and item['id'] is None:
                continue

            item = convert_float_to_decimal(item)
            item = {k: v for k, v in item.items() if v is not None}
            batch.put_item(Item=item)


    print(f"Completed migration for '{dynamo_table.name}'")


# ------------------ MAPPERS ------------------

def map_book(row):
    return {
        'isbn13': str(row['isbn13']),
        'isbn10': row['isbn10'] or '',
        'title': row['title'],
        'subtitle': row['subtitle'] or '',
        'authors': row['authors'] or 'Unknown',
        'categories': row['categories'] or 'Uncategorized',
        'thumbnail': row['thumbnail'] or '',
        'description': row['description'] or '',
        'published_year': row['published_year'],
        'average_rating': row['average_rating'],
        'num_pages': row['num_pages'],
        'ratings_count': row['ratings_count'],
        'price': row['price'],
        'stock': row['stock']
    }


def map_user(row):
    return {
        'id': int(row['id']),
        'username': row['username'],
        'email': row['email'],
        'password_hash': row['password_hash'],
        'full_name': row['full_name'] or '',
        'role': row['role'],
        'created_at': str(row['created_at']),
        'last_login': str(row['last_login']) if row['last_login'] else ''
    }


def map_admin(row):
    return {
        'id': int(row['id']),
        'username': row['username'],
        'email': row['email'],
        'password_hash': row['password_hash'],
        'full_name': row['full_name'] or '',
        'created_at': str(row['created_at']),
        'last_login': str(row['last_login']) if row['last_login'] else ''
    }


def map_order(row):
    item = {
        'order_id': str(row['order_id']),
        'guest_email': row['guest_email'] or '',
        'guest_name': row['guest_name'] or '',
        'guest_phone': row['guest_phone'] or '',
        'subtotal': row['subtotal'],
        'discount': row['discount'],
        'shipping': row['shipping'],
        'tax': row['tax'],
        'total': row['total'],
        'coupon_code': row['coupon_code'] or '',
        'status': row['status'],
        'created_at': str(row['created_at'])
    }

    # CRITICAL FIX: only include user_id if present
    if row['user_id'] is not None:
        item['user_id'] = int(row['user_id'])

    return item


def map_order_item(row):
    return {
        'order_id': str(row['order_id']),
        'isbn13': str(row['isbn13']),
        'title': row['title'],
        'author': row['author'] or '',
        'price': row['price'],
        'quantity': row['quantity'],
        'subtotal': row['subtotal']
    }


def map_address(row):
    return {
        'order_id': str(row['order_id']),
        'full_name': row['full_name'],
        'phone': row['phone'],
        'address_line1': row['address_line1'],
        'address_line2': row['address_line2'] or '',
        'city': row['city'],
        'state': row['state'],
        'pincode': row['pincode'],
        'landmark': row['landmark'] or ''
    }


# ------------------ MAIN ------------------

def main():
    print("Starting SQLite → DynamoDB migration")

    dynamodb = get_dynamodb_resource()
    conn = get_sqlite_conn()

    migrate_table(conn, dynamodb.Table('Users'), "SELECT * FROM users", map_user)
    migrate_table(conn, dynamodb.Table('Admins'), "SELECT * FROM admins", map_admin)
    migrate_table(conn, dynamodb.Table('Orders'), "SELECT * FROM orders", map_order)
    migrate_table(conn, dynamodb.Table('OrderItems'), "SELECT * FROM order_items", map_order_item)
    migrate_table(conn, dynamodb.Table('DeliveryAddresses'), "SELECT * FROM delivery_addresses", map_address)
    migrate_table(conn, dynamodb.Table('Books'), "SELECT * FROM books", map_book)

    conn.close()
    print("Migration completed successfully")


if __name__ == "__main__":
    main()
