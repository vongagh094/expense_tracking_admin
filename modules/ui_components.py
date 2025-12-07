"""
Reusable UI Components for Firebase Admin Dashboard

This module provides reusable Streamlit components for consistent UI across the dashboard.
Includes search filters, data tables, forms, and other interactive elements.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
import math

from utils.formatters import (
    format_date, format_phone_number, format_citizen_id,
    format_name, format_qr_payload_display, format_validation_errors
)
from utils.validators import (
    validate_user_profile_data, validate_citizen_card_data,
    validate_residence_data, validate_household_member_data
)

# Use absolute import when available (package run), fall back to local for script run
try:
    from firebase_admin_dashboard.utils.error_handler import feedback_manager, loading_manager
except ImportError:
    from utils.error_handler import feedback_manager, loading_manager


def render_user_search_filters() -> Dict[str, Any]:
    """
    Render search and filtering components for user list.
    
    Returns:
        Dict containing search parameters:
        - search_term: str
        - date_from: datetime or None
        - date_to: datetime or None
        - search_field: str (name, email, citizen_id, or all)
    """
    st.subheader("🔍 Tìm kiếm & Lọc")
    
    # Create columns for search controls
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Search term input
        search_term = st.text_input(
            "Tìm kiếm người dùng",
            placeholder="Nhập tên, email, hoặc số CCCD...",
            help="Tìm kiếm theo tên, email, và số CCCD"
        )
        
        # Search field selector
        search_field = st.selectbox(
            "Tìm trong",
            options=["all", "name", "email", "citizen_id"],
            format_func=lambda x: {
                "all": "Tất cả",
                "name": "Chỉ Tên", 
                "email": "Chỉ Email",
                "citizen_id": "Chỉ số CCCD"
            }[x],
            help="Chọn trường để tìm kiếm"
        )
    
    with col2:
        # Date range filter
        st.write("**Ngày tạo**")
        
        # Date from
        date_from = st.date_input(
            "Từ ngày",
            value=None,
            help="Lọc người dùng tạo từ ngày này"
        )
        
        # Date to  
        date_to = st.date_input(
            "Đến ngày", 
            value=None,
            help="Lọc người dùng tạo đến ngày này"
        )
        
        # Quick date range buttons
        st.write("**Lọc nhanh**")
        col_today, col_week, col_month = st.columns(3)
        
        with col_today:
            if st.button("Hôm nay", help="Người dùng tạo hôm nay"):
                st.session_state.date_from = date.today()
                st.session_state.date_to = date.today()
                st.rerun()
        
        with col_week:
            if st.button("Tuần này", help="Người dùng tạo tuần này"):
                today = date.today()
                week_start = today - timedelta(days=today.weekday())
                st.session_state.date_from = week_start
                st.session_state.date_to = today
                st.rerun()
        
        with col_month:
            if st.button("Tháng này", help="Người dùng tạo tháng này"):
                today = date.today()
                month_start = today.replace(day=1)
                st.session_state.date_from = month_start
                st.session_state.date_to = today
                st.rerun()
    
    # Clear filters button
    if st.button("🗑️ Clear All Filters"):
        # Clear session state
        for key in ['date_from', 'date_to']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    # Convert dates to datetime objects
    date_from_dt = None
    date_to_dt = None
    
    if date_from:
        date_from_dt = datetime.combine(date_from, datetime.min.time())
    
    if date_to:
        date_to_dt = datetime.combine(date_to, datetime.max.time())
    
    return {
        "search_term": search_term.strip() if search_term else "",
        "search_field": search_field,
        "date_from": date_from_dt,
        "date_to": date_to_dt
    }


def render_user_table(users_data: List[Dict[str, Any]], page_size: int = 20) -> Optional[str]:
    """
    Render paginated user table with sorting capabilities.
    
    Args:
        users_data: List of user dictionaries
        page_size: Number of users per page
        
    Returns:
        Selected user UID if a row is clicked, None otherwise
    """
    if not users_data:
        st.info("Không tìm thấy người dùng nào khớp với bộ lọc.")
        return None
    
    # Sort options
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.write(f"**Tìm thấy {len(users_data)} người dùng**")
    
    with col2:
        sort_by = st.selectbox(
            "Sắp xếp theo",
            options=["created_at", "name", "email", "citizen_id"],
            format_func=lambda x: {
                "created_at": "Ngày tạo",
                "name": "Tên",
                "email": "Email", 
                "citizen_id": "CCCD"
            }[x]
        )
    
    with col3:
        sort_order = st.selectbox(
            "Thứ tự",
            options=["desc", "asc"],
            format_func=lambda x: "Mới nhất trước" if x == "desc" else "Cũ nhất trước"
        )
    
    # Sort the data
    reverse_sort = sort_order == "desc"
    try:
        sorted_users = sorted(
            users_data, 
            key=lambda x: x.get(sort_by, ""), 
            reverse=reverse_sort
        )
    except Exception:
        # Fallback if sorting fails
        sorted_users = users_data
    
    # Pagination
    total_pages = math.ceil(len(sorted_users) / page_size)
    
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("⬅️ Trước", disabled=st.session_state.get('current_page', 1) <= 1):
                st.session_state.current_page = max(1, st.session_state.get('current_page', 1) - 1)
                st.rerun()
        
        with col2:
            current_page = st.number_input(
                "Trang",
                min_value=1,
                max_value=total_pages,
                value=st.session_state.get('current_page', 1),
                key="page_input"
            )
            st.session_state.current_page = current_page
            st.write(f"trên {total_pages} trang")
        
        with col3:
            if st.button("Sau ➡️", disabled=st.session_state.get('current_page', 1) >= total_pages):
                st.session_state.current_page = min(total_pages, st.session_state.get('current_page', 1) + 1)
                st.rerun()
    else:
        st.session_state.current_page = 1
    
    # Calculate page slice
    start_idx = (st.session_state.get('current_page', 1) - 1) * page_size
    end_idx = start_idx + page_size
    page_users = sorted_users[start_idx:end_idx]
    
    # Create table data
    table_data = []
    for user in page_users:
        table_data.append({
            "Họ và Tên": format_name(user.get('name', '')),
            "Email": user.get('email', ''),
            "Số CCCD": format_citizen_id(user.get('citizen_id', '')),
            "SĐT": format_phone_number(user.get('phone', '')),
            "Ngày tạo": format_date(user.get('created_at')) if user.get('created_at') else '',
            "UID": user.get('uid', '')
        })
    
    # Display table
    if table_data:
        df = pd.DataFrame(table_data)
        
        # Use st.dataframe with selection
        selected_rows = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Handle row selection
        if selected_rows and len(selected_rows.selection.rows) > 0:
            selected_idx = selected_rows.selection.rows[0]
            selected_user_uid = table_data[selected_idx]["UID"]
            return selected_user_uid
    
    return None


def show_success_message(message: str) -> None:
    """Display success message with consistent styling."""
    feedback_manager.show_success(message)


def show_error_message(message: str) -> None:
    """Display error message with consistent styling."""
    feedback_manager.show_error(message)


def show_warning_message(message: str) -> None:
    """Display warning message with consistent styling."""
    feedback_manager.show_warning(message)


def show_info_message(message: str) -> None:
    """Display info message with consistent styling."""
    feedback_manager.show_info(message)


def render_loading_spinner(message: str = "Loading...") -> None:
    """Display loading spinner with message."""
    with st.spinner(message):
        pass


def render_enhanced_loading_indicator(message: str = "Loading...", 
                                    show_progress: bool = False,
                                    progress_value: float = 0.0) -> None:
    """
    Display enhanced loading indicator with optional progress bar.
    
    Args:
        message: Loading message to display
        show_progress: Whether to show progress bar
        progress_value: Progress value between 0.0 and 1.0
    """
    if show_progress:
        loading_manager.show_progress_bar(progress_value, message)
    else:
        with st.spinner(message):
            pass


def render_operation_feedback(success: bool, 
                            success_message: str,
                            error_message: str = "Operation failed",
                            show_details: bool = False,
                            error_details: str = None) -> None:
    """
    Display feedback for database operations with enhanced error handling.
    
    Args:
        success: Whether the operation was successful
        success_message: Message to show on success
        error_message: Message to show on error
        show_details: Whether to show error details
        error_details: Technical error details to show
    """
    from ..utils.error_handler import feedback_manager
    
    if success:
        feedback_manager.show_success(success_message)
    else:
        feedback_manager.show_error(error_message)
        
        if show_details and error_details:
            with st.expander("🔧 Technical Details"):
                st.code(error_details)


def render_form_validation_feedback(validation_result: Dict[str, Any], 
                                  form_name: str = "form") -> bool:
    """
    Display comprehensive form validation feedback.
    
    Args:
        validation_result: Dictionary with validation results
        form_name: Name of the form for error messages
        
    Returns:
        True if validation passed, False otherwise
    """
    from ..utils.error_handler import feedback_manager
    
    if validation_result.get('valid', False):
        feedback_manager.show_success(f"{form_name.title()} data is valid!")
        return True
    else:
        errors = validation_result.get('errors', [])
        if errors:
            feedback_manager.show_validation_errors(
                errors, 
                f"Please fix the following errors in {form_name}:"
            )
        else:
            feedback_manager.show_error(f"Validation failed for {form_name}")
        return False


def render_confirmation_dialog(
    title: str, 
    message: str, 
    confirm_text: str = "Xác nhận",
    cancel_text: str = "Hủy"
) -> Optional[bool]:
    """
    Render confirmation dialog.
    
    Returns:
        True if confirmed, False if cancelled, None if no action
    """
    st.subheader(title)
    st.write(message)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(confirm_text, type="primary"):
            return True
    
    with col2:
        if st.button(cancel_text):
            return False
    
    return None


def render_breadcrumb(pages: List[Tuple[str, str]]) -> None:
    """
    Render breadcrumb navigation.
    
    Args:
        pages: List of (page_name, page_url) tuples
    """
    breadcrumb_html = " > ".join([
        f'<a href="{url}" style="text-decoration: none; color: #1f77b4;">{name}</a>' 
        if url else f'<span style="color: #666;">{name}</span>'
        for name, url in pages
    ])
    
    st.markdown(f"**Điều hướng:** {breadcrumb_html}", unsafe_allow_html=True)
    st.markdown("---")


def render_section_header(title: str, description: str = None, icon: str = None) -> None:
    """Render consistent section headers."""
    header_text = f"{icon} {title}" if icon else title
    st.subheader(header_text)
    
    if description:
        st.write(description)
    
    st.markdown("---")


def render_data_summary_cards(data: Dict[str, Any]) -> None:
    """Render summary cards for key metrics."""
    cols = st.columns(len(data))
    
    for i, (label, value) in enumerate(data.items()):
        with cols[i]:
            st.metric(label=label, value=value)


def render_empty_state(
    title: str = "Không có dữ liệu", 
    description: str = "Hiện không có dữ liệu để hiển thị.",
    action_text: str = None,
    action_callback = None
) -> None:
    """Render empty state with optional action."""
    st.markdown(
        f"""
        <div style="text-align: center; padding: 2rem; color: #666;">
            <h3>{title}</h3>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if action_text and action_callback:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(action_text):
                action_callback()


def render_field_help_text(field_name: str, help_texts: Dict[str, str]) -> None:
    """Render help text for form fields."""
    if field_name in help_texts:
        st.caption(help_texts[field_name])

def render_user_form(user_data: Dict[str, Any] = None, form_key: str = "user_form") -> Tuple[Dict[str, Any], List[str]]:
    """
    Render user profile creation/editing form.
    
    Args:
        user_data: Existing user data for editing (None for creation)
        form_key: Unique key for the form
        
    Returns:
        Tuple of (form_data, validation_errors)
    """
    st.subheader("👤 Thông tin hồ sơ người dùng")
    
    # Initialize form data
    form_data = {}
    validation_errors = []
    
    # Help texts for fields
    help_texts = {
        "name": "Họ và tên đầy đủ trên giấy tờ tùy thân",
        "email": "Địa chỉ email hợp lệ để liên lạc",
        "phone": "Số điện thoại định dạng Việt Nam (VD: 0123 456 789)",
        "citizen_id": "Số Căn cước công dân 12 chữ số",
        "passcode": "Mã bảo mật 4-6 chữ số để xác thực",
        "address": "Địa chỉ thường trú hiện tại",
        "dob": "Ngày tháng năm sinh",
        "gender": "Giới tính"
    }
    
    with st.form(key=form_key):
        # Required fields section
        st.markdown("**Thông tin bắt buộc**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            form_data['name'] = st.text_input(
                "Họ và tên *",
                value=user_data.get('name', '') if user_data else '',
                placeholder="Nhập họ và tên",
                help=help_texts['name']
            )
            
            form_data['email'] = st.text_input(
                "Email *",
                value=user_data.get('email', '') if user_data else '',
                placeholder="user@example.com",
                help=help_texts['email']
            )
            
            form_data['phone'] = st.text_input(
                "Số điện thoại *",
                value=user_data.get('phone', '') if user_data else '',
                placeholder="0123 456 789",
                help=help_texts['phone']
            )
        
        with col2:
            form_data['citizen_id'] = st.text_input(
                "Số CCCD *",
                value=user_data.get('citizen_id', '') if user_data else '',
                placeholder="123456789012",
                help=help_texts['citizen_id']
            )
            
            form_data['passcode'] = st.text_input(
                "Mã bảo mật *",
                value=user_data.get('passcode', '') if user_data else '',
                type="password",
                placeholder="1234",
                help=help_texts['passcode']
            )
        
        # Optional fields section
        st.markdown("**Thông tin bổ sung**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            form_data['address'] = st.text_area(
                "Địa chỉ",
                value=user_data.get('address', '') if user_data else '',
                placeholder="Nhập địa chỉ cư trú",
                help=help_texts['address']
            )
            
            form_data['dob'] = st.date_input(
                "Ngày sinh",
                value=user_data.get('dob').date() if user_data and user_data.get('dob') else None,
                help=help_texts['dob']
            )
        
        with col2:
            form_data['gender'] = st.selectbox(
                "Giới tính",
                options=["", "Nam", "Nữ", "Khác"],
                index=0 if not user_data or not user_data.get('gender') else 
                      ["", "Male", "Female", "Other", "Nam", "Nữ", "Khác"].index(user_data.get('gender')) if user_data.get('gender') in ["", "Male", "Female", "Other", "Nam", "Nữ", "Khác"] else 0,
                help=help_texts['gender']
            )
        
        # QR Code fields
        st.markdown("**📱 QR Code Data** (để trống để sử dụng UID làm mặc định)")
        
        col1, col2 = st.columns(2)
        with col1:
            form_data['qr_home'] = st.text_input(
                "QR Home",
                value=user_data.get('qr_home', '') if user_data else '',
                placeholder="Để trống = UID"
            )
            form_data['qr_card'] = st.text_input(
                "QR Card",
                value=user_data.get('qr_card', '') if user_data else '',
                placeholder="Để trống = UID"
            )
        with col2:
            form_data['qr_id_detail'] = st.text_input(
                "QR ID Detail",
                value=user_data.get('qr_id_detail', '') if user_data else '',
                placeholder="Để trống = UID"
            )
            form_data['qr_residence'] = st.text_input(
                "QR Residence",
                value=user_data.get('qr_residence', '') if user_data else '',
                placeholder="Để trống = UID"
            )
        
        # Form submission
        submitted = st.form_submit_button(
            "Lưu thông tin hồ sơ" if user_data else "Tạo hồ sơ người dùng",
            type="primary"
        )
        
        if submitted:
            # Convert date to datetime if provided
            if form_data['dob']:
                form_data['dob'] = datetime.combine(form_data['dob'], datetime.min.time())
            
            # Validate form data
            validation_result = validate_user_profile_data(form_data)
            validation_errors = validation_result.get('errors', [])
            
            # Use enhanced validation feedback
            render_form_validation_feedback(validation_result, "hồ sơ người dùng")
    
    return form_data, validation_errors


def render_citizen_card_form(card_data: Dict[str, Any] = None, form_key: str = "citizen_card_form") -> Tuple[Dict[str, Any], List[str]]:
    """
    Render citizen card information form.
    
    Args:
        card_data: Existing citizen card data for editing
        form_key: Unique key for the form
        
    Returns:
        Tuple of (form_data, validation_errors)
    """
    st.subheader("🆔 Thông tin Căn cước công dân")
    
    form_data = {}
    validation_errors = []
    
    help_texts = {
        "full_name": "Họ và tên đầy đủ trên thẻ",
        "citizen_id": "Số Căn cước công dân 12 chữ số",
        "date_of_birth": "Ngày sinh ghi trên thẻ",
        "place_of_birth": "Nơi sinh",
        "birth_registration_place": "Nơi đăng ký khai sinh",
        "hometown": "Quê quán",
        "permanent_address": "Địa chỉ thường trú",
        "temporary_address": "Địa chỉ tạm trú (nếu có)"
    }
    
    with st.form(key=form_key):
        # Personal Information
        st.markdown("**Thông tin cá nhân**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            form_data['full_name'] = st.text_input(
                "Họ và tên *",
                value=card_data.get('full_name', '') if card_data else '',
                help=help_texts['full_name']
            )
            
            form_data['citizen_id'] = st.text_input(
                "Số CCCD *",
                value=card_data.get('citizen_id', '') if card_data else '',
                help=help_texts['citizen_id']
            )
            
            form_data['date_of_birth'] = st.date_input(
                "Ngày sinh *",
                value=card_data.get('date_of_birth').date() if card_data and card_data.get('date_of_birth') else None,
                help=help_texts['date_of_birth']
            )
        
        with col2:
            form_data['place_of_birth'] = st.text_input(
                "Nơi sinh *",
                value=card_data.get('place_of_birth', '') if card_data else '',
                help=help_texts['place_of_birth']
            )
            
            form_data['birth_registration_place'] = st.text_input(
                "Nơi ĐKKS *",
                value=card_data.get('birth_registration_place', '') if card_data else '',
                help=help_texts['birth_registration_place']
            )
            
            form_data['hometown'] = st.text_input(
                "Quê quán *",
                value=card_data.get('hometown', '') if card_data else '',
                help=help_texts['hometown']
            )
        
        # Additional Information
        st.markdown("**Thông tin bổ sung**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            form_data['ethnicity'] = st.text_input(
                "Dân tộc",
                value=card_data.get('ethnicity', '') if card_data else '',
                placeholder="VD: Kinh, Tày, Thái"
            )
            
            form_data['religion'] = st.text_input(
                "Tôn giáo",
                value=card_data.get('religion', '') if card_data else '',
                placeholder="VD: Phật giáo, Thiên chúa giáo, Không"
            )
            
            form_data['nationality'] = st.text_input(
                "Quốc tịch",
                value=card_data.get('nationality', '') if card_data else 'Việt Nam',
                placeholder="Việt Nam"
            )
        
        with col2:
            form_data['personal_identification'] = st.text_input(
                "Đặc điểm nhận dạng",
                value=card_data.get('personal_identification', '') if card_data else '',
                help="Các đặc điểm nhận dạng nổi bật"
            )
            
            form_data['issue_date'] = st.date_input(
                "Ngày cấp",
                value=card_data.get('issue_date').date() if card_data and card_data.get('issue_date') else None
            )
            
            form_data['expiry_date'] = st.date_input(
                "Ngày hết hạn",
                value=card_data.get('expiry_date').date() if card_data and card_data.get('expiry_date') else None
            )
        
        form_data['issuing_authority'] = st.text_input(
            "Nơi cấp",
            value=card_data.get('issuing_authority', '') if card_data else '',
            placeholder="VD: Cục Cảnh sát QLHC về TTXH"
        )
        
        # Address Information
        st.markdown("**Địa chỉ**")
        
        form_data['permanent_address'] = st.text_area(
            "Địa chỉ thường trú *",
            value=card_data.get('permanent_address', '') if card_data else '',
            help=help_texts['permanent_address']
        )
        
        form_data['temporary_address'] = st.text_area(
            "Địa chỉ tạm trú",
            value=card_data.get('temporary_address', '') if card_data else '',
            help=help_texts['temporary_address']
        )
        
        # Form submission
        submitted = st.form_submit_button(
            "Lưu dự thảo CCCD" if card_data else "Tạo dự thảo CCCD",
            type="primary"
        )
        
        if submitted:
            # Convert dates to datetime if provided
            for date_field in ['date_of_birth', 'issue_date', 'expiry_date']:
                if form_data[date_field]:
                    form_data[date_field] = datetime.combine(form_data[date_field], datetime.min.time())
            
            # Validate form data
            validation_result = validate_citizen_card_data(form_data)
            validation_errors = validation_result.get('errors', [])
            
            # Use enhanced validation feedback
            render_form_validation_feedback(validation_result, "Căn cước công dân")
    
    return form_data, validation_errors


def render_residence_form(residence_data: Dict[str, Any] = None, form_key: str = "residence_form") -> Tuple[Dict[str, Any], List[str]]:
    """
    Render residence information form.
    
    Args:
        residence_data: Existing residence data for editing
        form_key: Unique key for the form
        
    Returns:
        Tuple of (form_data, validation_errors)
    """
    st.subheader("🏠 Thông tin cư trú")
    
    form_data = {}
    validation_errors = []
    
    help_texts = {
        "full_name": "Họ và tên người cư trú",
        "citizen_id": "Số CCCD người cư trú",
        "residence_type": "Loại cư trú (Thường trú, tạm trú, ...)",
        "permanent_address": "Địa chỉ thường trú chính thức",
        "current_address": "Chỗ ở hiện nay",
        "household_id": "Số sổ hộ khẩu (nếu có)",
        "head_of_household": "Tên chủ hộ",
        "relationship_to_head": "Quan hệ với chủ hộ"
    }
    
    with st.form(key=form_key):
        # Basic Information
        st.markdown("**Thông tin cơ bản**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            form_data['full_name'] = st.text_input(
                "Họ và tên *",
                value=residence_data.get('full_name', '') if residence_data else '',
                help=help_texts['full_name']
            )
            
            form_data['citizen_id'] = st.text_input(
                "Số CCCD *",
                value=residence_data.get('citizen_id', '') if residence_data else '',
                help=help_texts['citizen_id']
            )
            
            form_data['residence_type'] = st.selectbox(
                "Loại cư trú",
                options=["", "Thường trú", "Tạm trú", "Ký túc xá", "Công nhân kcn", "Khác"],
                index=0 if not residence_data or not residence_data.get('residence_type') else
                      ["", "Permanent", "Temporary", "Student", "Worker", "Other"].index(residence_data.get('residence_type', '')) if residence_data.get('residence_type') in ["Permanent", "Temporary", "Student", "Worker", "Other"] else 0,
                format_func=lambda x: {"": "Chọn loại", "Thường trú": "Thường trú", "Tạm trú": "Tạm trú", "Ký túc xá": "Ký túc xá", "Công nhân kcn": "Công nhân KCN", "Khác": "Khác", "Permanent": "Thường trú", "Temporary": "Tạm trú", "Student": "Học sinh/SV", "Worker": "Công nhân", "Other": "Khác"}.get(x, x),
                help=help_texts['residence_type']
            )
        
        with col2:
            form_data['household_id'] = st.text_input(
                "Mã hộ gia đình",
                value=residence_data.get('household_id', '') if residence_data else '',
                help=help_texts['household_id']
            )
            
            form_data['head_of_household'] = st.text_input(
                "Chủ hộ",
                value=residence_data.get('head_of_household', '') if residence_data else '',
                help=help_texts['head_of_household']
            )
            
            form_data['relationship_to_head'] = st.selectbox(
                "Quan hệ với chủ hộ",
                options=["", "Chủ hộ", "Vợ/Chồng", "Con", "Cha/Mẹ", "Anh/Chị/Em", "Ông/Bà", "Cháu", "Khác"],
                index=0 if not residence_data or not residence_data.get('relationship_to_head') else
                      ["", "Head", "Spouse", "Child", "Parent", "Sibling", "Grandparent", "Grandchild", "Other"].index(residence_data.get('relationship_to_head', '')) if residence_data.get('relationship_to_head') in ["Head", "Spouse", "Child", "Parent", "Sibling", "Grandparent", "Grandchild", "Other"] else 0,
                format_func=lambda x: {"": "Chọn quan hệ", "Chủ hộ": "Chủ hộ", "Vợ/Chồng": "Vợ/Chồng", "Con": "Con", "Cha/Mẹ": "Cha/Mẹ", "Anh/Chị/Em": "Anh/Chị/Em", "Ông/Bà": "Ông/Bà", "Cháu": "Cháu", "Khác": "Khác", "Head": "Chủ hộ", "Spouse": "Vợ/Chồng", "Child": "Con", "Parent": "Cha/Mẹ", "Sibling": "Anh/Chị/Em", "Grandparent": "Ông/Bà", "Grandchild": "Cháu", "Other": "Khác"}.get(x, x),
                help=help_texts['relationship_to_head']
            )
        
        # Address Information
        st.markdown("**Thông tin địa chỉ**")
        
        form_data['permanent_address'] = st.text_area(
            "Địa chỉ thường trú *",
            value=residence_data.get('permanent_address', '') if residence_data else '',
            help=help_texts['permanent_address']
        )
        
        form_data['current_address'] = st.text_area(
            "Nơi ở hiện nay *",
            value=residence_data.get('current_address', '') if residence_data else '',
            help=help_texts['current_address']
        )
        
        # Form submission
        submitted = st.form_submit_button(
            "Lưu thông tin cư trú" if residence_data else "Tạo thông tin cư trú",
            type="primary"
        )
        
        if submitted:
            # Validate form data
            validation_result = validate_residence_data(form_data)
            validation_errors = validation_result.get('errors', [])
            
            # Use enhanced validation feedback
            render_form_validation_feedback(validation_result, "thông tin cư trú")
    
    return form_data, validation_errors


def render_form_validation_summary(validation_errors: List[str]) -> None:
    """
    Render validation error summary for forms.
    
    Args:
        validation_errors: List of validation error messages
    """
    if validation_errors:
        st.error("**Please fix the following errors:**")
        error_text = format_validation_errors(validation_errors)
        st.markdown(error_text)
    else:
        st.success("✅ All form data is valid!")


def render_form_help_panel() -> None:
    """Render expandable help panel for forms."""
    with st.expander("ℹ️ Form Help & Guidelines"):
        st.markdown("""
        **Required Fields Guidelines:**
        - **Name**: Enter full name as it appears on official documents
        - **Email**: Must be a valid email format (user@domain.com)
        - **Phone**: Vietnamese phone number format preferred
        - **Citizen ID**: Must be exactly 12 digits
        - **Passcode**: 4-6 digit numeric code for user authentication
        
        **Optional Fields:**
        - Leave optional fields empty if information is not available
        - You can always edit this information later
        
        **Data Validation:**
        - All required fields must be filled
        - Email format will be validated
        - Citizen ID must be unique in the system
        - Dates cannot be in the future (for birth dates)
        
        **Tips:**
        - Use the Tab key to navigate between fields quickly
        - Save your work frequently
        - Contact support if you encounter any issues
        """)
def render_household_members_table(
    members_data: List[Dict[str, Any]], 
    residence_uid: str,
    editable: bool = True
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Render household members table with add/edit/delete functionality.
    
    Args:
        members_data: List of household member dictionaries
        residence_uid: UID of the residence document
        editable: Whether to show edit/delete controls
        
    Returns:
        Tuple of (updated_members_data, action_taken)
        action_taken can be: 'add', 'edit', 'delete', 'none'
    """
    st.subheader("👨‍👩‍👧‍👦 Thành viên hộ gia đình")
    
    action_taken = 'none'
    updated_members = members_data.copy()
    
    # Add new member section
    if editable:
        with st.expander("➕ Thêm thành viên mới"):
            member_form_data, member_errors = render_household_member_form(
                member_data=None,
                form_key=f"new_member_{residence_uid}"
            )
            
            if st.button("Thêm thành viên", key=f"add_member_{residence_uid}"):
                if not member_errors:
                    # Generate member ID
                    member_id = f"member_{len(updated_members) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    member_form_data['member_id'] = member_id
                    updated_members.append(member_form_data)
                    action_taken = 'add'
                    show_success_message(f"Đã thêm thành viên: {member_form_data['name']}")
                else:
                    show_error_message("Vui lòng sửa các lỗi trước khi thêm")
    
    # Display existing members
    if updated_members:
        st.markdown(f"**Danh sách thành viên ({len(updated_members)})**")
        
        # Create table data
        table_data = []
        for i, member in enumerate(updated_members):
            table_data.append({
                "Tên": format_name(member.get('name', '')),
                "Quan hệ": "Chủ hộ" if member.get('relationship') == "Head" else 
                           "Vợ/Chồng" if member.get('relationship') == "Spouse" else
                           "Con" if member.get('relationship') == "Child" else
                           "Cha/Mẹ" if member.get('relationship') == "Parent" else
                           "Anh/Chị/Em" if member.get('relationship') == "Sibling" else
                           "Ông/Bà" if member.get('relationship') == "Grandparent" else
                           "Cháu" if member.get('relationship') == "Grandchild" else
                           "Khác" if member.get('relationship') == "Other" else member.get('relationship', ''),
                "CCCD": format_citizen_id(member.get('citizen_id', '')) if member.get('citizen_id') else 'Trống',
                "Ngày sinh": format_date(member.get('dob')) if member.get('dob') else 'Trống',
                "Index": i
            })
        
        # Display table
        if table_data:
            df = pd.DataFrame(table_data)
            
            # Show table without index column for display
            display_df = df.drop('Index', axis=1)
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            if editable:
                # Edit/Delete controls
                st.markdown("**Thao tác**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Select member to edit
                    member_names = [f"{i}: {member['name']}" for i, member in enumerate(updated_members)]
                    selected_member_idx = st.selectbox(
                        "Chọn thành viên để sửa",
                        options=range(len(updated_members)),
                        format_func=lambda x: member_names[x],
                        key=f"edit_select_{residence_uid}"
                    )
                    
                    if st.button("Sửa thành viên đã chọn", key=f"edit_btn_{residence_uid}"):
                        st.session_state[f'editing_member_{residence_uid}'] = selected_member_idx
                
                with col2:
                    # Select member to delete
                    delete_member_idx = st.selectbox(
                        "Chọn thành viên để xóa",
                        options=range(len(updated_members)),
                        format_func=lambda x: member_names[x],
                        key=f"delete_select_{residence_uid}"
                    )
                    
                    if st.button("Xóa thành viên đã chọn", key=f"delete_btn_{residence_uid}", type="secondary"):
                        st.session_state[f'confirm_delete_{residence_uid}'] = delete_member_idx
                
                # Handle member editing
                if f'editing_member_{residence_uid}' in st.session_state:
                    edit_idx = st.session_state[f'editing_member_{residence_uid}']
                    
                    st.markdown("---")
                    st.subheader(f"✏️ Đang sửa: {updated_members[edit_idx]['name']}")
                    
                    edited_data, edit_errors = render_household_member_form(
                        member_data=updated_members[edit_idx],
                        form_key=f"edit_member_{residence_uid}_{edit_idx}"
                    )
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Lưu thay đổi", key=f"save_edit_{residence_uid}"):
                            if not edit_errors:
                                # Keep the original member_id
                                edited_data['member_id'] = updated_members[edit_idx]['member_id']
                                updated_members[edit_idx] = edited_data
                                action_taken = 'edit'
                                del st.session_state[f'editing_member_{residence_uid}']
                                show_success_message(f"Đã cập nhật: {edited_data['name']}")
                                st.rerun()
                            else:
                                show_error_message("Vui lòng sửa lỗi trước khi lưu")
                    
                    with col2:
                        if st.button("Hủy sửa", key=f"cancel_edit_{residence_uid}"):
                            del st.session_state[f'editing_member_{residence_uid}']
                            st.rerun()
                
                # Handle member deletion confirmation
                if f'confirm_delete_{residence_uid}' in st.session_state:
                    delete_idx = st.session_state[f'confirm_delete_{residence_uid}']
                    member_to_delete = updated_members[delete_idx]
                    
                    st.markdown("---")
                    st.error(f"⚠️ **Xác nhận xóa**")
                    st.write(f"Bạn có chắc chắn muốn xóa thành viên **{member_to_delete['name']}** khỏi hộ khẩu?")
                    st.write("Hành động này không thể hoàn tác.")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Có, Xóa thành viên", key=f"confirm_delete_yes_{residence_uid}", type="primary"):
                            deleted_member = updated_members.pop(delete_idx)
                            action_taken = 'delete'
                            del st.session_state[f'confirm_delete_{residence_uid}']
                            show_success_message(f"Đã xóa thành viên: {deleted_member['name']}")
                            st.rerun()
                    
                    with col2:
                        if st.button("Hủy", key=f"confirm_delete_no_{residence_uid}"):
                            del st.session_state[f'confirm_delete_{residence_uid}']
                            st.rerun()
    
    else:
        render_empty_state(
            title="Chưa có thành viên",
            description="Chưa có thành viên nào trong hộ khẩu.",
            action_text="Thêm thành viên đầu tiên" if editable else None,
            action_callback=lambda: st.session_state.update({f'show_add_member_{residence_uid}': True}) if editable else None
        )
    
    return updated_members, action_taken


def render_household_member_form(
    member_data: Dict[str, Any] = None, 
    form_key: str = "household_member_form"
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Render household member form for adding/editing members.
    
    Args:
        member_data: Existing member data for editing
        form_key: Unique key for the form
        
    Returns:
        Tuple of (form_data, validation_errors)
    """
    form_data = {}
    validation_errors = []
    
    help_texts = {
        "name": "Họ và tên thành viên",
        "relationship": "Quan hệ với chủ hộ",
        "citizen_id": "Số CCCD (tùy chọn)",
        "dob": "Ngày sinh"
    }
    
    with st.form(key=form_key):
        col1, col2 = st.columns(2)
        
        with col1:
            form_data['name'] = st.text_input(
                "Họ và tên *",
                value=member_data.get('name', '') if member_data else '',
                placeholder="Nhập họ tên thành viên",
                help=help_texts['name']
            )
            
            form_data['relationship'] = st.selectbox(
                "Quan hệ *",
                options=["", "Chủ hộ", "Vợ/Chồng", "Con", "Cha/Mẹ", "Anh/Chị/Em", "Ông/Bà", "Cháu", "Khác"],
                index=0 if not member_data or not member_data.get('relationship') else
                      ["", "Head", "Spouse", "Child", "Parent", "Sibling", "Grandparent", "Grandchild", "Other"].index(member_data.get('relationship', '')) if member_data.get('relationship') in ["Head", "Spouse", "Child", "Parent", "Sibling", "Grandparent", "Grandchild", "Other"] else 0,
                format_func=lambda x: {"": "Chọn quan hệ", "Chủ hộ": "Chủ hộ", "Vợ/Chồng": "Vợ/Chồng", "Con": "Con", "Cha/Mẹ": "Cha/Mẹ", "Anh/Chị/Em": "Anh/Chị/Em", "Ông/Bà": "Ông/Bà", "Cháu": "Cháu", "Khác": "Khác", "Head": "Chủ hộ", "Spouse": "Vợ/Chồng", "Child": "Con", "Parent": "Cha/Mẹ", "Sibling": "Anh/Chị/Em", "Grandparent": "Ông/Bà", "Grandchild": "Cháu", "Other": "Khác"}.get(x, x),
                help=help_texts['relationship']
            )
        
        with col2:
            form_data['citizen_id'] = st.text_input(
                "Số CCCD",
                value=member_data.get('citizen_id', '') if member_data else '',
                placeholder="123456789012 (nếu có)",
                help=help_texts['citizen_id']
            )
            
            form_data['dob'] = st.date_input(
                "Ngày sinh",
                value=member_data.get('dob').date() if member_data and member_data.get('dob') else None,
                help=help_texts['dob']
            )
        
        # Form submission
        submitted = st.form_submit_button(
            "Lưu thành viên" if member_data else "Thêm thành viên",
            type="primary"
        )
        
        if submitted:
            # Convert date to datetime if provided
            if form_data['dob']:
                form_data['dob'] = datetime.combine(form_data['dob'], datetime.min.time())
            
            # Validate form data
            validation_result = validate_household_member_data(form_data)
            validation_errors = validation_result.get('errors', [])
            
            if validation_errors:
                for error in validation_errors:
                    show_error_message(error)
            else:
                show_success_message("Dữ liệu thành viên hợp lệ!")
    
    return form_data, validation_errors


def render_household_member_summary(members_data: List[Dict[str, Any]]) -> None:
    """
    Render summary of household members.
    
    Args:
        members_data: List of household member dictionaries
    """
    if not members_data:
        st.info("No household members registered")
        return
    
    # Summary statistics
    total_members = len(members_data)
    adults = len([m for m in members_data if m.get('dob') and 
                 (datetime.now() - m['dob']).days >= 18 * 365])
    children = total_members - adults
    
    # Display summary cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Members", total_members)
    
    with col2:
        st.metric("Adults (18+)", adults)
    
    with col3:
        st.metric("Children (<18)", children)
    
    # Relationship breakdown
    relationships = {}
    for member in members_data:
        rel = member.get('relationship', 'Unknown')
        relationships[rel] = relationships.get(rel, 0) + 1
    
    if relationships:
        st.markdown("**Relationship Breakdown:**")
        for relationship, count in relationships.items():
            st.write(f"- {relationship}: {count}")


def render_inline_member_editor(
    member_data: Dict[str, Any],
    member_index: int,
    residence_uid: str
) -> Tuple[Dict[str, Any], bool]:
    """
    Render inline editor for a single household member.
    
    Args:
        member_data: Member data to edit
        member_index: Index of the member in the list
        residence_uid: UID of the residence
        
    Returns:
        Tuple of (updated_member_data, save_clicked)
    """
    updated_data = member_data.copy()
    save_clicked = False
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        updated_data['name'] = st.text_input(
            "Tên",
            value=member_data.get('name', ''),
            key=f"inline_name_{residence_uid}_{member_index}"
        )
    
    with col2:
        updated_data['relationship'] = st.selectbox(
            "Quan hệ",
            options=["", "Chủ hộ", "Vợ/Chồng", "Con", "Cha/Mẹ", "Anh/Chị/Em", "Ông/Bà", "Cháu", "Khác"],
            index=["", "Head", "Spouse", "Child", "Parent", "Sibling", "Grandparent", "Grandchild", "Other"].index(member_data.get('relationship', 'Other')) if member_data.get('relationship') in ["Head", "Spouse", "Child", "Parent", "Sibling", "Grandparent", "Grandchild", "Other"] else 8,
            format_func=lambda x: {"": "Chọn", "Chủ hộ": "Chủ hộ", "Vợ/Chồng": "Vợ/Chồng", "Con": "Con", "Cha/Mẹ": "Cha/Mẹ", "Anh/Chị/Em": "Anh/Chị/Em", "Ông/Bà": "Ông/Bà", "Cháu": "Cháu", "Khác": "Khác", "Head": "Chủ hộ", "Spouse": "Vợ/Chồng", "Child": "Con", "Parent": "Cha/Mẹ", "Sibling": "Anh/Chị/Em", "Grandparent": "Ông/Bà", "Grandchild": "Cháu", "Other": "Khác"}.get(x, x),
            key=f"inline_rel_{residence_uid}_{member_index}"
        )
    
    with col3:
        updated_data['citizen_id'] = st.text_input(
            "Số CCCD",
            value=member_data.get('citizen_id', ''),
            key=f"inline_cid_{residence_uid}_{member_index}"
        )
    
    with col4:
        save_clicked = st.button(
            "💾",
            help="Lưu thay đổi",
            key=f"inline_save_{residence_uid}_{member_index}"
        )
    
    return updated_data, save_clicked
def render_qr_payload_input(
    qr_payload: Optional[str], 
    field_name: str,
    uid: str,
    label: str = None,
    help_text: str = None
) -> str:
    """
    Render QR payload text input field with validation and fallback indication.
    
    Args:
        qr_payload: Current QR payload value
        field_name: Name of the QR field (e.g., 'qr_home', 'qr_card')
        uid: User UID for fallback display
        label: Custom label for the field
        help_text: Custom help text
        
    Returns:
        Updated QR payload value
    """
    if not label:
        label = field_name.replace('qr_', 'QR ').replace('_', ' ').title()
    
    if not help_text:
        help_text = f"Dữ liệu QR tùy chỉnh cho {field_name}. Để trống để dùng UID làm mặc định."
    
    # Display current value or fallback
    current_display = format_qr_payload_display(qr_payload, uid)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        new_payload = st.text_input(
            label,
            value=qr_payload if qr_payload else '',
            placeholder=f"Nhập dữ liệu QR hoặc để trống (mặc định: {uid})",
            help=help_text,
            key=f"qr_input_{field_name}_{uid}"
        )
    
    with col2:
        st.write("**Giá trị hiện tại:**")
        if qr_payload and qr_payload.strip():
            st.success(f"✅ Tùy chỉnh: {qr_payload[:20]}{'...' if len(qr_payload) > 20 else ''}")
        else:
            st.info(f"🔄 Mặc định: {uid}")
    
    return new_payload


def render_qr_payload_section(
    user_data: Dict[str, Any],
    editable: bool = True
) -> Dict[str, str]:
    """
    Render complete QR payload management section.
    
    Args:
        user_data: User data containing QR payloads
        editable: Whether fields should be editable
        
    Returns:
        Dictionary of updated QR payload values
    """
    st.subheader("📱 Dữ liệu mã QR (Payloads)")
    
    uid = user_data.get('uid', '')
    qr_payloads = {}
    
    # QR field definitions
    qr_fields = {
        'qr_home': {
            'label': 'QR Trang chủ',
            'help': 'Dữ liệu cho mã QR hiển thị ở trang chủ'
        },
        'qr_card': {
            'label': 'QR Thẻ căn cước', 
            'help': 'Dữ liệu cho mã QR trên thẻ căn cước'
        },
        'qr_id_detail': {
            'label': 'QR Chi tiết danh tính',
            'help': 'Dữ liệu cho mã QR chi tiết thông tin'
        },
        'qr_residence': {
            'label': 'QR Cư trú',
            'help': 'Dữ liệu cho mã QR thông tin cư trú'
        }
    }
    
    if editable:
        st.markdown("""
        **Thông tin về QR Payload:**
        - QR payload là chuỗi văn bản sẽ được mã hóa vào mã QR trong ứng dụng.
        - Nếu để trống, hệ thống sẽ sử dụng UID của người dùng làm mặc định.
        - Độ dài tối đa: 500 ký tự mỗi payload.
        """)
        
        with st.form(key=f"qr_payloads_{uid}"):
            for field_name, field_config in qr_fields.items():
                current_value = user_data.get(field_name, '')
                
                qr_payloads[field_name] = render_qr_payload_input(
                    qr_payload=current_value,
                    field_name=field_name,
                    uid=uid,
                    label=field_config['label'],
                    help_text=field_config['help']
                )
            
            # Validation and submission
            submitted = st.form_submit_button("Cập nhật QR Payloads", type="primary")
            
            if submitted:
                # Validate all QR payloads
                validation_errors = []
                
                for field_name, payload in qr_payloads.items():
                    from ..utils.validators import validate_qr_payload
                    result = validate_qr_payload(payload)
                    if not result['valid']:
                        validation_errors.append(f"{field_name}: {result['error']}")
                
                if validation_errors:
                    for error in validation_errors:
                        show_error_message(error)
                else:
                    show_success_message("Tất cả QR payloads hợp lệ!")
    
    else:
        # Read-only display
        for field_name, field_config in qr_fields.items():
            current_value = user_data.get(field_name, '')
            display_value = format_qr_payload_display(current_value, uid)
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.write(f"**{field_config['label']}:**")
            
            with col2:
                if current_value and current_value.strip():
                    st.code(current_value, language=None)
                else:
                    st.write(f"*Sử dụng mặc định: {uid}*")
    
    return qr_payloads if editable else {}


def render_qr_payload_preview(qr_payloads: Dict[str, str], uid: str) -> None:
    """
    Render QR payload preview section.
    
    Args:
        qr_payloads: Dictionary of QR payload values
        uid: User UID for fallback
    """
    st.subheader("👁️ Xem trước QR Payload")
    
    # Create tabs for different QR types
    tabs = st.tabs(["QR Trang chủ", "QR Thẻ căn cước", "QR Chi tiết ID", "QR Cư trú"])
    
    qr_fields = ['qr_home', 'qr_card', 'qr_id_detail', 'qr_residence']
    
    for i, (tab, field_name) in enumerate(zip(tabs, qr_fields)):
        with tab:
            payload = qr_payloads.get(field_name, '')
            display_value = format_qr_payload_display(payload, uid)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write("**Nội dung Payload:**")
                if payload and payload.strip():
                    st.code(payload, language=None)
                    st.success("✅ Đang dùng payload tùy chỉnh")
                else:
                    st.code(uid, language=None)
                    st.info("🔄 Đang dùng UID mặc định")
            
            with col2:
                st.write("**Xem trước mã QR:**")
                # Note: In a real implementation, you might generate actual QR codes here
                st.write(f"*Mã QR sẽ chứa: `{display_value}`*")
                
                # Character count
                char_count = len(display_value)
                max_chars = 500
                
                if char_count <= max_chars:
                    st.write(f"📊 Độ dài: {char_count}/{max_chars} ký tự")
                else:
                    st.error(f"⚠️ Quá dài: {char_count}/{max_chars} ký tự")


def render_qr_payload_help() -> None:
    """Render help information for QR payloads."""
    with st.expander("ℹ️ Hướng dẫn về QR Payload"):
        st.markdown("""
        **QR Payload là gì?**
        
        QR payload là chuỗi văn bản tùy chỉnh được mã hóa vào mã QR hiển thị trong ứng dụng di động. 
        Mỗi người dùng có thể có các QR payload khác nhau cho các ngữ cảnh khác nhau:
        
        - **QR Trang chủ**: Hiển thị trên màn hình chính của ứng dụng
        - **QR Thẻ căn cước**: Hiển thị khi xem thẻ căn cước công dân
        - **QR Chi tiết ID**: Sử dụng cho mục đích định danh chi tiết  
        - **QR Cư trú**: Hiển thị cùng thông tin cư trú
        
        **Cơ chế mặc định:**
        
        Nếu QR payload để trống hoặc chưa được thiết lập, hệ thống sẽ tự động sử dụng UID của người dùng làm nội dung mã QR.
        Điều này đảm bảo mọi người dùng luôn có mã QR hoạt động.
        
        **Khuyến nghị:**
        
        - Giữ payload ngắn gọn nhưng đầy đủ ý nghĩa
        - Sử dụng định dạng nhất quán
        - Kiểm tra mã QR bằng thiết bị di động thực tế
        
        **Giới hạn kỹ thuật:**
        
        - Tối đa 500 ký tự mỗi payload
        - Hỗ trợ mã hóa UTF-8
        
        **Lưu ý bảo mật:**
        
        - Không bao gồm thông tin cá nhân nhạy cảm trong QR payload công khai
        - Mã QR có thể được quét bởi người khác
        """)


def render_qr_bulk_operations(user_list: List[Dict[str, Any]]) -> None:
    """
    Render bulk QR payload operations for multiple users.
    
    Args:
        user_list: List of user dictionaries
    """
    st.subheader("🔄 Thao tác QR hàng loạt")
    
    if not user_list:
        st.info("Không có người dùng nào để thực hiện thao tác hàng loạt")
        return
    
    # Bulk operation type
    operation_type = st.selectbox(
        "Chọn thao tác",
        options=[
            "clear_all_payloads",
            "set_default_payloads", 
            "copy_payloads_from_user",
            "reset_to_uid_fallback"
        ],
        format_func=lambda x: {
            "clear_all_payloads": "Xóa tất cả QR Payloads",
            "set_default_payloads": "Đặt QR Payloads mặc định theo mẫu",
            "copy_payloads_from_user": "Sao chép QR Payloads từ người khác",
            "reset_to_uid_fallback": "Reset về mặc định (UID)"
        }[x]
    )
    
    # User selection
    selected_users = st.multiselect(
        "Chọn người dùng áp dụng",
        options=range(len(user_list)),
        format_func=lambda x: f"{user_list[x]['name']} ({user_list[x]['email']})",
        help="Chọn những người dùng sẽ bị ảnh hưởng bởi thao tác này"
    )
    
    if operation_type == "copy_payloads_from_user":
        source_user_idx = st.selectbox(
            "Sao chép từ người dùng",
            options=range(len(user_list)),
            format_func=lambda x: f"{user_list[x]['name']} ({user_list[x]['email']})"
        )
        
        if source_user_idx is not None:
            source_user = user_list[source_user_idx]
            st.write("**QR Payloads nguồn:**")
            
            for field in ['qr_home', 'qr_card', 'qr_id_detail', 'qr_residence']:
                value = source_user.get(field, '')
                display_value = format_qr_payload_display(value, source_user.get('uid', ''))
                st.write(f"- {field}: `{display_value}`")
    
    elif operation_type == "set_default_payloads":
        st.write("**Mẫu QR Payload mặc định:**")
        st.caption("Sử dụng {uid} để chèn UID của người dùng vào mẫu.")
        
        default_templates = {
            'qr_home': st.text_input("QR Trang chủ mặc định", placeholder="VD: HOME_{uid}"),
            'qr_card': st.text_input("QR Căn cước mặc định", placeholder="VD: CARD_{uid}"),
            'qr_id_detail': st.text_input("QR Chi tiết ID mặc định", placeholder="VD: ID_{uid}"),
            'qr_residence': st.text_input("QR Cư trú mặc định", placeholder="VD: RES_{uid}")
        }
    
    # Confirmation and execution
    if selected_users:
        st.write(f"**Thao tác sẽ ảnh hưởng đến {len(selected_users)} người dùng:**")
        for idx in selected_users:
            st.write(f"- {user_list[idx]['name']} ({user_list[idx]['email']})")
        
        if st.button("Thực thi thao tác", type="primary"):
            st.success(f"Thao tác hàng loạt '{operation_type}' sẽ được thực thi cho {len(selected_users)} người dùng")
            # Note: Actual implementation would call the UserManager bulk operation methods
    else:
        st.info("Vui lòng chọn người dùng để thực hiện thao tác")


def validate_qr_payload_batch(qr_payloads: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Validate multiple QR payloads at once.
    
    Args:
        qr_payloads: Dictionary of field_name -> payload mappings
        
    Returns:
        Tuple of (all_valid, error_messages)
    """
    from ..utils.validators import validate_qr_payload
    
    errors = []
    
    for field_name, payload in qr_payloads.items():
        result = validate_qr_payload(payload)
        if not result['valid']:
            errors.append(f"{field_name}: {result['error']}")
    
    return len(errors) == 0, errors

# ===== STYLED COMPONENT FUNCTIONS =====

def render_styled_card(title: str, content: str, icon: str = None, card_type: str = "default") -> None:
    """
    Render a styled card component with consistent design.
    
    Args:
        title: Card title
        content: Card content (can be HTML)
        icon: Optional icon for the card
        card_type: Type of card (default, primary, success, warning, error)
    """
    card_classes = {
        "default": "dashboard-card",
        "primary": "dashboard-card bg-primary text-white",
        "success": "dashboard-card border-success",
        "warning": "dashboard-card border-warning", 
        "error": "dashboard-card border-error"
    }
    
    card_class = card_classes.get(card_type, "dashboard-card")
    title_with_icon = f"{icon} {title}" if icon else title
    
    st.markdown(f"""
    <div class="{card_class}">
        <h4 class="mb-3">{title_with_icon}</h4>
        <div>{content}</div>
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, delta: str = None, delta_color: str = "normal") -> None:
    """
    Render a metric card with value and optional delta.
    
    Args:
        label: Metric label
        value: Metric value
        delta: Optional delta value
        delta_color: Color for delta (normal, success, warning, error)
    """
    delta_class = f"text-{delta_color}" if delta_color != "normal" else ""
    delta_html = f'<div class="mt-1 {delta_class}"><small>{delta}</small></div>' if delta else ""
    
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_status_badge(status: str, text: str = None) -> None:
    """
    Render a status badge with appropriate styling.
    
    Args:
        status: Status type (success, warning, error, info)
        text: Optional custom text (defaults to status)
    """
    display_text = text or status.title()
    
    st.markdown(f"""
    <span class="status-badge {status}">{display_text}</span>
    """, unsafe_allow_html=True)


def render_action_button_group(buttons: List[Dict[str, Any]]) -> None:
    """
    Render a group of action buttons with consistent styling.
    
    Args:
        buttons: List of button configs with keys: label, key, type, icon, callback
    """
    st.markdown('<div class="action-buttons">', unsafe_allow_html=True)
    
    cols = st.columns(len(buttons))
    
    for i, button_config in enumerate(buttons):
        with cols[i]:
            label = button_config.get('label', 'Button')
            key = button_config.get('key', f'btn_{i}')
            btn_type = button_config.get('type', 'secondary')
            icon = button_config.get('icon', '')
            callback = button_config.get('callback')
            
            button_label = f"{icon} {label}" if icon else label
            
            if st.button(button_label, key=key, type=btn_type):
                if callback:
                    callback()
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_data_grid(title: str, data: pd.DataFrame, actions: List[Dict[str, Any]] = None) -> None:
    """
    Render a styled data grid with optional actions.
    
    Args:
        title: Grid title
        data: DataFrame to display
        actions: Optional list of action buttons
    """
    st.markdown(f"""
    <div class="data-grid-container">
        <div class="data-grid-header">
            <span>{title}</span>
            <span>{len(data)} records</span>
        </div>
        <div class="data-grid-content">
    """, unsafe_allow_html=True)
    
    if not data.empty:
        st.dataframe(data, use_container_width=True)
        
        if actions:
            st.markdown("---")
            render_action_button_group(actions)
    else:
        render_empty_state(
            title="No Data Available",
            description="There are no records to display.",
            icon="📊"
        )
    
    st.markdown('</div></div>', unsafe_allow_html=True)


def render_styled_empty_state(title: str, description: str, icon: str = "📭", 
                             action_label: str = None, action_callback = None) -> None:
    """
    Render a styled empty state with optional action.
    
    Args:
        title: Empty state title
        description: Empty state description
        icon: Icon to display
        action_label: Optional action button label
        action_callback: Optional action button callback
    """
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-description">{description}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if action_label and action_callback:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(action_label, type="primary"):
                action_callback()


def render_styled_breadcrumb(pages: List[Tuple[str, str]]) -> None:
    """
    Render styled breadcrumb navigation.
    
    Args:
        pages: List of (page_name, page_url) tuples
    """
    breadcrumb_items = []
    
    for i, (page_name, page_url) in enumerate(pages):
        if i > 0:
            breadcrumb_items.append('<span class="breadcrumb-separator">›</span>')
        
        if page_url:
            breadcrumb_items.append(f'<a href="{page_url}" class="breadcrumb-item">{page_name}</a>')
        else:
            breadcrumb_items.append(f'<span class="breadcrumb-item">{page_name}</span>')
    
    st.markdown(f"""
    <nav class="breadcrumb">
        {''.join(breadcrumb_items)}
    </nav>
    """, unsafe_allow_html=True)


def render_loading_overlay(message: str = "Đang tải...", show_spinner: bool = True) -> None:
    """
    Render a loading overlay with message.
    
    Args:
        message: Loading message
        show_spinner: Whether to show spinner
    """
    if show_spinner:
        with st.spinner(message):
            st.empty()
    else:
        st.info(f"⏳ {message}")


def render_form_section(title: str, content_func, icon: str = None, 
                       collapsible: bool = False, expanded: bool = True) -> None:
    """
    Render a styled form section with optional collapsible behavior.
    
    Args:
        title: Section title
        content_func: Function that renders the section content
        icon: Optional icon
        collapsible: Whether section is collapsible
        expanded: Whether section is expanded by default (if collapsible)
    """
    section_title = f"{icon} {title}" if icon else title
    
    if collapsible:
        with st.expander(section_title, expanded=expanded):
            content_func()
    else:
        st.subheader(section_title)
        content_func()


def apply_responsive_columns(num_columns: int, mobile_stack: bool = True) -> List:
    """
    Create responsive columns that stack on mobile if specified.
    
    Args:
        num_columns: Number of columns for desktop
        mobile_stack: Whether to stack columns on mobile
        
    Returns:
        List of column objects
    """
    # For now, just return regular columns
    # In a real implementation, you might use CSS media queries
    # or JavaScript to handle responsive behavior
    return st.columns(num_columns)


def render_responsive_table(data: pd.DataFrame, mobile_columns: List[str] = None) -> None:
    """
    Render a table that adapts to mobile screens.
    
    Args:
        data: DataFrame to display
        mobile_columns: Columns to show on mobile (if None, shows all)
    """
    # For mobile responsiveness, we could implement column hiding
    # or horizontal scrolling based on screen size
    
    if mobile_columns and len(data.columns) > 4:
        # Show a simplified view for mobile
        with st.expander("📱 Chế độ xem di động (Rút gọn)"):
            mobile_data = data[mobile_columns] if mobile_columns else data.iloc[:, :3]
            st.dataframe(mobile_data, use_container_width=True)
        
        # Show full view for desktop
        with st.expander("🖥️ Chế độ xem máy tính (Đầy đủ)", expanded=True):
            st.dataframe(data, use_container_width=True)
    else:
        st.dataframe(data, use_container_width=True)


def render_theme_toggle() -> None:
    """
    Render a theme toggle button (placeholder for future implementation).
    """
    # This would require JavaScript integration for theme switching
    # For now, just show a placeholder
    if st.button("🌓 Đổi giao diện"):
        st.info("Tính năng đổi giao diện sẽ có trong bản cập nhật tới!")


def get_responsive_grid_config(total_items: int) -> Dict[str, int]:
    """
    Get responsive grid configuration based on number of items.
    
    Args:
        total_items: Total number of items to display
        
    Returns:
        Dictionary with grid configuration
    """
    if total_items <= 2:
        return {"desktop": total_items, "tablet": total_items, "mobile": 1}
    elif total_items <= 4:
        return {"desktop": 2, "tablet": 2, "mobile": 1}
    else:
        return {"desktop": 3, "tablet": 2, "mobile": 1}