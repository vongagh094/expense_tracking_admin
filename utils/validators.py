"""
Validation utilities for user data fields in the Firebase Admin Dashboard.
Provides comprehensive validation functions for all user data types.
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from email_validator import validate_email, EmailNotValidError


def validate_required_field(value: Any, field_name: str) -> Dict[str, Any]:
    """Validate that a required field is not empty."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return {"valid": False, "error": f"{field_name} is required"}
    return {"valid": True}


def validate_email_field(email: str) -> Dict[str, Any]:
    """Validate email format."""
    if not email or not email.strip():
        return {"valid": False, "error": "Email is required"}
    
    try:
        # Use check_deliverability=False to avoid DNS checks for testing
        validate_email(email, check_deliverability=False)
        return {"valid": True}
    except EmailNotValidError:
        return {"valid": False, "error": "Invalid email format"}


def validate_phone_number(phone: str) -> Dict[str, Any]:
    """Validate phone number (basic required field check only)."""
    if not phone or not phone.strip():
        return {"valid": False, "error": "Phone number is required"}
    
    return {"valid": True}


def validate_citizen_id(citizen_id: str) -> Dict[str, Any]:
    """Validate Vietnamese citizen ID format."""
    if not citizen_id or not citizen_id.strip():
        return {"valid": False, "error": "Citizen ID is required"}
    
    clean_id = citizen_id.strip()
    
    # Vietnamese citizen ID is 12 digits
    if not re.match(r'^\d{12}$', clean_id):
        return {"valid": False, "error": "Citizen ID must be exactly 12 digits"}
    
    return {"valid": True}


def validate_passcode(passcode: str) -> Dict[str, Any]:
    """Validate user passcode."""
    if not passcode or not passcode.strip():
        return {"valid": False, "error": "Passcode is required"}
    
    clean_passcode = passcode.strip()
    
    # Passcode should be 4-6 digits
    if not re.match(r'^\d{4,6}$', clean_passcode):
        return {"valid": False, "error": "Passcode must be 4-6 digits"}
    
    return {"valid": True}


def validate_name(name: str) -> Dict[str, Any]:
    """Validate person name."""
    if not name or not name.strip():
        return {"valid": False, "error": "Name is required"}
    
    clean_name = name.strip()
    
    # Name should be at least 2 characters and contain only letters, spaces, and Vietnamese characters
    if len(clean_name) < 2:
        return {"valid": False, "error": "Name must be at least 2 characters"}
    
    # Allow Vietnamese characters, letters, spaces, and common punctuation
    if not re.match(r'^[a-zA-ZÀ-ỹ\s\.\-\']+$', clean_name):
        return {"valid": False, "error": "Name contains invalid characters"}
    
    return {"valid": True}


def validate_date_of_birth(dob: datetime) -> Dict[str, Any]:
    """Validate date of birth."""
    if not dob:
        return {"valid": False, "error": "Date of birth is required"}
    
    current_date = datetime.now()
    
    # Check if date is not in the future
    if dob > current_date:
        return {"valid": False, "error": "Date of birth cannot be in the future"}
    
    # Check reasonable age limits (0-150 years)
    age_years = (current_date - dob).days / 365.25
    if age_years > 150:
        return {"valid": False, "error": "Date of birth is too far in the past"}
    
    return {"valid": True}


def validate_address(address: str) -> Dict[str, Any]:
    """Validate address field."""
    if not address or not address.strip():
        return {"valid": False, "error": "Address is required"}
    
    clean_address = address.strip()
    
    if len(clean_address) < 5:
        return {"valid": False, "error": "Address must be at least 5 characters"}
    
    return {"valid": True}


def validate_gender(gender: Optional[str]) -> Dict[str, Any]:
    """Validate gender field."""
    if gender is None:
        return {"valid": True}  # Optional field
    
    valid_genders = ["Male", "Female", "Other", "Nam", "Nữ", "Khác"]
    if gender not in valid_genders:
        return {"valid": False, "error": f"Gender must be one of: {', '.join(valid_genders)}"}
    
    return {"valid": True}


def validate_qr_payload(qr_payload: Optional[str]) -> Dict[str, Any]:
    """Validate QR payload text."""
    if qr_payload is None or qr_payload.strip() == "":
        return {"valid": True}  # Optional field, empty means use uid as fallback
    
    clean_payload = qr_payload.strip()
    
    # QR payload should not be too long (reasonable limit for QR codes)
    if len(clean_payload) > 500:
        return {"valid": False, "error": "QR payload is too long (max 500 characters)"}
    
    return {"valid": True}


def validate_relationship(relationship: str) -> Dict[str, Any]:
    """Validate household member relationship."""
    if not relationship or not relationship.strip():
        return {"valid": False, "error": "Relationship is required"}
    
    valid_relationships = [
        "Head", "Spouse", "Child", "Parent", "Sibling", "Grandparent", 
        "Grandchild", "Other", "Chủ hộ", "Vợ/Chồng", "Con", "Cha/Mẹ", 
        "Anh/Chị/Em", "Ông/Bà", "Cháu", "Khác"
    ]
    
    if relationship not in valid_relationships:
        return {"valid": False, "error": f"Relationship must be one of: {', '.join(valid_relationships)}"}
    
    return {"valid": True}


def validate_user_profile_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate complete user profile data."""
    errors = []
    
    # Required fields validation
    required_fields = ['name', 'email', 'phone', 'citizen_id', 'passcode']
    for field in required_fields:
        result = validate_required_field(data.get(field), field)
        if not result["valid"]:
            errors.append(result["error"])
    
    # Specific field validations
    if data.get('email'):
        result = validate_email_field(data['email'])
        if not result["valid"]:
            errors.append(result["error"])
    
    if data.get('phone'):
        result = validate_phone_number(data['phone'])
        if not result["valid"]:
            errors.append(result["error"])
    
    if data.get('citizen_id'):
        result = validate_citizen_id(data['citizen_id'])
        if not result["valid"]:
            errors.append(result["error"])
    
    if data.get('passcode'):
        result = validate_passcode(data['passcode'])
        if not result["valid"]:
            errors.append(result["error"])
    
    if data.get('name'):
        result = validate_name(data['name'])
        if not result["valid"]:
            errors.append(result["error"])
    
    if data.get('dob'):
        result = validate_date_of_birth(data['dob'])
        if not result["valid"]:
            errors.append(result["error"])
    
    if data.get('gender'):
        result = validate_gender(data['gender'])
        if not result["valid"]:
            errors.append(result["error"])
    
    # QR payload validations
    for qr_field in ['qr_home', 'qr_card', 'qr_id_detail', 'qr_residence']:
        if data.get(qr_field):
            result = validate_qr_payload(data[qr_field])
            if not result["valid"]:
                errors.append(f"{qr_field}: {result['error']}")
    
    return {"valid": len(errors) == 0, "errors": errors}


def validate_citizen_card_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate citizen card data."""
    errors = []
    
    # Required fields for citizen card
    required_fields = ['full_name', 'citizen_id', 'date_of_birth', 'place_of_birth', 
                      'birth_registration_place', 'hometown', 'permanent_address']
    
    for field in required_fields:
        result = validate_required_field(data.get(field), field)
        if not result["valid"]:
            errors.append(result["error"])
    
    # Specific validations
    if data.get('full_name'):
        result = validate_name(data['full_name'])
        if not result["valid"]:
            errors.append(f"Full name: {result['error']}")
    
    if data.get('citizen_id'):
        result = validate_citizen_id(data['citizen_id'])
        if not result["valid"]:
            errors.append(f"Citizen ID: {result['error']}")
    
    if data.get('date_of_birth'):
        result = validate_date_of_birth(data['date_of_birth'])
        if not result["valid"]:
            errors.append(f"Date of birth: {result['error']}")
    
    if data.get('permanent_address'):
        result = validate_address(data['permanent_address'])
        if not result["valid"]:
            errors.append(f"Permanent address: {result['error']}")
    
    if data.get('qr_payload'):
        result = validate_qr_payload(data['qr_payload'])
        if not result["valid"]:
            errors.append(f"QR payload: {result['error']}")
    
    return {"valid": len(errors) == 0, "errors": errors}


def validate_residence_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate residence data."""
    errors = []
    
    # Required fields for residence
    required_fields = ['full_name', 'citizen_id', 'permanent_address', 'current_address']
    
    for field in required_fields:
        result = validate_required_field(data.get(field), field)
        if not result["valid"]:
            errors.append(result["error"])
    
    # Specific validations
    if data.get('full_name'):
        result = validate_name(data['full_name'])
        if not result["valid"]:
            errors.append(f"Full name: {result['error']}")
    
    if data.get('citizen_id'):
        result = validate_citizen_id(data['citizen_id'])
        if not result["valid"]:
            errors.append(f"Citizen ID: {result['error']}")
    
    if data.get('permanent_address'):
        result = validate_address(data['permanent_address'])
        if not result["valid"]:
            errors.append(f"Permanent address: {result['error']}")
    
    if data.get('current_address'):
        result = validate_address(data['current_address'])
        if not result["valid"]:
            errors.append(f"Current address: {result['error']}")
    
    if data.get('relationship_to_head'):
        result = validate_relationship(data['relationship_to_head'])
        if not result["valid"]:
            errors.append(f"Relationship to head: {result['error']}")
    
    if data.get('qr_payload'):
        result = validate_qr_payload(data['qr_payload'])
        if not result["valid"]:
            errors.append(f"QR payload: {result['error']}")
    
    return {"valid": len(errors) == 0, "errors": errors}


def validate_household_member_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate household member data."""
    errors = []
    
    # Required fields for household member
    required_fields = ['name', 'relationship']
    
    for field in required_fields:
        result = validate_required_field(data.get(field), field)
        if not result["valid"]:
            errors.append(result["error"])
    
    # Specific validations
    if data.get('name'):
        result = validate_name(data['name'])
        if not result["valid"]:
            errors.append(f"Name: {result['error']}")
    
    if data.get('relationship'):
        result = validate_relationship(data['relationship'])
        if not result["valid"]:
            errors.append(f"Relationship: {result['error']}")
    
    if data.get('citizen_id'):
        result = validate_citizen_id(data['citizen_id'])
        if not result["valid"]:
            errors.append(f"Citizen ID: {result['error']}")
    
    if data.get('dob'):
        result = validate_date_of_birth(data['dob'])
        if not result["valid"]:
            errors.append(f"Date of birth: {result['error']}")
    
    return {"valid": len(errors) == 0, "errors": errors}

# Convenience functions for UserManager compatibility
def validate_user_profile(data: Dict[str, Any]) -> List[str]:
    """
    Validate user profile data and return list of errors.
    
    Args:
        data: User profile data to validate
        
    Returns:
        List of validation error messages
    """
    result = validate_user_profile_data(data)
    return result.get('errors', [])


def validate_citizen_card(data: Dict[str, Any]) -> List[str]:
    """
    Validate citizen card data and return list of errors.
    
    Args:
        data: Citizen card data to validate
        
    Returns:
        List of validation error messages
    """
    result = validate_citizen_card_data(data)
    return result.get('errors', [])


def validate_residence(data: Dict[str, Any]) -> List[str]:
    """
    Validate residence data and return list of errors.
    
    Args:
        data: Residence data to validate
        
    Returns:
        List of validation error messages
    """
    result = validate_residence_data(data)
    return result.get('errors', [])