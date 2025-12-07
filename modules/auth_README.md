# Authentication Module

This module provides authentication and session management for the Firebase Admin Dashboard using Streamlit's built-in authentication capabilities.

## Features

- **Multi-method Authentication**: Supports various Streamlit authentication methods
- **Session Management**: Maintains admin session state across page reloads
- **Audit Integration**: Provides admin email for audit logging
- **Development Support**: Includes manual authentication for testing
- **Error Handling**: Graceful handling of authentication failures

## Key Functions

### `get_current_admin() -> Optional[str]`
Retrieves the current authenticated admin email from various Streamlit sources:
- Session state (cached)
- `st.user.email` (Streamlit Cloud)
- `st.experimental_user.email` (legacy)
- Request headers (proxy authentication)

### `is_authenticated() -> bool`
Checks if the current user is authenticated as an admin.

### `require_authentication() -> bool`
Enforces authentication for protected pages. Shows authentication UI if not authenticated.
Returns `True` if authenticated and can proceed, `False` if should stop execution.

### `get_admin_email() -> Optional[str]`
Alias for `get_current_admin()` with explicit purpose for audit logging.

### `clear_session() -> None`
Clears the current admin session and authentication data.

### `get_session_info() -> Dict[str, Any]`
Returns current session information for debugging and monitoring.

### `display_auth_status() -> None`
Displays current authentication status in the Streamlit interface (for debugging).

### `@require_auth` decorator
Decorator to require authentication for functions.

## Usage Examples

### Basic Page Protection
```python
from modules.auth import require_authentication, get_current_admin

def protected_page():
    # Check authentication at the start of the page
    if not require_authentication():
        return  # Stop execution if not authenticated
    
    # Page content for authenticated users
    admin_email = get_current_admin()
    st.success(f"Welcome, {admin_email}!")
```

### Function Decorator
```python
from modules.auth import require_auth

@require_auth
def admin_only_function():
    # This function requires authentication
    st.write("This is only visible to authenticated admins")
```

### Audit Logging Integration
```python
from modules.auth import get_admin_email
from modules.audit import log_user_creation

def create_user(user_data):
    # ... user creation logic ...
    
    # Log the action with admin email
    admin_email = get_admin_email()
    log_user_creation(admin_email, user_data)
```

## Authentication Methods

The module supports multiple authentication methods in order of priority:

1. **Session State**: Cached admin email from previous authentication
2. **Streamlit User**: `st.user.email` (Streamlit Cloud authentication)
3. **Experimental User**: `st.experimental_user.email` (legacy support)
4. **Request Headers**: Common authentication headers from proxies/load balancers
5. **Manual Input**: Development/testing authentication (when enabled)

## Development/Testing

For development and testing environments, the module provides a manual authentication option:

1. When `require_authentication()` is called and no authentication is found
2. An expandable "Development/Testing Authentication" section appears
3. Admins can manually enter their email address
4. This should only be used in development environments

## Security Considerations

- Email validation ensures proper format
- Mock detection prevents test artifacts from being used as real authentication
- Session state is cleared on logout
- All authentication attempts are logged for debugging

## Integration with Main Application

The authentication module is integrated into the main application (`main.py`) to protect all admin functionality:

```python
from modules.auth import require_authentication, get_current_admin

def main():
    # ... page configuration ...
    
    # Require authentication for the entire dashboard
    if not require_authentication():
        return
    
    # Authenticated content
    admin_email = get_current_admin()
    st.success(f"Welcome, {admin_email}!")
    # ... rest of dashboard ...
```

## Error Handling

The module includes comprehensive error handling:
- Graceful fallback when authentication methods are unavailable
- Logging of authentication attempts and failures
- User-friendly error messages
- Continuation of operation even if some authentication methods fail

## Testing

The module includes test coverage for:
- Basic function imports and calls
- Session state authentication
- Streamlit user authentication
- Error handling scenarios
- Mock detection and filtering

Run tests with:
```bash
python test_auth_simple.py
```