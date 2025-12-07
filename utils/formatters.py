"""
Data formatting utilities for the Firebase Admin Dashboard.
Provides functions for data transformation and display formatting.
"""

from datetime import datetime
from typing import Any, Optional, Dict, List
import re


def format_phone_number(phone: str) -> str:
    """Format phone number for display."""
    if not phone:
        return ""
    
    # Remove all non-digit characters except +
    clean_phone = re.sub(r'[^\d+]', '', phone)
    
    # Format Vietnamese phone numbers
    if clean_phone.startswith('+84'):
        # +84 format: +84 XXX XXX XXX
        if len(clean_phone) == 12:
            return f"+84 {clean_phone[3:6]} {clean_phone[6:9]} {clean_phone[9:12]}"
    elif clean_phone.startswith('84'):
        # 84 format: convert to +84 format
        if len(clean_phone) == 11:
            return f"+84 {clean_phone[2:5]} {clean_phone[5:8]} {clean_phone[8:11]}"
    elif clean_phone.startswith('0'):
        # 0 format: 0XXX XXX XXX
        if len(clean_phone) == 10:
            return f"{clean_phone[0:4]} {clean_phone[4:7]} {clean_phone[7:10]}"
    
    # Return original if no pattern matches
    return phone


def format_citizen_id(citizen_id: str) -> str:
    """Format citizen ID for display."""
    if not citizen_id:
        return ""
    
    # Format as XXX XXX XXX XXX for 12-digit IDs
    clean_id = re.sub(r'\D', '', citizen_id)
    if len(clean_id) == 12:
        return f"{clean_id[0:3]} {clean_id[3:6]} {clean_id[6:9]} {clean_id[9:12]}"
    
    return citizen_id


def format_date(date_obj: Optional[Any], format_type: str = "display") -> str:
    """Format datetime object or string for display."""
    if not date_obj:
        return ""
    
    # Handle string dates
    if isinstance(date_obj, str):
        return date_obj[:10] if len(date_obj) >= 10 else date_obj
    
    # Handle datetime objects
    if not hasattr(date_obj, 'strftime'):
        return str(date_obj)
    
    if format_type == "display":
        return date_obj.strftime("%d/%m/%Y")
    elif format_type == "display_with_time":
        return date_obj.strftime("%d/%m/%Y %H:%M")
    elif format_type == "iso":
        return date_obj.isoformat()
    elif format_type == "long":
        return date_obj.strftime("%B %d, %Y")
    else:
        return date_obj.strftime("%d/%m/%Y")


def format_datetime(datetime_obj: Optional[datetime]) -> str:
    """Format datetime object with time for display."""
    return format_date(datetime_obj, "display_with_time")


def format_name(name: str) -> str:
    """Format name for display (title case)."""
    if not name:
        return ""
    
    # Convert to title case while preserving Vietnamese characters
    return name.strip().title()


def format_address(address: str, max_length: int = None) -> str:
    """Format address for display."""
    if not address:
        return ""
    
    formatted_address = address.strip()
    
    if max_length and len(formatted_address) > max_length:
        return formatted_address[:max_length-3] + "..."
    
    return formatted_address


def format_qr_payload_display(qr_payload: Optional[str], uid: str) -> str:
    """Format QR payload for display, showing fallback if empty."""
    if qr_payload and qr_payload.strip():
        return qr_payload.strip()
    else:
        return f"{uid} (fallback)"


def format_gender(gender: Optional[str]) -> str:
    """Format gender for display."""
    if not gender:
        return ""
    
    # Normalize gender values
    gender_map = {
        "male": "Male",
        "female": "Female", 
        "other": "Other",
        "nam": "Nam",
        "nữ": "Nữ",
        "khác": "Khác"
    }
    
    return gender_map.get(gender.lower(), gender)


def format_relationship(relationship: str) -> str:
    """Format relationship for display."""
    if not relationship:
        return ""
    
    # Capitalize first letter
    return relationship.strip().capitalize()


def format_user_summary(user_data: Dict[str, Any]) -> str:
    """Create a summary string for a user."""
    name = user_data.get('name', 'Unknown')
    citizen_id = format_citizen_id(user_data.get('citizen_id', ''))
    email = user_data.get('email', '')
    
    return f"{name} ({citizen_id}) - {email}"


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def format_age_from_dob(dob: Optional[datetime]) -> str:
    """Calculate and format age from date of birth."""
    if not dob:
        return ""
    
    today = datetime.now()
    age = today.year - dob.year
    
    # Adjust if birthday hasn't occurred this year
    if today.month < dob.month or (today.month == dob.month and today.day < dob.day):
        age -= 1
    
    return f"{age} years old"


def format_time_ago(datetime_obj: Optional[datetime]) -> str:
    """Format datetime as 'time ago' string."""
    if not datetime_obj:
        return ""
    
    now = datetime.utcnow()
    diff = now - datetime_obj
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to specified length with suffix."""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_boolean(value: Optional[bool], true_text: str = "Yes", false_text: str = "No") -> str:
    """Format boolean value for display."""
    if value is None:
        return ""
    return true_text if value else false_text


def format_list_display(items: List[str], separator: str = ", ", max_items: int = None) -> str:
    """Format a list of items for display."""
    if not items:
        return ""
    
    if max_items and len(items) > max_items:
        displayed_items = items[:max_items]
        remaining = len(items) - max_items
        return f"{separator.join(displayed_items)} and {remaining} more"
    
    return separator.join(items)


def format_currency(amount: float, currency: str = "VND") -> str:
    """Format currency amount."""
    if currency == "VND":
        return f"{amount:,.0f} ₫"
    else:
        return f"{amount:,.2f} {currency}"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations."""
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    # Limit length
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    
    return sanitized


def format_search_highlight(text: str, search_term: str) -> str:
    """Add highlighting markup for search results (for Streamlit markdown)."""
    if not search_term or not text:
        return text
    
    # Simple highlighting - replace with bold markdown
    pattern = re.compile(re.escape(search_term), re.IGNORECASE)
    return pattern.sub(f"**{search_term}**", text)


def format_validation_errors(errors: List[str]) -> str:
    """Format validation errors for display."""
    if not errors:
        return ""
    
    if len(errors) == 1:
        return errors[0]
    
    return "• " + "\n• ".join(errors)


def format_audit_action(action_type: str) -> str:
    """Format audit action type for display."""
    action_map = {
        "create": "Created",
        "update": "Updated", 
        "delete": "Deleted",
        "view": "Viewed"
    }
    
    return action_map.get(action_type.lower(), action_type.capitalize())


def format_table_data(data: List[Dict[str, Any]], columns: List[str]) -> List[List[str]]:
    """Format data for table display in Streamlit."""
    formatted_rows = []
    
    for row in data:
        formatted_row = []
        for col in columns:
            value = row.get(col, "")
            
            # Apply specific formatting based on column type
            if col in ['created_at', 'updated_at', 'date_of_birth', 'issue_date', 'expiry_date']:
                if isinstance(value, datetime):
                    formatted_value = format_date(value)
                else:
                    formatted_value = str(value)
            elif col in ['phone']:
                formatted_value = format_phone_number(str(value))
            elif col in ['citizen_id']:
                formatted_value = format_citizen_id(str(value))
            elif col in ['name', 'full_name']:
                formatted_value = format_name(str(value))
            else:
                formatted_value = str(value) if value is not None else ""
            
            formatted_row.append(formatted_value)
        
        formatted_rows.append(formatted_row)
    
    return formatted_rows


def parse_date_input(date_str: str) -> Optional[datetime]:
    """Parse date string from user input into datetime object."""
    if not date_str or not date_str.strip():
        return None
    
    # Try different date formats
    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y", 
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M",
        "%d-%m-%Y %H:%M",
        "%Y-%m-%d %H:%M:%S"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    # If no format matches, return None
    return None


def format_form_data_for_firebase(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format form data for Firebase storage."""
    formatted_data = {}
    
    for key, value in form_data.items():
        if value is None or (isinstance(value, str) and not value.strip()):
            # Skip empty values
            continue
        
        if isinstance(value, str):
            # Clean string values
            formatted_data[key] = value.strip()
        elif isinstance(value, datetime):
            # Keep datetime objects as-is for Firebase
            formatted_data[key] = value
        else:
            formatted_data[key] = value
    
    return formatted_data