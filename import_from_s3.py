#!/usr/bin/env python3
"""
Import data from S3 into DynamoDB using schema-consistent tables.
"""

import boto3
import json
import time
from dotenv import load_dotenv
import os

load_dotenv()

S3_BUCKET = 'bookstore-migration-data'
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

dynamodb = boto3.client('dynamodb', region_name=AWS_REGION)

# Load schema definitions
with open('dynamodb_schema.json', 'r') as f:
    SCHEMAS = json.load(f)

def import_table(table_config, csv_filename):
    """Import a single table from S3."""
    table_name = table_config['TableName']
    
    try:
        print(f"\n📥 Importing {table_name} from s3://{S3_BUCKET}/import/{csv_filename}")
        
        response = dynamodb.import_table(
            S3BucketSource={
                'S3Bucket': S3_BUCKET,
                'S3KeyPrefix': f'import/{csv_filename}'
            },
            InputFormat='CSV',
            InputFormatOptions={
                'Csv': {
                    'Delimiter': ',',
                    'HeaderList': table_config['Headers']
                }
            },
            TableCreationParameters={
                'TableName': table_config['TableName'],
                'KeySchema': table_config['KeySchema'],
                'AttributeDefinitions': table_config['AttributeDefinitions'],
                'BillingMode': table_config['BillingMode'],
                'GlobalSecondaryIndexes': table_config.get('GlobalSecondaryIndexes', [])
            }
        )
        
        import_arn = response['ImportTableDescription']['ImportArn']
        print(f"✅ Import started: {import_arn}")
        
        return import_arn
        
    except Exception as e:
        print(f"❌ Error importing {table_name}: {e}")
        return None

def check_import_status(import_arn):
    """Check import status."""
    try:
        response = dynamodb.describe_import(ImportArn=import_arn)
        status = response['ImportTableDescription']['ImportStatus']
        
        if status == 'COMPLETED':
            imported_items = response['ImportTableDescription'].get('ImportedItemCount', 0)
            processed_items = response['ImportTableDescription'].get('ProcessedItemCount', 0)
            print(f"   ✅ {status} - Imported: {imported_items:,} | Processed: {processed_items:,}")
        elif status == 'FAILED':
            error = response['ImportTableDescription'].get('FailureMessage', 'Unknown error')
            print(f"   ❌ {status} - {error}")
        else:
            print(f"   ⏳ {status}")
        
        return status
        
    except Exception as e:
        print(f"   Error: {e}")
        return 'ERROR'

def wait_for_import(import_arn, table_name, timeout=3600):
    """Wait for import to complete."""
    print(f"\n⏳ Waiting for {table_name} import...")
    
    start_time = time.time()
    last_check = 0
    
    while True:
        elapsed = time.time() - start_time
        
        # Check every 30 seconds
        if elapsed - last_check >= 30:
            status = check_import_status(import_arn)
            last_check = elapsed
            
            if status == 'COMPLETED':
                print(f"✅ {table_name} import completed in {elapsed:.1f}s!")
                return True
            elif status in ['FAILED', 'CANCELLED', 'ERROR']:
                print(f"❌ {table_name} import failed!")
                return False
        
        if elapsed > timeout:
            print(f"⏱️ Timeout after {timeout}s")
            return False
        
        time.sleep(5)

def import_all_tables():
    """Import all tables from S3."""
    
    imports = [
        ('Books', 'books.csv'),
        ('Users', 'users.csv'),
        ('Admins', 'admins.csv'),
        ('Orders', 'orders.csv'),
        ('OrderItems', 'order_items.csv'),
        ('DeliveryAddresses', 'delivery_addresses.csv')
    ]
    
    import_jobs = []
    
    for table_name, csv_file in imports:
        table_config = SCHEMAS[table_name]
        import_arn = import_table(table_config, csv_file)
        
        if import_arn:
            import_jobs.append((table_name, import_arn))
        
        time.sleep(2)  # Small delay between import requests
    
    # Wait for all imports
    print("\n" + "=" * 60)
    print("⏳ MONITORING IMPORT PROGRESS")
    print("=" * 60)
    
    results = []
    for table_name, import_arn in import_jobs:
        success = wait_for_import(import_arn, table_name)
        results.append((table_name, success))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 IMPORT SUMMARY")
    print("=" * 60)
    
    for table_name, success in results:
        status = "✅ Success" if success else "❌ Failed"
        print(f"   {table_name}: {status}")

if __name__ == '__main__':
    print("=" * 60)
    print("📥 IMPORTING DATA FROM S3 TO DYNAMODB")
    print("=" * 60)
    
    import_all_tables()
    
    print("\n" + "=" * 60)
    print("✅ IMPORT PROCESS COMPLETE!")
    print("=" * 60)
