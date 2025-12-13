"""
Enhanced Logging Configuration for Firebase Admin Dashboard

This module provides comprehensive logging configuration with file rotation,
structured logging, and error tracking for compliance and debugging.
"""

import logging
import logging.handlers
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with JSON output."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'admin_email'):
            log_data['admin_email'] = record.admin_email
        if hasattr(record, 'operation'):
            log_data['operation'] = record.operation
        if hasattr(record, 'error_type'):
            log_data['error_type'] = record.error_type
        
        return json.dumps(log_data, default=str)


class DashboardLogger:
    """Enhanced logging configuration for the admin dashboard."""
    
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize logging configuration.
        
        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = log_dir
        # On Windows, file logging often crashes with Streamlit due to locking.
        # Defaulting to console only for stability.
        self.use_file_logging = os.name != 'nt' 
        if self.use_file_logging:
            self.ensure_log_directory()
        self.setup_logging()
    
    def ensure_log_directory(self) -> None:
        """Ensure log directory exists."""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def setup_logging(self) -> None:
        """Configure comprehensive logging with multiple handlers."""
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        if not self.use_file_logging:
            return

        # File handler for general application logs
        try:
            app_log_file = os.path.join(self.log_dir, 'dashboard.log')
            app_handler = logging.handlers.RotatingFileHandler(
                app_log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            app_handler.setLevel(logging.INFO)
            app_handler.setFormatter(console_formatter)
            root_logger.addHandler(app_handler)
            
            # Error-specific handler with structured logging
            error_log_file = os.path.join(self.log_dir, 'errors.log')
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=5*1024*1024,  # 5MB
                backupCount=10
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(StructuredFormatter())
            root_logger.addHandler(error_handler)
        except PermissionError:
            print("WARNING: Could not set up file logging due to permissions. Using console only.")
        except Exception as e:
            print(f"WARNING: logging setup failed: {e}")
        
        # Audit log handler for compliance
        try:
            audit_log_file = os.path.join(self.log_dir, 'audit.log')
            audit_handler = logging.handlers.RotatingFileHandler(
                audit_log_file,
                maxBytes=20*1024*1024,  # 20MB
                backupCount=20
            )
            audit_handler.setLevel(logging.INFO)
            audit_handler.setFormatter(StructuredFormatter())
            
            # Create audit logger
            audit_logger = logging.getLogger('audit')
            audit_logger.setLevel(logging.INFO)
            audit_logger.addHandler(audit_handler)
            audit_logger.propagate = False  # Don't propagate to root logger
        except Exception:
             # If audit logging fails, disable it or log to root (console)
             pass
    
    def log_user_operation(self, operation: str, user_id: str, admin_email: str, 
                          details: Dict[str, Any] = None, success: bool = True) -> None:
        """
        Log user operations for audit purposes.
        
        Args:
            operation: Type of operation (create, update, delete, view)
            user_id: ID of the user being operated on
            admin_email: Email of the admin performing the operation
            details: Additional operation details
            success: Whether the operation was successful
        """
        audit_logger = logging.getLogger('audit')
        
        log_data = {
            'operation': operation,
            'user_id': user_id,
            'admin_email': admin_email,
            'success': success,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if details:
            log_data['details'] = details
        
        level = logging.INFO if success else logging.ERROR
        audit_logger.log(level, f"User operation: {operation}", extra=log_data)
    
    def log_authentication_event(self, admin_email: str, success: bool, 
                                reason: str = None, ip_address: str = None) -> None:
        """
        Log authentication events.
        
        Args:
            admin_email: Email of the admin attempting authentication
            success: Whether authentication was successful
            reason: Reason for failure (if applicable)
            ip_address: IP address of the request
        """
        audit_logger = logging.getLogger('audit')
        
        log_data = {
            'event_type': 'authentication',
            'admin_email': admin_email,
            'success': success,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if reason:
            log_data['reason'] = reason
        if ip_address:
            log_data['ip_address'] = ip_address
        
        level = logging.INFO if success else logging.WARNING
        message = f"Authentication {'successful' if success else 'failed'} for {admin_email}"
        audit_logger.log(level, message, extra=log_data)
    
    def log_error_with_context(self, error: Exception, error_type: str, 
                              user_context: Dict[str, Any] = None) -> None:
        """
        Log errors with full context for debugging.
        
        Args:
            error: The exception that occurred
            error_type: Type/category of the error
            user_context: Additional context about the user and operation
        """
        logger = logging.getLogger('error_handler')
        
        log_data = {
            'error_type': error_type,
            'error_message': str(error),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if user_context:
            log_data.update(user_context)
        
        logger.error(f"Error occurred: {error_type}", extra=log_data, exc_info=True)
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get statistics about log files."""
        stats = {}
        
        for log_file in ['dashboard.log', 'errors.log', 'audit.log']:
            file_path = os.path.join(self.log_dir, log_file)
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                stats[log_file] = {
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
            else:
                stats[log_file] = {'size_mb': 0, 'modified': None}
        
        return stats


# Global logger instance
dashboard_logger = DashboardLogger()


# Convenience functions for logging
def log_user_operation(operation: str, user_id: str, admin_email: str, 
                      details: Dict[str, Any] = None, success: bool = True) -> None:
    """Log user operations - convenience function."""
    dashboard_logger.log_user_operation(operation, user_id, admin_email, details, success)


def log_authentication_event(admin_email: str, success: bool, 
                            reason: str = None, ip_address: str = None) -> None:
    """Log authentication events - convenience function."""
    dashboard_logger.log_authentication_event(admin_email, success, reason, ip_address)


def log_error_with_context(error: Exception, error_type: str, 
                          user_context: Dict[str, Any] = None) -> None:
    """Log errors with context - convenience function."""
    dashboard_logger.log_error_with_context(error, error_type, user_context)


def get_log_stats() -> Dict[str, Any]:
    """Get log statistics - convenience function."""
    return dashboard_logger.get_log_stats()