"""
Audit Logging Module

This module provides comprehensive audit logging functionality for tracking
administrative actions in the Firebase Admin Dashboard. All user management
operations are logged for compliance and accountability purposes.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from firebase_admin import firestore
from google.cloud.firestore_v1.base_document import DocumentSnapshot

try:
    from config.settings import get_config
except ImportError:
    # Handle case when running as script or test
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config.settings import get_config

logger = logging.getLogger(__name__)
config = get_config()


class AuditLogger:
    """
    Handles audit logging for all administrative actions in the dashboard.
    
    This class provides methods to log user creation, deletion, and update
    operations with comprehensive details for compliance tracking.
    """
    
    def __init__(self, db: firestore.Client):
        """
        Initialize AuditLogger with Firestore database client.
        
        Args:
            db: Firestore database client instance
        """
        self.db = db
        self.audit_collection = db.collection(config.AUDIT_COLLECTION_NAME)
        self._ensure_audit_collection_exists()
    
    def _ensure_audit_collection_exists(self) -> None:
        """
        Ensure the audit collection exists by creating it if necessary.
        
        This method attempts to create the audit collection if it doesn't exist.
        It handles the case where the collection might be created concurrently.
        """
        try:
            # Try to get a document from the collection to check if it exists
            docs = self.audit_collection.limit(1).get()
            
            # If we can query it, the collection exists (even if empty)
            logger.debug(f"Audit collection '{config.AUDIT_COLLECTION_NAME}' verified")
            
        except Exception as e:
            logger.warning(f"Could not verify audit collection existence: {e}")
            # Collection will be created automatically when first document is added
    
    def _create_audit_record(self, admin_email: str, action_type: str, 
                           target_user_id: str, target_user_name: str,
                           details: Dict[str, Any], ip_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a standardized audit record structure.
        
        Args:
            admin_email: Email of the admin performing the action
            action_type: Type of action ('create', 'update', 'delete')
            target_user_id: UID of the user being affected
            target_user_name: Name of the user being affected
            details: Action-specific details
            ip_address: Optional IP address of the admin
            
        Returns:
            Dict containing the audit record
        """
        return {
            'timestamp': datetime.utcnow(),
            'admin_email': admin_email,
            'action_type': action_type,
            'target_user_id': target_user_id,
            'target_user_name': target_user_name,
            'details': details,
            'ip_address': ip_address,
            'dashboard_version': '1.0.0',  # Could be made configurable
            'session_id': None  # Could be enhanced with session tracking
        }
    
    def _safe_log_audit(self, audit_record: Dict[str, Any]) -> bool:
        """
        Safely log an audit record with error handling.
        
        Args:
            audit_record: The audit record to log
            
        Returns:
            bool: True if logging succeeded, False otherwise
        """
        try:
            # Add the audit record to Firestore
            doc_ref = self.audit_collection.add(audit_record)
            logger.info(f"Audit record created with ID: {doc_ref[1].id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create audit record: {e}")
            logger.error(f"Audit record data: {audit_record}")
            return False
    
    def log_user_creation(self, admin_email: str, user_data: Dict[str, Any],
                         citizen_card_data: Optional[Dict[str, Any]] = None,
                         residence_data: Optional[Dict[str, Any]] = None,
                         ip_address: Optional[str] = None) -> bool:
        """
        Log user creation event to the audit collection.
        
        Args:
            admin_email: Email of the admin creating the user
            user_data: User profile data that was created
            citizen_card_data: Optional citizen card data that was created
            residence_data: Optional residence data that was created
            ip_address: Optional IP address of the admin
            
        Returns:
            bool: True if audit logging succeeded, False otherwise
        """
        try:
            # Extract key information for the audit log
            user_id = user_data.get('uid', 'unknown')
            user_name = user_data.get('name', 'unknown')
            
            # Create details object with relevant information
            details = {
                'user_profile': {
                    'name': user_data.get('name'),
                    'email': user_data.get('email'),
                    'phone': user_data.get('phone'),
                    'citizen_id': user_data.get('citizen_id'),
                    'address': user_data.get('address'),
                    'dob': user_data.get('dob'),
                    'gender': user_data.get('gender')
                },
                'citizen_card_created': citizen_card_data is not None,
                'residence_created': residence_data is not None,
                'creation_timestamp': datetime.utcnow().isoformat()
            }
            
            # Add citizen card details if provided
            if citizen_card_data:
                details['citizen_card'] = {
                    'full_name': citizen_card_data.get('full_name'),
                    'citizen_id': citizen_card_data.get('citizen_id'),
                    'place_of_birth': citizen_card_data.get('place_of_birth'),
                    'permanent_address': citizen_card_data.get('permanent_address')
                }
            
            # Add residence details if provided
            if residence_data:
                details['residence'] = {
                    'full_name': residence_data.get('full_name'),
                    'citizen_id': residence_data.get('citizen_id'),
                    'permanent_address': residence_data.get('permanent_address'),
                    'current_address': residence_data.get('current_address'),
                    'household_id': residence_data.get('household_id')
                }
            
            # Create and log the audit record
            audit_record = self._create_audit_record(
                admin_email=admin_email,
                action_type='create',
                target_user_id=user_id,
                target_user_name=user_name,
                details=details,
                ip_address=ip_address
            )
            
            success = self._safe_log_audit(audit_record)
            
            if success:
                logger.info(f"User creation audit logged for user {user_id} by {admin_email}")
            else:
                logger.error(f"Failed to log user creation audit for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in log_user_creation: {e}")
            return False
    
    def log_user_deletion(self, admin_email: str, user_id: str, user_name: str,
                         deleted_collections: Optional[List[str]] = None,
                         ip_address: Optional[str] = None) -> bool:
        """
        Log user deletion event to the audit collection.
        
        Args:
            admin_email: Email of the admin deleting the user
            user_id: UID of the user being deleted
            user_name: Name of the user being deleted
            deleted_collections: List of collections that were deleted
            ip_address: Optional IP address of the admin
            
        Returns:
            bool: True if audit logging succeeded, False otherwise
        """
        try:
            # Create details object with deletion information
            details = {
                'deleted_user_id': user_id,
                'deleted_user_name': user_name,
                'deleted_collections': deleted_collections or [],
                'deletion_timestamp': datetime.utcnow().isoformat(),
                'cascade_deletion': True if deleted_collections else False
            }
            
            # Create and log the audit record
            audit_record = self._create_audit_record(
                admin_email=admin_email,
                action_type='delete',
                target_user_id=user_id,
                target_user_name=user_name,
                details=details,
                ip_address=ip_address
            )
            
            success = self._safe_log_audit(audit_record)
            
            if success:
                logger.info(f"User deletion audit logged for user {user_id} by {admin_email}")
            else:
                logger.error(f"Failed to log user deletion audit for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in log_user_deletion: {e}")
            return False
    
    def log_user_update(self, admin_email: str, user_id: str, user_name: str,
                       changes: Dict[str, Any], collection_name: str,
                       ip_address: Optional[str] = None) -> bool:
        """
        Log user update event to the audit collection.
        
        Args:
            admin_email: Email of the admin updating the user
            user_id: UID of the user being updated
            user_name: Name of the user being updated
            changes: Dictionary containing the changes made
            collection_name: Name of the collection being updated
            ip_address: Optional IP address of the admin
            
        Returns:
            bool: True if audit logging succeeded, False otherwise
        """
        try:
            # Create details object with update information
            details = {
                'updated_collection': collection_name,
                'changes_made': changes,
                'update_timestamp': datetime.utcnow().isoformat(),
                'fields_modified': list(changes.keys()) if isinstance(changes, dict) else []
            }
            
            # Create and log the audit record
            audit_record = self._create_audit_record(
                admin_email=admin_email,
                action_type='update',
                target_user_id=user_id,
                target_user_name=user_name,
                details=details,
                ip_address=ip_address
            )
            
            success = self._safe_log_audit(audit_record)
            
            if success:
                logger.info(f"User update audit logged for user {user_id} in {collection_name} by {admin_email}")
            else:
                logger.error(f"Failed to log user update audit for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in log_user_update: {e}")
            return False
    
    def get_audit_logs(self, user_id: Optional[str] = None, 
                      admin_email: Optional[str] = None,
                      action_type: Optional[str] = None,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve audit logs with optional filtering.
        
        Args:
            user_id: Optional filter by target user ID
            admin_email: Optional filter by admin email
            action_type: Optional filter by action type
            start_date: Optional filter by start date
            end_date: Optional filter by end date
            limit: Maximum number of logs to return
            
        Returns:
            List of audit log records
        """
        try:
            query = self.audit_collection
            
            # Apply filters
            if user_id:
                query = query.where('target_user_id', '==', user_id)
            
            if admin_email:
                query = query.where('admin_email', '==', admin_email)
            
            if action_type:
                query = query.where('action_type', '==', action_type)
            
            if start_date:
                query = query.where('timestamp', '>=', start_date)
            
            if end_date:
                query = query.where('timestamp', '<=', end_date)
            
            # Order by timestamp (most recent first) and limit results
            query = query.order_by('timestamp', direction=firestore.Query.DESCENDING)
            query = query.limit(limit)
            
            # Execute query and return results
            docs = query.get()
            audit_logs = []
            
            for doc in docs:
                log_data = doc.to_dict()
                log_data['id'] = doc.id
                audit_logs.append(log_data)
            
            logger.info(f"Retrieved {len(audit_logs)} audit logs")
            return audit_logs
            
        except Exception as e:
            logger.error(f"Error retrieving audit logs: {e}")
            return []
    
    def cleanup_old_audit_logs(self, retention_days: Optional[int] = None) -> int:
        """
        Clean up audit logs older than the specified retention period.
        
        Args:
            retention_days: Number of days to retain logs (uses config default if None)
            
        Returns:
            int: Number of logs deleted
        """
        try:
            if retention_days is None:
                retention_days = config.AUDIT_RETENTION_DAYS
            
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Query for old logs
            old_logs_query = self.audit_collection.where('timestamp', '<', cutoff_date)
            old_logs = old_logs_query.get()
            
            # Delete old logs in batches
            deleted_count = 0
            batch = self.db.batch()
            batch_size = 0
            
            for doc in old_logs:
                batch.delete(doc.reference)
                batch_size += 1
                deleted_count += 1
                
                # Commit batch when it reaches 500 operations (Firestore limit)
                if batch_size >= 500:
                    batch.commit()
                    batch = self.db.batch()
                    batch_size = 0
            
            # Commit remaining operations
            if batch_size > 0:
                batch.commit()
            
            logger.info(f"Cleaned up {deleted_count} old audit logs (older than {retention_days} days)")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old audit logs: {e}")
            return 0


# Convenience functions for direct usage
def log_user_creation(db: firestore.Client, admin_email: str, user_data: Dict[str, Any],
                     citizen_card_data: Optional[Dict[str, Any]] = None,
                     residence_data: Optional[Dict[str, Any]] = None,
                     ip_address: Optional[str] = None) -> bool:
    """
    Convenience function to log user creation.
    
    Args:
        db: Firestore database client
        admin_email: Email of the admin creating the user
        user_data: User profile data that was created
        citizen_card_data: Optional citizen card data that was created
        residence_data: Optional residence data that was created
        ip_address: Optional IP address of the admin
        
    Returns:
        bool: True if audit logging succeeded, False otherwise
    """
    audit_logger = AuditLogger(db)
    return audit_logger.log_user_creation(
        admin_email, user_data, citizen_card_data, residence_data, ip_address
    )


def log_user_deletion(db: firestore.Client, admin_email: str, user_id: str, user_name: str,
                     deleted_collections: Optional[List[str]] = None,
                     ip_address: Optional[str] = None) -> bool:
    """
    Convenience function to log user deletion.
    
    Args:
        db: Firestore database client
        admin_email: Email of the admin deleting the user
        user_id: UID of the user being deleted
        user_name: Name of the user being deleted
        deleted_collections: List of collections that were deleted
        ip_address: Optional IP address of the admin
        
    Returns:
        bool: True if audit logging succeeded, False otherwise
    """
    audit_logger = AuditLogger(db)
    return audit_logger.log_user_deletion(
        admin_email, user_id, user_name, deleted_collections, ip_address
    )


def log_user_update(db: firestore.Client, admin_email: str, user_id: str, user_name: str,
                   changes: Dict[str, Any], collection_name: str,
                   ip_address: Optional[str] = None) -> bool:
    """
    Convenience function to log user update.
    
    Args:
        db: Firestore database client
        admin_email: Email of the admin updating the user
        user_id: UID of the user being updated
        user_name: Name of the user being updated
        changes: Dictionary containing the changes made
        collection_name: Name of the collection being updated
        ip_address: Optional IP address of the admin
        
    Returns:
        bool: True if audit logging succeeded, False otherwise
    """
    audit_logger = AuditLogger(db)
    return audit_logger.log_user_update(
        admin_email, user_id, user_name, changes, collection_name, ip_address
    )