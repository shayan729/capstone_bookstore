#!/usr/bin/env python3
import boto3
import sqlite3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
conn = sqlite3.connect('instance/bookstore.db')

tables = ['Books', 'Users', 'Admins', 'Orders', 'OrderItems', 'DeliveryAddresses']
sqlite_tables = ['books', 'users', 'admins', 'orders', 'order_items', 'delivery_addresses']

print("=" * 60)
print("🔍 VERIFYING MIGRATION")
print("=" * 60)

for dynamo_table, sqlite_table in zip(tables, sqlite_tables):
    # Count in DynamoDB
    table = dynamodb.Table(dynamo_table)
    dynamo_count = table.scan(Select='COUNT')['Count']
    
    # Count in SQLite
    cursor = conn.execute(f'SELECT COUNT(*) FROM {sqlite_table}')
    sqlite_count = cursor.fetchone()[0]
    
    match = "✅" if dynamo_count == sqlite_count else "❌"
    print(f"{match} {dynamo_table:20s} - SQLite: {sqlite_count:5d} | DynamoDB: {dynamo_count:5d}")

conn.close()
print("=" * 60)
