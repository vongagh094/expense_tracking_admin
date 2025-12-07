"""
Modules package for Firebase Admin Dashboard.

This package contains all the core modules for the admin dashboard:
- user_management: User CRUD operations
- audit: Audit logging functionality
- auth: Authentication and session management
- ui_components: Reusable UI components (future)
"""

from .user_management import UserManager
from .audit import AuditLogger, log_user_creation, log_user_deletion, log_user_update
from .auth import (
    get_current_admin,
    is_authenticated,
    get_admin_email,
    require_authentication,
    clear_session,
    get_session_info,
    display_auth_status,
    require_auth
)

__all__ = [
    'UserManager',
    'AuditLogger', 
    'log_user_creation',
    'log_user_deletion', 
    'log_user_update',
    'get_current_admin',
    'is_authenticated',
    'get_admin_email',
    'require_authentication',
    'clear_session',
    'get_session_info',
    'display_auth_status',
    'require_auth'
]