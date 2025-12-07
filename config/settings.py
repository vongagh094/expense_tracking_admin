"""
Application configuration management.

This module handles environment-based configuration for the Firebase Admin Dashboard,
including Firebase credentials, project settings, and application parameters.
"""

import os
from typing import Optional


class Config:
    """Application configuration class with environment variable support."""
    
    # Firebase Configuration
    FIREBASE_PROJECT_ID: str = os.getenv('FIREBASE_PROJECT_ID', 'vneid-default')
    FIREBASE_CREDENTIALS_PATH: Optional[str] = os.getenv('FIREBASE_CREDENTIALS_PATH')
    FIREBASE_CREDENTIALS_JSON: Optional[str] = os.getenv('FIREBASE_CREDENTIALS_JSON')
    
    # Application Configuration
    DEBUG_MODE: bool = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Admin Configuration
    ADMIN_EMAIL_DOMAIN: str = os.getenv('ADMIN_EMAIL_DOMAIN', '@admin.vneid.com')
    ALLOWED_ADMIN_EMAILS: list = [
        email.strip() for email in os.getenv('ALLOWED_ADMIN_EMAILS', '').split(',') 
        if email.strip()
    ]
    
    # UI Configuration
    PAGE_SIZE: int = int(os.getenv('PAGE_SIZE', '20'))
    MAX_SEARCH_RESULTS: int = int(os.getenv('MAX_SEARCH_RESULTS', '100'))
    
    # Security Configuration
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv('SESSION_TIMEOUT_MINUTES', '60'))
    REQUIRE_HTTPS: bool = os.getenv('REQUIRE_HTTPS', 'True').lower() == 'true'
    
    # Audit Configuration
    AUDIT_COLLECTION_NAME: str = os.getenv('AUDIT_COLLECTION_NAME', 'audit_logs')
    AUDIT_RETENTION_DAYS: int = int(os.getenv('AUDIT_RETENTION_DAYS', '365'))
    
    # Database Collections
    USERS_COLLECTION: str = os.getenv('USERS_COLLECTION', 'users')
    CITIZEN_CARDS_COLLECTION: str = os.getenv('CITIZEN_CARDS_COLLECTION', 'citizen_cards')
    RESIDENCE_COLLECTION: str = os.getenv('RESIDENCE_COLLECTION', 'residence')
    HOUSEHOLD_MEMBERS_SUBCOLLECTION: str = os.getenv('HOUSEHOLD_MEMBERS_SUBCOLLECTION', 'household_members')
    
    @classmethod
    def validate_config(cls) -> list:
        """
        Validate configuration and return list of validation errors.
        
        Returns:
            list: List of validation error messages
        """
        errors = []
        
        # Validate Firebase configuration
        if not cls.FIREBASE_PROJECT_ID:
            errors.append("FIREBASE_PROJECT_ID is required")
        
        if not cls.FIREBASE_CREDENTIALS_PATH and not cls.FIREBASE_CREDENTIALS_JSON:
            errors.append(
                "Either FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_JSON must be set"
            )
        
        # Validate numeric configurations
        try:
            if cls.PAGE_SIZE <= 0:
                errors.append("PAGE_SIZE must be a positive integer")
        except (ValueError, TypeError):
            errors.append("PAGE_SIZE must be a valid integer")
        
        try:
            if cls.MAX_SEARCH_RESULTS <= 0:
                errors.append("MAX_SEARCH_RESULTS must be a positive integer")
        except (ValueError, TypeError):
            errors.append("MAX_SEARCH_RESULTS must be a valid integer")
        
        try:
            if cls.SESSION_TIMEOUT_MINUTES <= 0:
                errors.append("SESSION_TIMEOUT_MINUTES must be a positive integer")
        except (ValueError, TypeError):
            errors.append("SESSION_TIMEOUT_MINUTES must be a valid integer")
        
        try:
            if cls.AUDIT_RETENTION_DAYS <= 0:
                errors.append("AUDIT_RETENTION_DAYS must be a positive integer")
        except (ValueError, TypeError):
            errors.append("AUDIT_RETENTION_DAYS must be a valid integer")
        
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if cls.LOG_LEVEL not in valid_log_levels:
            errors.append(f"LOG_LEVEL must be one of: {', '.join(valid_log_levels)}")
        
        return errors
    
    @classmethod
    def get_config_summary(cls) -> dict:
        """
        Get a summary of current configuration (excluding sensitive data).
        
        Returns:
            dict: Configuration summary
        """
        return {
            'firebase_project_id': cls.FIREBASE_PROJECT_ID,
            'debug_mode': cls.DEBUG_MODE,
            'log_level': cls.LOG_LEVEL,
            'admin_email_domain': cls.ADMIN_EMAIL_DOMAIN,
            'page_size': cls.PAGE_SIZE,
            'max_search_results': cls.MAX_SEARCH_RESULTS,
            'session_timeout_minutes': cls.SESSION_TIMEOUT_MINUTES,
            'require_https': cls.REQUIRE_HTTPS,
            'audit_collection_name': cls.AUDIT_COLLECTION_NAME,
            'audit_retention_days': cls.AUDIT_RETENTION_DAYS,
            'users_collection': cls.USERS_COLLECTION,
            'citizen_cards_collection': cls.CITIZEN_CARDS_COLLECTION,
            'residence_collection': cls.RESIDENCE_COLLECTION,
            'household_members_subcollection': cls.HOUSEHOLD_MEMBERS_SUBCOLLECTION,
            'has_credentials_path': bool(cls.FIREBASE_CREDENTIALS_PATH),
            'has_credentials_json': bool(cls.FIREBASE_CREDENTIALS_JSON),
            'allowed_admin_emails_count': len(cls.ALLOWED_ADMIN_EMAILS)
        }


class DevelopmentConfig(Config):
    """Development-specific configuration."""
    
    DEBUG_MODE = True
    LOG_LEVEL = 'DEBUG'
    REQUIRE_HTTPS = False
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID', 'vneid-dev')


class ProductionConfig(Config):
    """Production-specific configuration."""
    
    DEBUG_MODE = False
    LOG_LEVEL = 'INFO'
    REQUIRE_HTTPS = True
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID', 'vneid-prod')


class TestConfig(Config):
    """Test-specific configuration."""
    
    DEBUG_MODE = True
    LOG_LEVEL = 'DEBUG'
    REQUIRE_HTTPS = False
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID', 'vneid-test')
    AUDIT_COLLECTION_NAME = 'test_audit_logs'
    USERS_COLLECTION = 'test_users'
    CITIZEN_CARDS_COLLECTION = 'test_citizen_cards'
    RESIDENCE_COLLECTION = 'test_residence'


def get_config() -> Config:
    """
    Get configuration based on environment.
    
    Returns:
        Config: Configuration instance based on ENVIRONMENT variable
    """
    env = os.getenv('ENVIRONMENT', 'development').lower()
    
    if env == 'production':
        return ProductionConfig()
    elif env == 'test':
        return TestConfig()
    else:
        return DevelopmentConfig()