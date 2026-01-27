# config.py
import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/bookstore.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Local development settings
    DEBUG = True
    TESTING = False
    
    # Session settings
    SESSION_COOKIE_SECURE = False  # True in production with HTTPS
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes

class AWSConfig(Config):
    """AWS deployment configuration (Stage 2)."""
    DEBUG = False
    # Will add DynamoDB settings later
    # DYNAMODB_TABLE = 'bookstore-books'
    # SNS_TOPIC_ARN = 'arn:aws:sns:...'
