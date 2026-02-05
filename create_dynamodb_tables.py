import boto3
import json
import os
import sys
from botocore.exceptions import ClientError

DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")


def get_dynamodb_resource():
    try:
        dynamodb = boto3.resource("dynamodb", region_name=DEFAULT_REGION)
        dynamodb.meta.client.list_tables()
        print(f"Connected to DynamoDB in region: {DEFAULT_REGION}")
        return dynamodb
    except Exception as e:
        print(f"Failed to connect to DynamoDB: {e}")
        sys.exit(1)


def table_exists(dynamodb, table_name: str) -> bool:
    try:
        dynamodb.meta.client.describe_table(TableName=table_name)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            return False
        raise


def create_table(dynamodb, schema: dict):
    table_name = schema["TableName"]

    if table_exists(dynamodb, table_name):
        print(f"Table already exists: {table_name} (skipping)")
        return

    params = {
        "TableName": table_name,
        "KeySchema": schema["KeySchema"],
        "AttributeDefinitions": schema["AttributeDefinitions"],
        "BillingMode": schema.get("BillingMode", "PAY_PER_REQUEST"),
    }

    if "GlobalSecondaryIndexes" in schema:
        params["GlobalSecondaryIndexes"] = schema["GlobalSecondaryIndexes"]

    if "LocalSecondaryIndexes" in schema:
        params["LocalSecondaryIndexes"] = schema["LocalSecondaryIndexes"]

    print(f"Creating table: {table_name}")
    table = dynamodb.create_table(**params)

    print(f"Waiting for table to become ACTIVE: {table_name}")
    table.wait_until_exists()
    print(f"Table created successfully: {table_name}")


def main():
    schema_file = "dynamo_schema.json"

    if not os.path.exists(schema_file):
        print(f"Schema file not found: {schema_file}")
        sys.exit(1)

    with open(schema_file, "r") as f:
        full_schema = json.load(f)

    dynamodb = get_dynamodb_resource()

    for _, schema in full_schema.items():
        try:
            create_table(dynamodb, schema)
        except ClientError as e:
            print(f"AWS error creating table {schema.get('TableName')}: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


if __name__ == "__main__":
    print("Starting DynamoDB table creation")
    main()
    print("DynamoDB table setup completed")
