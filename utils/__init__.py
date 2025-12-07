"""
Utilities package for the Firebase Admin Dashboard.
Contains validation, data models, and formatting utilities.
"""

from .validators import (
    validate_required_field,
    validate_email_field,
    validate_phone_number,
    validate_citizen_id,
    validate_passcode,
    validate_name,
    validate_date_of_birth,
    validate_address,
    validate_gender,
    validate_qr_payload,
    validate_relationship,
    validate_user_profile_data,
    validate_citizen_card_data,
    validate_residence_data,
    validate_household_member_data
)

from .models import (
    UserProfile,
    CitizenCard,
    Residence,
    HouseholdMember,
    create_user_profile,
    create_citizen_card,
    create_residence,
    create_household_member
)

from .formatters import (
    format_phone_number,
    format_citizen_id,
    format_date,
    format_datetime,
    format_name,
    format_address,
    format_qr_payload_display,
    format_gender,
    format_relationship,
    format_user_summary,
    format_age_from_dob,
    format_time_ago,
    truncate_text,
    format_boolean,
    format_validation_errors,
    format_table_data,
    parse_date_input,
    format_form_data_for_firebase
)

from .error_handler import (
    ErrorHandler,
    FeedbackManager,
    LoadingManager,
    ErrorType,
    FeedbackType,
    error_handler,
    feedback_manager,
    loading_manager,
    safe_execute,
    validate_and_show_errors,
    show_success_message,
    show_error_message,
    show_warning_message,
    show_info_message
)

__all__ = [
    # Validators
    'validate_required_field',
    'validate_email_field', 
    'validate_phone_number',
    'validate_citizen_id',
    'validate_passcode',
    'validate_name',
    'validate_date_of_birth',
    'validate_address',
    'validate_gender',
    'validate_qr_payload',
    'validate_relationship',
    'validate_user_profile_data',
    'validate_citizen_card_data',
    'validate_residence_data',
    'validate_household_member_data',
    
    # Models
    'UserProfile',
    'CitizenCard',
    'Residence', 
    'HouseholdMember',
    'create_user_profile',
    'create_citizen_card',
    'create_residence',
    'create_household_member',
    
    # Formatters
    'format_phone_number',
    'format_citizen_id',
    'format_date',
    'format_datetime',
    'format_name',
    'format_address',
    'format_qr_payload_display',
    'format_gender',
    'format_relationship',
    'format_user_summary',
    'format_age_from_dob',
    'format_time_ago',
    'truncate_text',
    'format_boolean',
    'format_validation_errors',
    'format_table_data',
    'parse_date_input',
    'format_form_data_for_firebase',
    
    # Error Handling
    'ErrorHandler',
    'FeedbackManager',
    'LoadingManager',
    'ErrorType',
    'FeedbackType',
    'error_handler',
    'feedback_manager',
    'loading_manager',
    'safe_execute',
    'validate_and_show_errors',
    'show_success_message',
    'show_error_message',
    'show_warning_message',
    'show_info_message'
]