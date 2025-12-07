# Audit Logging Module

The audit logging module provides comprehensive tracking of all administrative actions performed in the Firebase Admin Dashboard. This ensures accountability, compliance, and security monitoring.

## Features

- **Comprehensive Logging**: Tracks user creation, updates, and deletion operations
- **Automatic Collection Management**: Creates audit collection if it doesn't exist
- **Error Handling**: Graceful error handling that doesn't interrupt primary operations
- **Flexible Querying**: Retrieve audit logs with various filtering options
- **Data Retention**: Built-in cleanup functionality for old audit logs

## Usage

### Basic Usage

```python
from modules.audit import AuditLogger
from config.firebase_config import get_db

# Initialize
db = get_db()
audit_logger = AuditLogger(db)

# Log user creation
success = audit_logger.log_user_creation(
    admin_email="admin@example.com",
    user_data={
        'uid': 'user123',
        'name': 'John Doe',
        'email': 'john@example.com',
        'citizen_id': 'CID123456789'
    },
    ip_address="192.168.1.100"
)

# Log user update
success = audit_logger.log_user_update(
    admin_email="admin@example.com",
    user_id="user123",
    user_name="John Doe",
    changes={'name': 'John Smith'},
    collection_name='users'
)

# Log user deletion
success = audit_logger.log_user_deletion(
    admin_email="admin@example.com",
    user_id="user123",
    user_name="John Doe",
    deleted_collections=['users', 'citizen_cards', 'residence']
)
```

### Convenience Functions

```python
from modules.audit import log_user_creation, log_user_deletion, log_user_update
from config.firebase_config import get_db

db = get_db()

# Direct function calls
log_user_creation(db, "admin@example.com", user_data)
log_user_update(db, "admin@example.com", "user123", "John Doe", changes, "users")
log_user_deletion(db, "admin@example.com", "user123", "John Doe")
```

### Retrieving Audit Logs

```python
# Get all logs for a specific user
logs = audit_logger.get_audit_logs(user_id="user123")

# Get logs by admin
logs = audit_logger.get_audit_logs(admin_email="admin@example.com")

# Get logs by action type
logs = audit_logger.get_audit_logs(action_type="delete")

# Get logs with date range
from datetime import datetime, timedelta
start_date = datetime.now() - timedelta(days=7)
logs = audit_logger.get_audit_logs(start_date=start_date)
```

## Audit Record Structure

Each audit record contains the following fields:

```python
{
    'timestamp': datetime,           # When the action occurred
    'admin_email': str,             # Email of the admin who performed the action
    'action_type': str,             # 'create', 'update', or 'delete'
    'target_user_id': str,          # UID of the affected user
    'target_user_name': str,        # Name of the affected user
    'details': dict,                # Action-specific details
    'ip_address': str,              # IP address of the admin (optional)
    'dashboard_version': str,       # Version of the dashboard
    'session_id': str               # Session ID (optional, for future use)
}
```

### Details Field Structure

#### For User Creation (`action_type: 'create'`)
```python
{
    'user_profile': {
        'name': str,
        'email': str,
        'phone': str,
        'citizen_id': str,
        # ... other profile fields
    },
    'citizen_card_created': bool,
    'residence_created': bool,
    'creation_timestamp': str,
    'citizen_card': dict,           # If citizen card was created
    'residence': dict               # If residence was created
}
```

#### For User Updates (`action_type: 'update'`)
```python
{
    'updated_collection': str,      # Collection that was updated
    'changes_made': dict,           # The actual changes
    'update_timestamp': str,
    'fields_modified': list         # List of field names that were changed
}
```

#### For User Deletion (`action_type: 'delete'`)
```python
{
    'deleted_user_id': str,
    'deleted_user_name': str,
    'deleted_collections': list,    # Collections that were deleted
    'deletion_timestamp': str,
    'cascade_deletion': bool        # Whether cascade deletion was performed
}
```

## Configuration

The audit module uses configuration from `config/settings.py`:

- `AUDIT_COLLECTION_NAME`: Name of the audit collection (default: 'audit_logs')
- `AUDIT_RETENTION_DAYS`: How long to keep audit logs (default: 365 days)

## Error Handling

The audit module is designed to be resilient:

1. **Non-blocking**: Audit failures don't prevent the primary operation from completing
2. **Logging**: All errors are logged for debugging
3. **Return Values**: All functions return `True` for success, `False` for failure
4. **Exception Safety**: No exceptions are raised to the caller

## Testing

### Unit Tests
Run unit tests that don't require Firebase connection:
```bash
python test_audit_unit.py
```

### Integration Tests
Run integration tests with actual Firebase (requires credentials):
```bash
python test_audit_integration.py
```

## Requirements Compliance

This module satisfies the following requirements:

- **8.1**: Logs user creation with admin email, timestamp, action type, and user details
- **8.2**: Logs user deletion with admin email, timestamp, action type, and deleted user identifier
- **8.3**: Includes sufficient detail for compliance tracking
- **8.4**: Completes primary action even if audit logging fails, logs audit failures
- **8.5**: Automatically creates audit collection if it doesn't exist

## Security Considerations

- Audit logs are stored in Firestore with the same security as other collections
- IP addresses are logged when available for security monitoring
- Admin emails are always logged for accountability
- Sensitive data (like passwords) is never logged in audit records

## Performance Considerations

- Audit logging is asynchronous and doesn't block primary operations
- Batch operations are used for cleanup to avoid hitting Firestore limits
- Audit queries are optimized with proper indexing considerations
- Old logs can be cleaned up automatically to manage storage costs