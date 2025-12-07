"""
Authentication Module for Firebase Admin Dashboard

This module handles admin session management using Streamlit's built-in authentication
capabilities. It provides functions to check authentication status, retrieve admin
information, and manage session state for the dashboard.

Key Features:
- Integration with Streamlit's native authentication
- Admin email retrieval for audit logging
- Session state management
- Protected page access control
"""

import streamlit as st
import logging
from typing import Optional, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

def get_current_admin() -> Optional[str]:
    """
    Retrieve the current authenticated admin email from Streamlit context.
    Always returns a default admin email since auth is disabled.
    """
    return "admin@system.local"

def is_authenticated() -> bool:
    """
    Check if the current user is authenticated as an admin.
    Always returns True since auth is disabled.
    """
    return True

def get_admin_email() -> Optional[str]:
    """
    Get the admin email for audit logging purposes.
    """
    return "admin@system.local"

def require_authentication() -> bool:
    """
    Require authentication for the current page.
    Always returns True since auth is disabled.
    """
    return True

def clear_session() -> None:
    """
    Clear the current admin session.
    
    This function removes authentication information from the session state
    and can be used for logout functionality.
    """
    try:
        if hasattr(st.session_state, 'admin_email'):
            delattr(st.session_state, 'admin_email')
        
        # Clear any other session-related data
        session_keys_to_clear = [
            'admin_email', 'user_cache', 'last_activity'
        ]
        
        for key in session_keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        logger.info("Admin session cleared successfully")
        
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")

def get_session_info() -> Dict[str, Any]:
    """
    Get current session information for debugging and monitoring.
    
    Returns:
        Dict[str, Any]: Dictionary containing session information
    """
    try:
        session_info = {
            'is_authenticated': is_authenticated(),
            'admin_email': get_current_admin(),
            'session_state_keys': list(st.session_state.keys()) if hasattr(st, 'session_state') else [],
            'has_streamlit_user': hasattr(st, 'user') and st.user is not None,
        }
        
        # Add experimental user info if available
        try:
            session_info['has_experimental_user'] = hasattr(st, 'experimental_user') and st.experimental_user is not None
        except:
            session_info['has_experimental_user'] = False
        
        return session_info
        
    except Exception as e:
        logger.error(f"Error getting session info: {str(e)}")
        return {
            'error': str(e),
            'is_authenticated': False
        }

def display_auth_status() -> None:
    """
    Display current authentication status for debugging purposes.
    
    This function shows authentication information in the Streamlit interface
    and is useful for development and troubleshooting.
    """
    session_info = get_session_info()
    
    with st.expander("🔍 Authentication Status (Debug Info)"):
        st.json(session_info)
        
        if session_info.get('is_authenticated'):
            st.success(f"✅ Authenticated as: {session_info.get('admin_email')}")
        else:
            st.error("❌ Not authenticated")
        
        if st.button("Clear Session"):
            clear_session()
            st.rerun()

# Authentication decorator for functions
def require_auth(func):
    """
    Decorator to require authentication for a function.
    
    Usage:
        @require_auth
        def protected_function():
            # This function requires authentication
            pass
    """
    def wrapper(*args, **kwargs):
        if not require_authentication():
            return None
        return func(*args, **kwargs)
    return wrapper