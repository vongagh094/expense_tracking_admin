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
        return {"valid": False, "error": f"{field_name} là bắt buộc"}
    return {"valid": True}


def validate_email_field(email: str) -> Dict[str, Any]:
    """Validate email format."""
    if not email or not email.strip():
        # Optional field usually, but if called it might be required context
        # Adjusting strictly:
        return {"valid": False, "error": "Email là bắt buộc"}
    
    try:
        # Use check_deliverability=False to avoid DNS checks for testing
        validate_email(email, check_deliverability=False)
        return {"valid": True}
    except EmailNotValidError:
        return {"valid": False, "error": "Email không đúng định dạng"}


def validate_phone_number(phone: str) -> Dict[str, Any]:
    """Validate phone number (basic required field check only)."""
    if not phone or not phone.strip():
        return {"valid": False, "error": "Số điện thoại là bắt buộc"}
    
    return {"valid": True}


def validate_citizen_id(citizen_id: str) -> Dict[str, Any]:
    """Validate Vietnamese citizen ID format."""
    if not citizen_id or not citizen_id.strip():
        return {"valid": False, "error": "Số CCCD là bắt buộc"}
    
    clean_id = citizen_id.strip()
    
    # Vietnamese citizen ID is 12 digits
    if not re.match(r'^\d{12}$', clean_id):
        return {"valid": False, "error": "Số CCCD phải có đúng 12 chữ số"}
    
    return {"valid": True}


def validate_passcode(passcode: str) -> Dict[str, Any]:
    """Validate user passcode."""
    if not passcode or not passcode.strip():
        return {"valid": False, "error": "Mã bảo mật là bắt buộc"}
    
    clean_passcode = passcode.strip()
    
    # Passcode should be 4-6 digits
    if not re.match(r'^\d{4,6}$', clean_passcode):
        return {"valid": False, "error": "Mã bảo mật phải từ 4-6 số"}
    
    return {"valid": True}


def validate_name(name: str) -> Dict[str, Any]:
    """Validate person name."""
    if not name or not name.strip():
        return {"valid": False, "error": "Họ và tên là bắt buộc"}
    
    clean_name = name.strip()
    
    # Name should be at least 2 characters and contain only letters, spaces, and Vietnamese characters
    if len(clean_name) < 2:
        return {"valid": False, "error": "Tên phải có ít nhất 2 ký tự"}
    
    # Allow Vietnamese characters, letters, spaces, and common punctuation
    if not re.match(r'^[a-zA-ZÀ-ỹ\s\.\-\']+$', clean_name):
        return {"valid": False, "error": "Tên chứa ký tự không hợp lệ"}
    
    return {"valid": True}


def validate_date_of_birth(dob: datetime) -> Dict[str, Any]:
    """Validate date of birth."""
    if not dob:
        return {"valid": False, "error": "Ngày sinh là bắt buộc"}
    
    current_date = datetime.now()
    
    # Check if date is not in the future
    if dob > current_date:
        return {"valid": False, "error": "Ngày sinh không thể ở tương lai"}
    
    # Check reasonable age limits (0-150 years)
    age_years = (current_date - dob).days / 365.25
    if age_years > 150:
        return {"valid": False, "error": "Ngày sinh quá xa trong quá khứ"}
    
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


def validate_date_string(date_str: str, field_name: str = "Date") -> Dict[str, Any]:
    """Validate date string format (DD/MM/YYYY)."""
    if not date_str:
         return {"valid": False, "error": f"{field_name} is required"}
    
    if not re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
        return {"valid": False, "error": f"{field_name}: Invalid format (DD/MM/YYYY)"}
        
    try:
        datetime.strptime(date_str, '%d/%m/%Y')
    except ValueError:
        return {"valid": False, "error": f"{field_name}: Invalid date value"}
        
    return {"valid": True}


def validate_user_profile_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate complete user profile data."""
    errors = []
    
    # Required fields validation
    required_fields = ['full_name', 'email', 'phone_number', 'citizen_id']
    for field in required_fields:
        # Handle aliases
        val = data.get(field)
        if val is None:
            if field == 'full_name': val = data.get('name')
            elif field == 'phone_number': val = data.get('phone')
        
        result = validate_required_field(val, field)
        if not result["valid"]:
            errors.append(result["error"])
    
    # Specific field validations
    email = data.get('email')
    if email:
        result = validate_email_field(email)
        if not result["valid"]:
            errors.append(result["error"])
    
    phone = data.get('phone_number') or data.get('phone')
    if phone:
        result = validate_phone_number(phone)
        if not result["valid"]:
            errors.append(result["error"])
    
    citizen_id = data.get('citizen_id')
    if citizen_id:
        result = validate_citizen_id(citizen_id)
        if not result["valid"]:
            errors.append(result["error"])
    
    # Validate Date of Birth (String or Datetime)
    dob = data.get('date_of_birth') or data.get('dob')
    if dob:
        if isinstance(dob, str):
            result = validate_date_string(dob, "Date of birth")
        elif isinstance(dob, datetime) or hasattr(dob, 'date'):
             # Accept if it's already a date object (legacy flow support)
             result = validate_date_of_birth(dob)
        else:
             result = {"valid": False, "error": "Date of birth has invalid type"}
             
        if not result["valid"]:
            errors.append(result["error"])
    else:
        # It's a required field in new schema
        errors.append("Date of birth is required")
    
    # Validate Address Fields
    if data.get('permanent_address'):
        result = validate_address(data['permanent_address'])
        if not result["valid"]:
            errors.append(f"Permanent address: {result['error']}")

    if data.get('current_address'):
        result = validate_address(data['current_address'])
        if not result["valid"]:
            errors.append(f"Current address: {result['error']}")

    # Common generic address check if others missing
    if not data.get('permanent_address') and not data.get('current_address') and data.get('address'):
         result = validate_address(data['address'])
         if not result["valid"]:
            errors.append(f"Address: {result['error']}")

    
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
    """
    Validate citizen card data against 'Citizen Card Data Guide'.
    """
    errors = []
    
    # Required fields per guide
    required_fields = [
        'full_name', 'citizen_id', 'date_of_birth', 'gender', 'nationality',
        'birthplace', 'birth_registration_place', 'hometown',
        'permanent_address', 'current_address', 
        'identifying_marks', 'issue_date', 'issue_place'
    ]
    
    for field in required_fields:
        # Handle potential backward compat aliases for validation checks
        val = data.get(field)
        if val is None:
            if field == 'birthplace': val = data.get('place_of_birth')
            elif field == 'identifying_marks': val = data.get('personal_identification')
            elif field == 'issue_place': val = data.get('issuing_authority')
            
        result = validate_required_field(val, field)
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
            
    # Date validations (String format)
    for date_field in ['date_of_birth', 'issue_date']:
        val = data.get(date_field)
        if val:
            if isinstance(val, str):
                result = validate_date_string(val, date_field.replace('_', ' ').title())
                if not result["valid"]:
                    errors.append(result["error"])
            elif isinstance(val, date) or isinstance(val, datetime):
                 # Allow object types if strict mode off, but warn or pass
                 pass 
    
    if data.get('qr_code_data') or data.get('qr_payload'):
        val = data.get('qr_code_data') or data.get('qr_payload')
        result = validate_qr_payload(val)
        if not result["valid"]:
            errors.append(f"QR Data: {result['error']}")
            
    return {"valid": len(errors) == 0, "errors": errors}


def validate_residence_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate residence data."""
    errors = []
    
    # Required fields per Resident Information Data Guide
    required_fields = [
        'full_name', 'id_number', 'birth_date', 'gender',
        'permanent_address', 'current_address', 
        'household_head_name', 'household_head_id', 'relation_to_head'
    ]
    
    for field in required_fields:
        # Handle field aliases if old data is passed
        val = data.get(field)
        if val is None:
            if field == 'id_number': val = data.get('citizen_id')
            elif field == 'household_head_name': val = data.get('head_of_household')
            elif field == 'household_head_id': val = data.get('head_of_household_id') # Potential alias
            elif field == 'relation_to_head': val = data.get('relationship_to_head')
        
        result = validate_required_field(val, field)
        if not result["valid"]:
            errors.append(result["error"])
    
    # Specific validations
    if data.get('full_name'):
        result = validate_name(data['full_name'])
        if not result["valid"]:
            errors.append(f"Full name: {result['error']}")

    # Validate ID Number
    id_num = data.get('id_number') or data.get('citizen_id')
    if id_num:
        result = validate_citizen_id(id_num)
        if not result["valid"]:
            errors.append(f"ID Number: {result['error']}")

    # Validate Dates
    for date_field in ['birth_date', 'temporary_start', 'temporary_end']:
        val = data.get(date_field)
        if val:
            if not re.match(r'^\d{2}/\d{2}/\d{4}$', str(val)):
                errors.append(f"{date_field}: Invalid format (DD/MM/YYYY)")

    if data.get('permanent_address'):
        result = validate_address(data['permanent_address'])
        if not result["valid"]:
            errors.append(f"Permanent address: {result['error']}")

    if data.get('current_address'):
        result = validate_address(data['current_address'])
        if not result["valid"]:
            errors.append(f"Current address: {result['error']}")
    
    if data.get('relation_to_head') or data.get('relationship_to_head'):
        val = data.get('relation_to_head') or data.get('relationship_to_head')
        result = validate_relationship(val)
        if not result["valid"]:
            errors.append(f"Relation to head: {result['error']}")
            
    return {"valid": len(errors) == 0, "errors": errors}


def validate_household_member_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate household member data."""
    errors = []
    
    # Required fields for household member per schema
    # Note: Schema says id_number, birth_date, gender are required
    required_fields = ['full_name', 'id_number', 'birth_date', 'gender', 'relation_to_head']
    
    for field in required_fields:
        # Handle field aliases
        val = data.get(field)
        if val is None:
            if field == 'full_name': val = data.get('name')
            elif field == 'id_number': val = data.get('citizen_id')
            elif field == 'birth_date': val = data.get('dob')
            elif field == 'relation_to_head': val = data.get('relationship')
            
        result = validate_required_field(val, field)
        if not result["valid"]:
            errors.append(result["error"])
    
    # Specific validations
    name_val = data.get('full_name') or data.get('name')
    if name_val:
        result = validate_name(name_val)
        if not result["valid"]:
            errors.append(f"Name: {result['error']}")
    
    rel_val = data.get('relation_to_head') or data.get('relationship')
    if rel_val:
        result = validate_relationship(rel_val)
        if not result["valid"]:
            errors.append(f"Relationship: {result['error']}")
    
    id_val = data.get('id_number') or data.get('citizen_id')
    if id_val:
        result = validate_citizen_id(id_val)
        if not result["valid"]:
            errors.append(f"ID Number: {result['error']}")
    
    dob_val = data.get('birth_date') or data.get('dob')
    if dob_val:
        # Check string format for schema compliance
        if not re.match(r'^\d{2}/\d{2}/\d{4}$', str(dob_val)):
             errors.append(f"Birth Date: Invalid format (DD/MM/YYYY)")
    
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