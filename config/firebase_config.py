"""
Firebase Admin SDK configuration and initialization.

This module handles the initialization of Firebase Admin SDK with service account
authentication and provides database connection utilities.
"""

import os
import json
import logging
from typing import Optional
import firebase_admin
from firebase_admin import credentials, firestore

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

logger = logging.getLogger(__name__)


class FirebaseConfig:
    """Firebase configuration and connection manager."""
    
    _db_instance: Optional[firestore.Client] = None
    _app_instance: Optional[firebase_admin.App] = None
    
    @classmethod
    def initialize_firebase(cls) -> None:
        """
        Initialize Firebase Admin SDK with service account credentials.
        
        Raises:
            ValueError: If credentials are not properly configured
            Exception: If Firebase initialization fails
        """
        if cls._app_instance is not None:
            logger.info("Firebase already initialized")
            return
            
        try:
            # Get credentials from environment or file
            cred = cls._get_credentials()
            
            # Get project ID from Streamlit secrets, environment, or default
            project_id = 'expense-tracking-app-27ae6'  # Default to your project
            
            if HAS_STREAMLIT and "firebase" in st.secrets:
                project_id = st.secrets["firebase"].get("project_id", project_id)
            else:
                project_id = os.getenv('FIREBASE_PROJECT_ID', project_id)
            
            # Initialize Firebase app
            try:
                cls._app_instance = firebase_admin.initialize_app(cred, {
                    'projectId': project_id
                })
            except ValueError as e:
                # If already initialized elsewhere, re-use existing default app
                if "already exists" in str(e).lower():
                    cls._app_instance = firebase_admin.get_app()
                    logger.info("Reusing existing Firebase default app")
                else:
                    raise
            
            logger.info(f"Firebase initialized successfully for project: {project_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            raise
    
    @classmethod
    def _get_credentials(cls) -> credentials.Certificate:
        """
        Get Firebase service account credentials from Streamlit secrets, environment, or file.
        
        Returns:
            credentials.Certificate: Firebase service account credentials
            
        Raises:
            ValueError: If credentials are not found or invalid
        """
        # Try to get credentials from Streamlit secrets first
        if HAS_STREAMLIT:
            try:
                if "firebase" in st.secrets:
                    firebase_config = st.secrets["firebase"]
                    # Convert to dict for credentials
                    cred_dict = dict(firebase_config)
                    return credentials.Certificate(cred_dict)
            except Exception as e:
                logger.debug(f"Could not load from Streamlit secrets: {e}")
        
        # Try to get credentials from environment variable (JSON string)
        firebase_creds_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
        if firebase_creds_json:
            try:
                cred_dict = json.loads(firebase_creds_json)
                return credentials.Certificate(cred_dict)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in FIREBASE_CREDENTIALS_JSON: {str(e)}")
        
        # Try to get credentials from file path
        firebase_creds_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
        if firebase_creds_path and os.path.exists(firebase_creds_path):
            return credentials.Certificate(firebase_creds_path)
        
        # Try default service account file locations
        default_paths = [
            'serviceAccountKey.json',
            'service-account-key.json',
            'config/service-account-key.json',
            os.path.expanduser('~/.config/firebase/service-account-key.json')
        ]
        
        for path in default_paths:
            if os.path.exists(path):
                logger.info(f"Using service account file: {path}")
                return credentials.Certificate(path)
        
        raise ValueError(
            "Firebase credentials not found. Please set FIREBASE_CREDENTIALS_JSON "
            "environment variable or FIREBASE_CREDENTIALS_PATH to a valid service account file."
        )
    
    @classmethod
    def get_database(cls) -> firestore.Client:
        """
        Get Firestore database client instance.
        
        Returns:
            firestore.Client: Firestore database client
            
        Raises:
            RuntimeError: If Firebase is not initialized
        """
        if cls._app_instance is None:
            cls.initialize_firebase()
        
        if cls._db_instance is None:
            cls._db_instance = firestore.client()
            logger.info("Firestore client created successfully")
        
        return cls._db_instance
    
    @classmethod
    def test_connection(cls) -> bool:
        """
        Test Firebase connection with a basic read operation.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            db = cls.get_database()
            
            # Try to read from a collection (this will create it if it doesn't exist)
            test_collection = db.collection('_connection_test')
            
            # Attempt to get documents (limit to 1 for efficiency)
            docs = list(test_collection.limit(1).stream())
            
            logger.info("Firebase connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"Firebase connection test failed: {str(e)}")
            return False
    
    @classmethod
    def reset_connection(cls) -> None:
        """Reset Firebase connection (useful for testing or reconnection)."""
        if cls._app_instance:
            try:
                firebase_admin.delete_app(cls._app_instance)
                logger.info("Firebase app deleted successfully")
            except Exception as e:
                logger.warning(f"Error deleting Firebase app: {str(e)}")
        
        cls._app_instance = None
        cls._db_instance = None


# Convenience functions for easy access
def get_db() -> firestore.Client:
    """Get Firestore database client (convenience function)."""
    return FirebaseConfig.get_database()


def initialize_firebase() -> None:
    """Initialize Firebase (convenience function)."""
    FirebaseConfig.initialize_firebase()


def test_firebase_connection() -> bool:
    """Test Firebase connection (convenience function)."""
    return FirebaseConfig.test_connection()