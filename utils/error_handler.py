"""
Centralized Error Handling and User Feedback System

This module provides comprehensive error handling, user feedback, and logging
management for the Firebase Admin Dashboard. Enhanced to provide user-friendly
error messages for all failure scenarios as per requirements 1.3, 3.6, 5.6, 6.5, 8.4.
"""

import streamlit as st
import logging
import traceback
import re
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from datetime import datetime
from enum import Enum
from contextlib import contextmanager

# Configure logging with enhanced formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('firebase_admin_dashboard.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Enumeration of error types for categorized handling."""
    VALIDATION = "validation"
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    PERMISSION = "permission"
    NOT_FOUND = "not_found"
    SYSTEM = "system"
    USER_INPUT = "user_input"
    AUDIT_FAILURE = "audit_failure"
    FIREBASE_ERROR = "firebase_error"
    DUPLICATE_DATA = "duplicate_data"
    FORM_VALIDATION = "form_validation"


class FeedbackType(Enum):
    """Enumeration of feedback message types."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ErrorHandler:
    """
    Centralized error handling and user feedback management.
    
    Provides consistent error handling, user-friendly messages,
    and feedback display across the application.
    """
    
    def __init__(self):
        """Initialize the error handler."""
        self.error_history = []
        self.max_history = 100
    
    def handle_error(self, 
                    error: Exception, 
                    error_type: ErrorType = ErrorType.SYSTEM,
                    user_message: Optional[str] = None,
                    show_details: bool = False,
                    log_error: bool = True) -> None:
        """
        Handle an error with appropriate user feedback and logging.
        
        Args:
            error: The exception that occurred
            error_type: Type of error for categorized handling
            user_message: Custom user-friendly message
            show_details: Whether to show technical details
            log_error: Whether to log the error
        """
        # Generate user-friendly message if not provided
        if not user_message:
            user_message = self._generate_user_message(error, error_type)
        
        # Log the error if requested
        if log_error:
            self._log_error(error, error_type, user_message)
        
        # Store in error history
        self._store_error_history(error, error_type, user_message)
        
        # Display user feedback
        self._display_error_feedback(user_message, error, show_details)
    
    def _generate_user_message(self, error: Exception, error_type: ErrorType) -> str:
        """Generate comprehensive user-friendly error messages based on error type and context."""
        error_str = str(error).lower()
        
        # Enhanced error messages with specific context
        if error_type == ErrorType.AUTHENTICATION:
            if "invalid" in error_str or "wrong" in error_str:
                return "Invalid email or password. Please check your credentials and try again."
            elif "expired" in error_str or "session" in error_str:
                return "Your session has expired. Please log in again to continue."
            elif "permission" in error_str or "unauthorized" in error_str:
                return "You don't have permission to access this dashboard. Please contact your administrator."
            else:
                return "Authentication failed. Please verify your credentials and try again."
        
        elif error_type == ErrorType.VALIDATION or error_type == ErrorType.FORM_VALIDATION:
            if "citizen_id" in error_str and ("unique" in error_str or "exists" in error_str):
                return "This Citizen ID is already registered in the system. Please use a different ID."
            elif "email" in error_str and ("unique" in error_str or "exists" in error_str):
                return "This email address is already registered. Please use a different email."
            elif "required" in error_str or "missing" in error_str:
                return "Please fill in all required fields before continuing."
            elif "format" in error_str or "invalid" in error_str:
                return "Please check the format of your input data and correct any errors."
            elif hasattr(error, 'args') and error.args:
                return f"Validation Error: {error.args[0]}"
            else:
                return "Please check your input data and correct any validation errors."
        
        elif error_type == ErrorType.DATABASE or error_type == ErrorType.FIREBASE_ERROR:
            if "permission" in error_str or "unauthorized" in error_str:
                return "Database access denied. Please check your permissions and try again."
            elif "network" in error_str or "connection" in error_str or "timeout" in error_str:
                return "Connection to database failed. Please check your internet connection and try again."
            elif "not found" in error_str or "does not exist" in error_str:
                return "The requested data was not found. It may have been deleted or moved."
            elif "quota" in error_str or "limit" in error_str:
                return "Database quota exceeded. Please try again later or contact support."
            elif "unique" in error_str or "duplicate" in error_str:
                return "This record already exists. Please use different values."
            else:
                return "Database operation failed. Please try again in a moment."
        
        elif error_type == ErrorType.DUPLICATE_DATA:
            if "citizen_id" in error_str:
                return "A user with this Citizen ID already exists. Please use a different ID."
            elif "email" in error_str:
                return "A user with this email already exists. Please use a different email."
            else:
                return "This record already exists in the system. Please use different values."
        
        elif error_type == ErrorType.NOT_FOUND:
            if "user" in error_str:
                return "User not found. The user may have been deleted or the ID is incorrect."
            elif "document" in error_str or "record" in error_str:
                return "The requested record was not found. It may have been deleted."
            else:
                return f"Item not found: {str(error)}"
        
        elif error_type == ErrorType.AUDIT_FAILURE:
            return "Action completed successfully, but audit logging failed. The operation was still saved."
        
        elif error_type == ErrorType.NETWORK:
            return "Network connection issue. Please check your internet connection and try again."
        
        elif error_type == ErrorType.PERMISSION:
            return "You don't have permission to perform this action. Please contact your administrator."
        
        elif error_type == ErrorType.USER_INPUT:
            return "Invalid input provided. Please check your data format and try again."
        
        else:  # SYSTEM or unknown
            if "firebase" in error_str:
                return "Firebase service error. Please try again in a moment or contact support."
            elif "streamlit" in error_str:
                return "Interface error occurred. Please refresh the page and try again."
            else:
                return "An unexpected error occurred. Please try again or contact support if this persists."
    
    def _log_error(self, error: Exception, error_type: ErrorType, user_message: str) -> None:
        """Log error details for debugging and monitoring."""
        logger.error(
            f"Error Type: {error_type.value} | "
            f"User Message: {user_message} | "
            f"Exception: {str(error)} | "
            f"Traceback: {traceback.format_exc()}"
        )
    
    def _store_error_history(self, error: Exception, error_type: ErrorType, user_message: str) -> None:
        """Store error in history for debugging purposes."""
        error_record = {
            'timestamp': datetime.utcnow(),
            'error_type': error_type.value,
            'user_message': user_message,
            'exception': str(error),
            'traceback': traceback.format_exc()
        }
        
        self.error_history.append(error_record)
        
        # Maintain history size limit
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]
    
    def _display_error_feedback(self, user_message: str, error: Exception, show_details: bool) -> None:
        """Display error feedback to the user."""
        st.error(f"❌ {user_message}")
        
        if show_details:
            with st.expander("🔧 Technical Details"):
                st.code(f"Error: {str(error)}")
                st.code(traceback.format_exc())
    
    def handle_authentication_error(self, error: Exception, context: str = "") -> None:
        """
        Handle authentication-specific errors with detailed user guidance.
        Requirement: 1.3 - Authentication error messages
        """
        error_str = str(error).lower()
        
        if "invalid" in error_str or "wrong" in error_str:
            message = "Invalid credentials. Please check your email and password."
        elif "expired" in error_str:
            message = "Your session has expired. Please log in again."
        elif "permission" in error_str:
            message = "Access denied. You don't have permission to use this dashboard."
        else:
            message = f"Authentication failed. {context}"
        
        self.handle_error(error, ErrorType.AUTHENTICATION, message, show_details=False)
        
    
    def handle_validation_error(self, error: Exception, field_name: str = "", context: str = "") -> None:
        """
        Handle validation errors with specific field guidance.
        Requirements: 3.6, 5.6 - Validation error messages
        """
        error_str = str(error).lower()
        
        if field_name:
            if "citizen_id" in field_name.lower():
                if "unique" in error_str or "exists" in error_str:
                    message = f"Citizen ID already exists. Please use a different ID."
                else:
                    message = f"Invalid Citizen ID format. Please check the format and try again."
            elif "email" in field_name.lower():
                if "unique" in error_str:
                    message = f"Email already registered. Please use a different email address."
                elif "format" in error_str or "invalid" in error_str:
                    message = f"Invalid email format. Please enter a valid email address."
                else:
                    message = f"Email validation failed. Please check the email format."
            elif "phone" in field_name.lower():
                message = f"Invalid phone number format. Please enter a valid phone number."
            else:
                message = f"Invalid {field_name}. Please check the format and try again."
        else:
            message = f"Validation failed. {context if context else 'Please check your input data.'}"
        
        self.handle_error(error, ErrorType.FORM_VALIDATION, message, show_details=False)
    
    def handle_deletion_error(self, error: Exception, user_name: str = "", context: str = "") -> None:
        """
        Handle user deletion errors with clear feedback.
        Requirement: 6.5 - Deletion error messages
        """
        error_str = str(error).lower()
        
        if "not found" in error_str:
            message = f"Cannot delete user {user_name}. User not found or already deleted."
        elif "permission" in error_str:
            message = f"Permission denied. You cannot delete user {user_name}."
        elif "cascade" in error_str or "related" in error_str:
            message = f"Failed to delete related data for user {user_name}. Some data may remain."
        else:
            message = f"Failed to delete user {user_name}. {context}"
        
        self.handle_error(error, ErrorType.DATABASE, message, show_details=True)
        
        # Show recovery guidance
        st.warning("🔄 **What to do next:**\n- Refresh the page and try again\n- Check if the user still exists in the list\n- Contact support if the problem persists")
    
    def handle_audit_failure(self, error: Exception, operation: str = "", user_id: str = "") -> None:
        """
        Handle audit logging failures gracefully.
        Requirement: 8.4 - Audit logging failure handling
        """
        message = f"Operation completed successfully, but audit logging failed for {operation}"
        if user_id:
            message += f" (User: {user_id})"
        
        self.handle_error(error, ErrorType.AUDIT_FAILURE, message, show_details=False, log_error=True)
        
        # Show that the main operation succeeded
        st.success("✅ Your operation was completed successfully!")
        st.warning("⚠️ Audit logging failed, but your changes were saved. This has been logged for administrator review.")
    
    def handle_firebase_error(self, error: Exception, operation: str = "") -> None:
        """Handle Firebase-specific errors with actionable guidance."""
        error_str = str(error).lower()
        
        if "quota" in error_str or "limit" in error_str:
            message = "Database quota exceeded. Please try again later."
            guidance = "💡 **Quota exceeded:**\n- Wait a few minutes before trying again\n- Contact your administrator about upgrading the plan"
        elif "permission" in error_str:
            message = "Database permission denied. Please check your access rights."
            guidance = "🔒 **Permission issue:**\n- Verify your admin credentials\n- Contact your administrator to check permissions"
        elif "network" in error_str or "connection" in error_str:
            message = "Connection to Firebase failed. Please check your internet connection."
            guidance = "🌐 **Connection issue:**\n- Check your internet connection\n- Try refreshing the page\n- Wait a moment and try again"
        else:
            message = f"Firebase error during {operation}. Please try again."
            guidance = "🔧 **Firebase error:**\n- Try refreshing the page\n- Wait a moment and retry\n- Contact support if this persists"
        
        self.handle_error(error, ErrorType.FIREBASE_ERROR, message, show_details=False)
        st.info(guidance)
    
    def get_error_history(self) -> List[Dict[str, Any]]:
        """Get the error history for debugging."""
        return self.error_history.copy()
    
    def clear_error_history(self) -> None:
        """Clear the error history."""
        self.error_history.clear()
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of recent errors for monitoring."""
        if not self.error_history:
            return {"total_errors": 0, "recent_errors": 0, "error_types": {}}
        
        recent_errors = [
            error for error in self.error_history 
            if (datetime.utcnow() - error['timestamp']).total_seconds() < 3600  # Last hour
        ]
        
        error_types = {}
        for error in self.error_history:
            error_type = error['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "recent_errors": len(recent_errors),
            "error_types": error_types,
            "last_error": self.error_history[-1] if self.error_history else None
        }


class FeedbackManager:
    """
    Enhanced user feedback management with comprehensive message types and styling.
    """
    
    @staticmethod
    def show_success(message: str, icon: str = "✅", details: str = None) -> None:
        """Display success message with optional details."""
        st.success(f"{icon} {message}")
        if details:
            with st.expander("📋 Details"):
                st.write(details)
    
    @staticmethod
    def show_error(message: str, icon: str = "❌", details: str = None, show_help: bool = True) -> None:
        """Display error message with optional details and help."""
        st.error(f"{icon} {message}")
        if details:
            with st.expander("🔧 Technical Details"):
                st.code(details)
        if show_help:
            st.info("💡 **Need help?** Try refreshing the page or contact support if the problem persists.")
    
    @staticmethod
    def show_warning(message: str, icon: str = "⚠️", action_text: str = None) -> None:
        """Display warning message with optional action guidance."""
        st.warning(f"{icon} {message}")
        if action_text:
            st.info(f"🔄 **What to do:** {action_text}")
    
    @staticmethod
    def show_info(message: str, icon: str = "ℹ️") -> None:
        """Display info message with consistent styling."""
        st.info(f"{icon} {message}")
    
    @staticmethod
    def show_validation_errors(errors: List[str], title: str = "Please fix the following errors:", 
                             show_guidance: bool = True) -> None:
        """Display validation errors with helpful guidance."""
        if not errors:
            return
        
        st.error(f"❌ **{title}**")
        for i, error in enumerate(errors, 1):
            st.markdown(f"   {i}. {error}")
        
        if show_guidance:
            st.info("💡 **Tips:**\n- Check required fields are filled\n- Verify data formats (email, phone, etc.)\n- Ensure unique values where required")
    
    @staticmethod
    def show_form_feedback(validation_result: Dict[str, Any], form_name: str = "form") -> bool:
        """
        Display comprehensive form validation feedback.
        
        Args:
            validation_result: Dictionary with 'valid' boolean and 'errors' list
            form_name: Name of the form for context
            
        Returns:
            True if validation passed, False otherwise
        """
        if validation_result.get('valid', False):
            FeedbackManager.show_success(f"✅ {form_name.title()} data is valid and ready to save!")
            return True
        else:
            errors = validation_result.get('errors', [])
            if errors:
                FeedbackManager.show_validation_errors(
                    errors, 
                    f"Please fix the following {form_name} errors:",
                    show_guidance=True
                )
            return False
    
    @staticmethod
    def show_operation_result(success: bool, 
                            success_message: str, 
                            error_message: str = "Operation failed",
                            operation_type: str = "operation") -> None:
        """Display comprehensive operation result with context."""
        if success:
            FeedbackManager.show_success(
                success_message, 
                details=f"{operation_type.title()} completed at {datetime.now().strftime('%H:%M:%S')}"
            )
        else:
            FeedbackManager.show_error(
                error_message,
                show_help=True
            )
    
    @staticmethod
    def show_confirmation_dialog(title: str, message: str, confirm_text: str = "Confirm", 
                               cancel_text: str = "Cancel") -> bool:
        """
        Display a confirmation dialog for destructive actions.
        
        Returns:
            True if confirmed, False if cancelled
        """
        st.warning(f"⚠️ **{title}**")
        st.write(message)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✅ {confirm_text}", type="primary"):
                return True
        with col2:
            if st.button(f"❌ {cancel_text}"):
                return False
        
        return False
    
    @staticmethod
    def show_progress_feedback(current: int, total: int, operation: str = "Processing") -> None:
        """Show progress feedback for multi-step operations."""
        progress = current / total if total > 0 else 0
        st.progress(progress)
        st.write(f"{operation}: {current}/{total} ({progress:.1%})")
    
    @staticmethod
    def show_audit_status(success: bool, operation: str, user_id: str = "") -> None:
        """Show audit logging status feedback."""
        if success:
            st.success(f"✅ {operation} completed and logged successfully")
        else:
            st.warning(f"⚠️ {operation} completed but audit logging failed")
            if user_id:
                st.caption(f"Operation affected user: {user_id}")
    
    @staticmethod
    def show_field_help(field_name: str, help_text: str, example: str = None) -> None:
        """Show contextual help for form fields."""
        with st.expander(f"❓ Help for {field_name}"):
            st.write(help_text)
            if example:
                st.code(f"Example: {example}")
    
    @staticmethod
    def show_data_summary(title: str, data: Dict[str, Any]) -> None:
        """Show a formatted data summary."""
        st.subheader(f"📊 {title}")
        for key, value in data.items():
            st.metric(key.replace('_', ' ').title(), value)


class LoadingManager:
    """
    Manages loading indicators and progress feedback.
    """
    
    @staticmethod
    @contextmanager
    def loading_spinner(message: str = "Loading...", success_message: Optional[str] = None):
        """
        Context manager for loading operations with spinner.
        
        Args:
            message: Loading message to display
            success_message: Optional success message to show on completion
        """
        with st.spinner(message):
            try:
                yield
                if success_message:
                    FeedbackManager.show_success(success_message)
            except Exception as e:
                # Re-raise the exception to be handled by the caller
                raise e
    
    @staticmethod
    def show_progress_bar(progress: float, message: str = "") -> None:
        """
        Display a progress bar with optional message.
        
        Args:
            progress: Progress value between 0.0 and 1.0
            message: Optional progress message
        """
        if message:
            st.write(message)
        st.progress(progress)
    
    @staticmethod
    def show_step_progress(current_step: int, total_steps: int, step_names: List[str] = None) -> None:
        """
        Display step-based progress indicator.
        
        Args:
            current_step: Current step number (1-based)
            total_steps: Total number of steps
            step_names: Optional list of step names
        """
        progress = (current_step - 1) / max(1, total_steps - 1) if total_steps > 1 else 1.0
        st.progress(progress)
        
        if step_names and len(step_names) >= total_steps:
            cols = st.columns(total_steps)
            for i in range(total_steps):
                with cols[i]:
                    if i + 1 == current_step:
                        st.markdown(f"**🔵 {step_names[i]}**")
                    elif i + 1 < current_step:
                        st.markdown(f"✅ {step_names[i]}")
                    else:
                        st.markdown(f"⚪ {step_names[i]}")


def safe_execute(func: Callable, 
                error_handler: ErrorHandler,
                error_type: ErrorType = ErrorType.SYSTEM,
                user_message: Optional[str] = None,
                show_details: bool = False,
                default_return: Any = None) -> Any:
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        error_handler: ErrorHandler instance
        error_type: Type of error for categorized handling
        user_message: Custom user-friendly message
        show_details: Whether to show technical details
        default_return: Value to return on error
        
    Returns:
        Function result or default_return on error
    """
    try:
        return func()
    except Exception as e:
        error_handler.handle_error(e, error_type, user_message, show_details)
        return default_return


def validate_and_show_errors(validation_func: Callable, 
                           data: Any, 
                           field_name: str = "data") -> Tuple[bool, List[str]]:
    """
    Validate data and show errors if validation fails.
    
    Args:
        validation_func: Function that validates the data
        data: Data to validate
        field_name: Name of the field being validated
        
    Returns:
        Tuple of (is_valid, error_list)
    """
    try:
        result = validation_func(data)
        
        if isinstance(result, dict):
            is_valid = result.get('valid', False)
            errors = result.get('errors', [])
        elif isinstance(result, bool):
            is_valid = result
            errors = [] if result else [f"Invalid {field_name}"]
        else:
            # Assume validation passed if no specific format
            is_valid = True
            errors = []
        
        if not is_valid and errors:
            FeedbackManager.show_validation_errors(errors, f"Validation errors for {field_name}:")
        
        return is_valid, errors
        
    except Exception as e:
        error_msg = f"Validation failed for {field_name}: {str(e)}"
        FeedbackManager.show_error(error_msg)
        return False, [error_msg]


# Global instances for easy access
error_handler = ErrorHandler()
feedback_manager = FeedbackManager()
loading_manager = LoadingManager()


# Enhanced error recovery and retry mechanisms
class ErrorRecovery:
    """Provides error recovery and retry mechanisms."""
    
    @staticmethod
    def retry_operation(func: Callable, max_retries: int = 3, delay: float = 1.0, 
                       error_handler: ErrorHandler = None) -> Tuple[bool, Any]:
        """
        Retry an operation with exponential backoff.
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            delay: Initial delay between retries (seconds)
            error_handler: ErrorHandler instance for logging
            
        Returns:
            Tuple of (success, result)
        """
        import time
        
        for attempt in range(max_retries + 1):
            try:
                result = func()
                return True, result
            except Exception as e:
                if attempt == max_retries:
                    if error_handler:
                        error_handler.handle_error(
                            e, ErrorType.SYSTEM, 
                            f"Operation failed after {max_retries} retries"
                        )
                    return False, None
                
                # Wait before retry with exponential backoff
                time.sleep(delay * (2 ** attempt))
        
        return False, None
    
    @staticmethod
    def safe_database_operation(operation: Callable, operation_name: str = "database operation") -> Any:
        """
        Safely execute a database operation with comprehensive error handling.
        
        Args:
            operation: Database operation function
            operation_name: Name of the operation for error messages
            
        Returns:
            Operation result or None on failure
        """
        try:
            return operation()
        except Exception as e:
            error_str = str(e).lower()
            
            if "permission" in error_str or "unauthorized" in error_str:
                error_handler.handle_error(
                    e, ErrorType.PERMISSION,
                    f"Permission denied for {operation_name}. Please check your access rights."
                )
            elif "network" in error_str or "connection" in error_str:
                error_handler.handle_error(
                    e, ErrorType.NETWORK,
                    f"Network error during {operation_name}. Please check your connection."
                )
            elif "quota" in error_str or "limit" in error_str:
                error_handler.handle_error(
                    e, ErrorType.FIREBASE_ERROR,
                    f"Database quota exceeded during {operation_name}. Please try again later."
                )
            else:
                error_handler.handle_firebase_error(e, operation_name)
            
            return None


# Enhanced validation helpers
def validate_user_input(data: Dict[str, Any], required_fields: List[str], 
                       field_validators: Dict[str, Callable] = None) -> Tuple[bool, List[str]]:
    """
    Comprehensive user input validation with detailed error messages.
    
    Args:
        data: Input data to validate
        required_fields: List of required field names
        field_validators: Optional dict of field-specific validators
        
    Returns:
        Tuple of (is_valid, error_list)
    """
    errors = []
    
    # Check required fields
    for field in required_fields:
        if not data.get(field):
            errors.append(f"{field.replace('_', ' ').title()} is required")
    
    # Run field-specific validators
    if field_validators:
        for field, validator in field_validators.items():
            if field in data and data[field]:
                try:
                    if not validator(data[field]):
                        errors.append(f"Invalid {field.replace('_', ' ').lower()} format")
                except Exception as e:
                    errors.append(f"Validation error for {field}: {str(e)}")
    
    return len(errors) == 0, errors


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    # Remove common separators and plus sign
    clean_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
    # Check if it's all digits and reasonable length
    return clean_phone.isdigit() and 10 <= len(clean_phone) <= 15


def validate_citizen_id(citizen_id: str) -> bool:
    """Validate citizen ID format."""
    # Remove spaces and check if it's alphanumeric with reasonable length
    clean_id = re.sub(r'\s', '', citizen_id)
    return clean_id.isalnum() and 8 <= len(clean_id) <= 20


# Comprehensive error context managers
@contextmanager
def handle_user_creation_errors():
    """Context manager for user creation error handling."""
    try:
        yield
    except ValueError as e:
        error_handler.handle_validation_error(e, context="user creation")
    except Exception as e:
        if "citizen_id" in str(e).lower() and "unique" in str(e).lower():
            error_handler.handle_error(
                e, ErrorType.DUPLICATE_DATA,
                "This Citizen ID is already registered. Please use a different ID."
            )
        else:
            error_handler.handle_firebase_error(e, "user creation")


@contextmanager
def handle_user_update_errors(user_id: str = ""):
    """Context manager for user update error handling."""
    try:
        yield
    except ValueError as e:
        error_handler.handle_validation_error(e, context=f"updating user {user_id}")
    except Exception as e:
        error_handler.handle_firebase_error(e, f"user update for {user_id}")


@contextmanager
def handle_user_deletion_errors(user_name: str = ""):
    """Context manager for user deletion error handling."""
    try:
        yield
    except Exception as e:
        error_handler.handle_deletion_error(e, user_name, "Please try again or contact support.")


@contextmanager
def handle_audit_errors(operation: str = "", user_id: str = ""):
    """Context manager for audit logging error handling."""
    try:
        yield
    except Exception as e:
        error_handler.handle_audit_failure(e, operation, user_id)


# Convenience functions for backward compatibility (enhanced)
def show_success_message(message: str, details: str = None) -> None:
    """Display success message - enhanced backward compatibility."""
    feedback_manager.show_success(message, details=details)


def show_error_message(message: str, details: str = None, show_help: bool = True) -> None:
    """Display error message - enhanced backward compatibility."""
    feedback_manager.show_error(message, details=details, show_help=show_help)


def show_warning_message(message: str, action_text: str = None) -> None:
    """Display warning message - enhanced backward compatibility."""
    feedback_manager.show_warning(message, action_text=action_text)


def show_info_message(message: str) -> None:
    """Display info message - backward compatibility."""
    feedback_manager.show_info(message)


def show_validation_errors(errors: List[str], title: str = "Please fix the following errors:") -> None:
    """Display validation errors - enhanced backward compatibility."""
    feedback_manager.show_validation_errors(errors, title, show_guidance=True)