"""
Configuration package for Firebase Admin Dashboard.

This package provides Firebase configuration, settings management,
and database connection utilities.
"""

from .firebase_config import (
    FirebaseConfig,
    get_db,
    initialize_firebase,
    test_firebase_connection
)
from .settings import Config, get_config

__all__ = [
    'FirebaseConfig',
    'Config',
    'get_db',
    'initialize_firebase',
    'test_firebase_connection',
    'get_config'
]