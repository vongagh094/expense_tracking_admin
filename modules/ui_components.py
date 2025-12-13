"""
Reusable UI Components for Firebase Admin Dashboard

This module provides reusable Streamlit components for consistent UI across the dashboard.
Includes search filters, data tables, forms, and other interactive elements.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
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
    """
    st.subheader("🔍 Tìm kiếm")
    
    # Simplified search interface
    search_term = st.text_input(
        "Tìm kiếm người dùng",
        placeholder="Nhập tên hoặc số CCCD...",
        help="Hệ thống sẽ tự động tìm theo CCCD (nếu nhập số) hoặc Tên (nếu nhập chữ)"
    )
    
    return {
        "search_term": search_term.strip() if search_term else ""
    }


def render_user_table(users_data: List[Dict[str, Any]], page_size: int = 20) -> Optional[str]:
    """
    Render paginated user table.
    
    Args:
        users_data: List of user dictionaries
        page_size: Number of users per page
        
    Returns:
        Selected user UID if a row is clicked, None otherwise
    """
    if not users_data:
        st.info("Không tìm thấy người dùng nào khớp với bộ lọc.")
        return None
    
    # Show count only
    st.write(f"**Tìm thấy {len(users_data)} người dùng**")
    
    # No sorting UI anymore, assuming data comes sorted or we just show as is
    
    # Pagination
    total_pages = math.ceil(len(users_data) / page_size)
    
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
    page_users = users_data[start_idx:end_idx]
    
    # Create table data
    table_data = []
    for user in page_users:
        table_data.append({
            "Họ và Tên": format_name(user.get('name', '')),
            "Số CCCD": format_citizen_id(user.get('citizen_id', '')),
            "Ngày sinh": user.get('dob', '--'),
            "Email": user.get('email', ''),
            "SĐT": format_phone_number(user.get('phone', '')),
            "Ngày tạo": format_date(user.get('created_at')) if user.get('created_at') else '',
            "UID": user.get('uid', '') # Hidden or used for selection
        })
    
    # Display table
    if table_data:
        df = pd.DataFrame(table_data)
        
        # Configure column config for better display
        column_config = {
            "UID": None, # Hide UID column
        }
        
        # Use st.dataframe (view only, outdated streamlit doesn't support on_select)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config=column_config
        )
        
        return None
    
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
    from utils.error_handler import feedback_manager
    
    if validation_result.get('valid', False):
        feedback_manager.show_success(f"Dữ liệu {form_name} hợp lệ! ✅")
        return True
    else:
        errors = validation_result.get('errors', [])
        if errors:
            feedback_manager.show_validation_errors(
                errors, 
                f"Vui lòng sửa các lỗi sau trong {form_name}:"
            )
        else:
            feedback_manager.show_error(f"Xác thực thất bại cho {form_name}")
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

import io
import base64
from PIL import Image

def process_avatar_image(uploaded_file) -> str:
    """
    Process uploaded avatar: Resize -> Compress -> Base64.
    Returns: Base64 string prefix with data URI.
    """
    try:
        image = Image.open(uploaded_file)
        # Convert to RGB if RGBA (transparency not supported in JPEG)
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
            
        # Resize to max 400x400
        image.thumbnail((400, 400))
        
        # Save to buffer
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=70)
        
        # Encode
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/jpeg;base64,{img_str}"
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return ""

def render_user_form(user_data: Dict[str, Any] = None, form_key: str = "user_form") -> Tuple[Dict[str, Any], List[str], bool]:
    """
    Render comprehensive user profile form.
    """
    st.subheader("👤 Thông tin hồ sơ (User Profile)")
    
    form_data = {}
    validation_errors = []
    
    # Initialize help texts...
    help_texts = {
        "full_name": "Họ và tên đầy đủ (Viết hoa)",
        "email": "Địa chỉ Email liên hệ",
        "phone_number": "Số điện thoại chính",
        "citizen_id": "Số CCCD (Identity Number)",
        "passcode": "Mã bảo mật ứng dụng (4-6 số)",
        "identity_level": "Mức độ định danh (1 hoặc 2)",
        "date_of_birth": "Ngày sinh (DD/MM/YYYY)",
        "permanent_address": "Địa chỉ thường trú theo giấy tờ",
        "current_address": "Nơi ở hiện tại",
    }
    
    with st.form(key=form_key):
        # 1. Core Identity
        st.markdown("**1. Thông tin định danh**")
        col1, col2 = st.columns(2)
        
        with col1:
            form_data['full_name'] = st.text_input(
                "Họ và tên *",
                value=user_data.get('full_name', user_data.get('name', '')) if user_data else '',
                help=help_texts['full_name']
            )
            form_data['citizen_id'] = st.text_input(
                "Số CCCD *",
                value=user_data.get('citizen_id', '') if user_data else '',
                help=help_texts['citizen_id']
            )
            form_data['date_of_birth'] = st.text_input(
                "Ngày sinh (DD/MM/YYYY) *",
                value=user_data.get('date_of_birth', user_data.get('dob', '')) if user_data else '',
                placeholder="20/10/1990",
                help=help_texts['date_of_birth']
            )
            form_data['gender'] = st.selectbox(
                "Giới tính *",
                options=["Nam", "Nữ"],
                index=["Nam", "Nữ"].index(user_data.get('gender', 'Nam')) if user_data and user_data.get('gender') in ["Nam", "Nữ"] else 0
            )

        with col2:
            form_data['phone_number'] = st.text_input(
                "Số điện thoại *",
                value=user_data.get('phone_number', user_data.get('phone', '')) if user_data else '',
                help=help_texts['phone_number']
            )
            form_data['email'] = st.text_input(
                "Email",
                value=user_data.get('email', '') if user_data else '',
                help=help_texts['email']
            )
            form_data['nationality'] = st.text_input(
                "Quốc tịch",
                value=user_data.get('nationality', 'Việt Nam') if user_data else 'Việt Nam'
            )
            form_data['identity_level'] = st.number_input(
                "Mức độ định danh *",
                min_value=1, max_value=2,
                value=int(user_data.get('identity_level', 2)) if user_data else 2,
                help=help_texts['identity_level']
            )

        # 2. Address Information
        st.markdown("---")
        st.markdown("**2. Thông tin địa chỉ**")
        
        form_data['permanent_address'] = st.text_area(
            "Địa chỉ thường trú *",
            value=user_data.get('permanent_address', user_data.get('address', '')) if user_data else '',
            help=help_texts['permanent_address']
        )
        form_data['current_address'] = st.text_area(
            "Nơi ở hiện tại *",
            value=user_data.get('current_address', user_data.get('address', '')) if user_data else '',
            help=help_texts['current_address']
        )
        form_data['temporary_address'] = st.text_area(
            "Địa chỉ tạm trú (Nếu có)",
            value=user_data.get('temporary_address', '') if user_data else ''
        )

        # 3. Assets & Security
        st.markdown("---")
        st.markdown("**3. Ảnh đại diện & Bảo mật**")
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            st.markdown("Avatar (Ảnh đại diện)")
            # Existing Avatar
            existing_avatar = user_data.get('avatar_asset', '') if user_data else ''
            
            # File Uploader
            uploaded_file = st.file_uploader("Upload ảnh (sẽ thay thế ảnh cũ)", type=['png', 'jpg', 'jpeg'])
            
            if uploaded_file:
                # Process new file
                processed_b64 = process_avatar_image(uploaded_file)
                if processed_b64:
                    form_data['avatar_asset'] = processed_b64
                    st.success("Ảnh đã được xử lý!")
                    st.image(uploaded_file, caption="Ảnh mới tải lên", width=150)
                else:
                     # Fallback to existing
                    form_data['avatar_asset'] = existing_avatar
            else:
                 # Keep existing
                form_data['avatar_asset'] = existing_avatar
                if existing_avatar and existing_avatar.startswith("data:"):
                     st.image(existing_avatar, caption="Ảnh hiện tại", width=150)
                elif existing_avatar:
                     st.text(f"Path/Url hiện tại: {existing_avatar}")

        with col_s2:
            form_data['passcode'] = st.text_input(
                "Passcode (App) *",
                value=user_data.get('passcode', '') if user_data else '',
                help=help_texts['passcode']
            )

        # 4. QR Codes
        st.markdown("---")
        st.markdown("**4. Dữ liệu QR Code**")
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            form_data['qr_home'] = st.text_input("QR Trang chủ", value=user_data.get('qr_home', '') if user_data else '')
            form_data['qr_card'] = st.text_input("QR Thẻ CCCD", value=user_data.get('qr_card', '') if user_data else '')
        with col_q2:
            form_data['qr_id_detail'] = st.text_input("QR Thẻ căn cước", value=user_data.get('qr_id_detail', '') if user_data else '')
            form_data['qr_residence'] = st.text_input("QR Trang thông tin cư trú", value=user_data.get('qr_residence', '') if user_data else '')

        # Submission
        submitted = st.form_submit_button(
            "Lưu thông tin hồ sơ" if user_data else "Tạo hồ sơ người dùng",
            type="primary"
        )
        
        if submitted:
            # Validate form data
            validation_result = validate_user_profile_data(form_data)
            validation_errors = validation_result.get('errors', [])
            render_form_validation_feedback(validation_result, "hồ sơ người dùng")
            
    return form_data, validation_errors, submitted


def render_citizen_card_form(card_data: Dict[str, Any] = None, 
                             linked_profile_data: Dict[str, Any] = None,
                             form_key: str = "citizen_card_form") -> Tuple[Dict[str, Any], List[str], bool]:
    """
    Render citizen card information form matching 'Citizen Card Data Guide'.
    
    Args:
        card_data: Existing citizen card data
        linked_profile_data: Optional profile data to sync/lock shared fields
        form_key: Unique key for the form
        
    Returns:
        Tuple of (form_data, validation_errors, submitted)
    """
    st.subheader("🆔 Thông tin Căn cước công dân (Citizen Card)")
    
    form_data = {}
    validation_errors = []
    
    # Helper to resolve value and lock state
    def get_field_config(field_name: str, profile_key: str = None) -> Tuple[Any, bool]:
        p_key = profile_key or field_name
        if linked_profile_data and linked_profile_data.get(p_key):
            return linked_profile_data.get(p_key), True
        return card_data.get(field_name, '') if card_data else '', False

    help_texts = {
        "citizen_id": "Số Căn cước công dân (12 số) [Đồng bộ]",
        "date_of_birth": "Ngày sinh (DD/MM/YYYY) [Đồng bộ]",
        "birthplace": "Nơi sinh (Theo giấy khai sinh)",
        "birth_registration_place": "Nơi đăng ký khai sinh",
        "hometown": "Quê quán",
        "permanent_address": "Địa chỉ thường trú [Đồng bộ]",
        "permanent_address_2": "Địa chỉ thường trú (Dòng 2 - Tùy chọn)",
        "identifying_marks": "Đặc điểm nhận dạng (VD: Nốt ruồi...)",
        "issue_date": "Ngày cấp (DD/MM/YYYY)",
        "issue_place": "Nơi cấp (VD: Cục Cảnh sát QLHC về TTXH)"
    }
    
    with st.form(key=form_key):
        # 1. Main Information
        st.markdown("**1. Thông tin chính**")
        col1, col2 = st.columns(2)
        
        with col1:
            val, dis = get_field_config('full_name')
            form_data['full_name'] = st.text_input(
                "Họ và tên *",
                value=val,
                disabled=dis
            )
            
            val, dis = get_field_config('citizen_id')
            form_data['citizen_id'] = st.text_input(
                "Số CCCD *",
                value=val,
                disabled=dis,
                help=help_texts['citizen_id']
            )
            
            val, dis = get_field_config('date_of_birth')
            form_data['date_of_birth'] = st.text_input(
                "Ngày sinh (DD/MM/YYYY) *",
                value=val,
                disabled=dis,
                placeholder="20/10/1990",
                help=help_texts['date_of_birth']
            )
            
            val, dis = get_field_config('gender')
            # Selectbox handling
            opts = ["Nam", "Nữ"]
            idx = 0
            if val in opts:
                idx = opts.index(val)
            elif card_data and card_data.get('gender') in opts:
                idx = opts.index(card_data.get('gender'))
                
            form_data['gender'] = st.selectbox(
                "Giới tính *",
                options=opts,
                index=idx,
                disabled=dis
            )
            
            val, dis = get_field_config('nationality')
            form_data['nationality'] = st.text_input(
                "Quốc tịch *",
                value=val or 'Việt Nam',
                disabled=dis
            )

        with col2:
            form_data['birthplace'] = st.text_area(
                "Nơi sinh *",
                value=card_data.get('birthplace', card_data.get('place_of_birth', '')) if card_data else '',
                help=help_texts['birthplace'],
                height=100
            )
            form_data['birth_registration_place'] = st.text_area(
                "Nơi ĐKKS *",
                value=card_data.get('birth_registration_place', '') if card_data else '',
                help=help_texts['birth_registration_place'],
                height=100
            )
            form_data['hometown'] = st.text_area(
                "Quê quán *",
                value=card_data.get('hometown', '') if card_data else '',
                help=help_texts['hometown'],
                height=100
            )

        # 2. Address & Location
        st.markdown("---")
        st.markdown("**2. Địa chỉ & Cư trú**")
        
        val, dis = get_field_config('permanent_address')
        form_data['permanent_address'] = st.text_area(
            "Địa chỉ thường trú *",
            value=val,
            disabled=dis,
            help=help_texts['permanent_address']
        )
        form_data['permanent_address_2'] = st.text_input(
            "Địa chỉ thường trú (Dòng 2)",
            value=card_data.get('permanent_address_2', '') if card_data else '',
            placeholder="Thôn/Xóm/Tổ dân phố...",
            help=help_texts['permanent_address_2']
        )
        
        col_addr1, col_addr2 = st.columns(2)
        with col_addr1:
            # Check profile for current_address
            val, dis = get_field_config('current_address')
            form_data['current_address'] = st.text_area(
                "Nơi ở hiện tại *",
                value=val,
                disabled=dis
            )
        with col_addr2:
            # Check profile for temporary_address
            val, dis = get_field_config('temporary_address')
            form_data['temporary_address'] = st.text_area(
                "Địa chỉ tạm trú",
                value=val,
                disabled=dis
            )

        # 3. Additional Details
        st.markdown("---")
        st.markdown("**3. Thông tin bổ sung**")
        
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            form_data['ethnicity'] = st.selectbox(
                "Dân tộc", 
                options=["Kinh", "Hoa", "Tày", "Thái", "Mường", "Khmer", "Nùng", "Ba Na", "Dao", "Gia Rai", "Ê Đê", "Sán Chay", "Chăm", "Cơ Ho", "Khác"],
                index=["Kinh", "Hoa", "Tày", "Thái", "Mường", "Khmer", "Nùng", "Ba Na", "Dao", "Gia Rai", "Ê Đê", "Sán Chay", "Chăm", "Cơ Ho", "Khác"].index(card_data.get('ethnicity', 'Kinh')) if card_data and card_data.get('ethnicity') in ["Kinh", "Hoa", "Tày", "Thái", "Mường", "Khmer", "Nùng", "Ba Na", "Dao", "Gia Rai", "Ê Đê", "Sán Chay", "Chăm", "Cơ Ho", "Khác"] else 0
            )
            form_data['religion'] = st.text_input("Tôn giáo", value=card_data.get('religion', '') if card_data else '')
            form_data['blood_type'] = st.text_input("Nhóm máu", value=card_data.get('blood_type', '') if card_data else '')
            
        with col_ex2:
            form_data['profession'] = st.text_input("Nghề nghiệp", value=card_data.get('profession', '') if card_data else '')
            form_data['other_info'] = st.text_input("Ghi chú / Khác", value=card_data.get('other_info', '') if card_data else '')

        # 4. Identification & Issue
        st.markdown("---")
        st.markdown("**4. Đặc điểm nhận dạng & Cấp phát**")
        
        form_data['identifying_marks'] = st.text_area(
            "Đặc điểm nhận dạng *",
            value=card_data.get('identifying_marks', card_data.get('personal_identification', '')) if card_data else '',
            help=help_texts['identifying_marks']
        )
        
        col_iss1, col_iss2 = st.columns(2)
        with col_iss1:
            form_data['issue_date'] = st.text_input(
                "Ngày cấp (DD/MM/YYYY) *",
                value=card_data.get('issue_date', '') if card_data else '',
                placeholder="10/10/2021",
                help=help_texts['issue_date']
            )
        with col_iss2:
            form_data['issue_place'] = st.text_input(
                "Nơi cấp *",
                value=card_data.get('issue_place', card_data.get('issuing_authority', '')) if card_data else '',
                help=help_texts['issue_place']
            )
            
        # QR Code Data
        st.markdown("---")
        form_data['qr_code_data'] = st.text_area(
            "Qr code thẻ",
            value=card_data.get('qr_code_data', card_data.get('qr_payload', '')) if card_data else '',
            height=100
        )
        
        # Submission
        submitted = st.form_submit_button(
            "Lưu thông tin CCCD" if card_data else "Tạo thẻ CCCD",
            type="primary"
        )
        
        if submitted:
             # Inject locked fields back into form_data to ensure they are saved
            if linked_profile_data:
                replacements = {
                    'full_name': 'full_name',
                    'citizen_id': 'citizen_id',
                    'date_of_birth': 'date_of_birth',
                    'gender': 'gender',
                    'nationality': 'nationality',
                    'permanent_address': 'permanent_address',
                    'current_address': 'current_address',
                    'temporary_address': 'temporary_address'
                }
                for form_key, profile_key in replacements.items():
                    val = linked_profile_data.get(profile_key)
                    if val: # Ensure we don't overwrite with empty if profile is empty but form has data?
                        # No, if profile is empty, we didn't lock it (checked in get_field_config).
                        # But get_field_config checks (linked_profile_data and get(p_key)).
                        # So here we should also check if it was actually locked.
                        # Safe enough to assign what's in profile if present.
                        form_data[form_key] = val
            
            # Map legacy field for validaton compatibility
            form_data['place_of_birth'] = form_data.get('birthplace', '')

            # Validate form data
            validation_result = validate_citizen_card_data(form_data)
            validation_errors = validation_result.get('errors', [])
            render_form_validation_feedback(validation_result, "thẻ CCCD")
            
    return form_data, validation_errors, submitted


def render_residence_form(residence_data: Dict[str, Any] = None, 
                          linked_profile_data: Dict[str, Any] = None,
                          form_key: str = "residence_form") -> Tuple[Dict[str, Any], List[str], bool]:
    """
    Render residence information form - aligned with Resident Information Data Guide.
    
    Args:
        residence_data: Existing residence data for editing
        linked_profile_data: Optional profile data to sync/lock shared fields
        form_key: Unique key for the form
        
    Returns:
        Tuple of (form_data, validation_errors, submitted)
    """
    st.subheader("🏠 Thông tin cư trú")
    
    form_data = {}
    validation_errors = []
    
    # Helper to resolve value and lock state with key mapping
    def get_field_config(field_name: str, profile_key: str = None) -> Tuple[Any, bool]:
        p_key = profile_key or field_name
        if linked_profile_data and linked_profile_data.get(p_key):
            return linked_profile_data.get(p_key), True
        return residence_data.get(field_name, '') if residence_data else '', False

    help_texts = {
        "full_name": "Họ và tên đầy đủ [Đồng bộ]",
        "id_number": "Số Citizen ID (CCCD) [Đồng bộ]",
        "birth_date": "Ngày sinh (DD/MM/YYYY) [Đồng bộ]",
        "gender": "Giới tính",
        "permanent_address": "Địa chỉ thường trú chính thức [Đồng bộ]",
        "current_address": "Nơi ở hiện tại [Đồng bộ]",
        "household_head_name": "Tên chủ hộ",
        "household_head_id": "Số CCCD chủ hộ",
        "relation_to_head": "Quan hệ với chủ hộ"
    }
    
    with st.form(key=form_key):
        # 1. Personal Information
        st.markdown("**1. Thông tin cá nhân**")
        col1, col2 = st.columns(2)
        
        with col1:
            val, dis = get_field_config('full_name')
            form_data['full_name'] = st.text_input(
                "Họ và tên *",
                value=val,
                disabled=dis,
                help=help_texts['full_name']
            )
            
            val, dis = get_field_config('birth_date', 'date_of_birth')
            form_data['birth_date'] = st.text_input(
                "Ngày sinh (DD/MM/YYYY) *",
                value=val,
                disabled=dis,
                placeholder="20/10/1990",
                help=help_texts['birth_date']
            )
            
            form_data['ethnicity'] = st.selectbox(
                "Dân tộc",
                options=["Kinh", "Hoa", "Tày", "Thái", "Mường", "Khmer", "Nùng", "Ba Na", "Dao", "Gia Rai", "Ê Đê", "Sán Chay", "Chăm", "Cơ Ho", "Khác"],
                index=["Kinh", "Hoa", "Tày", "Thái", "Mường", "Khmer", "Nùng", "Ba Na", "Dao", "Gia Rai", "Ê Đê", "Sán Chay", "Chăm", "Cơ Ho", "Khác"].index(residence_data.get('ethnicity', 'Kinh')) if residence_data and residence_data.get('ethnicity') in ["Kinh", "Hoa", "Tày", "Thái", "Mường", "Khmer", "Nùng", "Ba Na", "Dao", "Gia Rai", "Ê Đê", "Sán Chay", "Chăm", "Cơ Ho", "Khác"] else 0
            )
            form_data['religion'] = st.text_input(
                "Tôn giáo",
                value=residence_data.get('religion', '') if residence_data else 'Không'
            )
            
        with col2:
            val, dis = get_field_config('id_number', 'citizen_id')
            form_data['id_number'] = st.text_input(
                "Số CCCD *",
                value=val,
                disabled=dis,
                help=help_texts['id_number']
            )
            
            val, dis = get_field_config('gender')
            # Selectbox handling
            opts = ["Nam", "Nữ"]
            idx = 0
            if val in opts:
                idx = opts.index(val)
            elif residence_data and residence_data.get('gender') in opts:
                idx = opts.index(residence_data.get('gender'))
                
            form_data['gender'] = st.selectbox(
                "Giới tính *",
                options=opts,
                index=idx,
                disabled=dis
            )
            
            val, dis = get_field_config('nationality')
            form_data['nationality'] = st.text_input(
                "Quốc tịch",
                value=val or 'Việt Nam',
                disabled=dis
            )
            
            form_data['hometown'] = st.text_input(
                "Quê quán",
                value=residence_data.get('hometown', '') if residence_data else ''
            )

        form_data['citizen_status'] = st.selectbox(
            "Tình trạng cư trú",
            options=["Thường trú", "Tạm trú", "Khác"],
            index=["Thường trú", "Tạm trú", "Khác"].index(residence_data.get('citizen_status', 'Thường trú')) if residence_data and residence_data.get('citizen_status') in ["Thường trú", "Tạm trú", "Khác"] else 0
        )

        st.markdown("---")
        
        # 2. Address Information
        st.markdown("**2. Thông tin địa chỉ**")
        
        val, dis = get_field_config('permanent_address')
        form_data['permanent_address'] = st.text_area(
            "Địa chỉ thường trú *",
            value=val,
            disabled=dis,
            help=help_texts['permanent_address']
        )
        
        val, dis = get_field_config('current_address')
        form_data['current_address'] = st.text_area(
            "Nơi ở hiện nay *",
            value=val,
            disabled=dis,
            help=help_texts['current_address']
        )
        
        with st.expander("Thông tin tạm trú (Nếu có)"):
            val, dis = get_field_config('temporary_address')
            form_data['temporary_address'] = st.text_area(
                 "Địa chỉ tạm trú",
                 value=val,
                 disabled=dis
            )
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                form_data['temporary_start'] = st.text_input(
                    "Từ ngày (DD/MM/YYYY)",
                    value=residence_data.get('temporary_start', '') if residence_data else ''
                )
            with t_col2:
                form_data['temporary_end'] = st.text_input(
                    "Đến ngày (DD/MM/YYYY)",
                    value=residence_data.get('temporary_end', '') if residence_data else ''
                )

        st.markdown("---")

        # 3. Household Head Information
        st.markdown("**3. Thông tin chủ hộ**")
        
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            form_data['household_head_name'] = st.text_input(
                "Tên chủ hộ *",
                value=residence_data.get('household_head_name', residence_data.get('head_of_household', '')) if residence_data else '',
                help=help_texts['household_head_name']
            )
            form_data['relation_to_head'] = st.selectbox(
                "Quan hệ với chủ hộ *",
                options=["Chủ hộ", "Vợ", "Chồng", "Con", "Cha", "Mẹ", "Ông", "Bà", "Cháu", "Khác"],
                index=["Chủ hộ", "Vợ", "Chồng", "Con", "Cha", "Mẹ", "Ông", "Bà", "Cháu", "Khác"].index(residence_data.get('relation_to_head', residence_data.get('relationship_to_head', 'Chủ hộ'))) if residence_data and residence_data.get('relation_to_head') in ["Chủ hộ", "Vợ", "Chồng", "Con", "Cha", "Mẹ", "Ông", "Bà", "Cháu", "Khác"] else 0
            )

        with col_h2:
            form_data['household_head_id'] = st.text_input(
                "Số CCCD chủ hộ *",
                value=residence_data.get('household_head_id', '') if residence_data else '',
                help=help_texts['household_head_id']
            )
        
        # Form submission
        submitted = st.form_submit_button(
            "Lưu thông tin cư trú" if residence_data else "Tạo thông tin cư trú",
            type="primary"
        )
        
        if submitted:
             # Inject locked fields back into form_data to ensure they are saved
            if linked_profile_data:
                # Format: form_key: profile_key
                replacements = {
                    'full_name': 'full_name',
                    'id_number': 'citizen_id',       # Key mapping
                    'birth_date': 'date_of_birth',   # Key mapping
                    'gender': 'gender',
                    'nationality': 'nationality',
                    'permanent_address': 'permanent_address',
                    'current_address': 'current_address',
                    'temporary_address': 'temporary_address'
                }
                for form_key, profile_key in replacements.items():
                    val = linked_profile_data.get(profile_key)
                    if val:
                        form_data[form_key] = val

            # Validate form data
            validation_result = validate_residence_data(form_data)
            validation_errors = validation_result.get('errors', [])
            
            # Use enhanced validation feedback
            render_form_validation_feedback(validation_result, "thông tin cư trú")
    
    return form_data, validation_errors, submitted


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
    editable: bool = True,
    on_save: Optional[Callable[[List[Dict[str, Any]]], None]] = None
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Render household members table with add/edit/delete functionality.
    
    Args:
        members_data: List of household member dictionaries
        residence_uid: UID of the residence document
        editable: Whether to show edit/delete controls
        on_save: Callback function to save changes (receives updated members list)
        
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
            member_form_data, member_errors, member_submitted = render_household_member_form(
                member_data=None,
                form_key=f"new_member_{residence_uid}"
            )
            
            if st.session_state.get(f'new_member_submitted_{residence_uid}', False):
                if not member_errors:
                    # Generate member ID
                    member_id = f"member_{len(updated_members) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    member_form_data['member_id'] = member_id
                    updated_members.append(member_form_data)
                    action_taken = 'add'
                    if on_save:
                        on_save(updated_members)
                    show_success_message(f"Đã thêm thành viên: {member_form_data.get('full_name') or member_form_data.get('name', 'Unknown')}")
                    # Clear submission state to prevent re-add on reload
                    st.session_state[f'new_member_submitted_{residence_uid}'] = False
                    st.rerun()
                else:
                    show_error_message("Vui lòng sửa các lỗi trước khi thêm")
                    st.session_state[f'new_member_submitted_{residence_uid}'] = False
    
    # Display existing members
    if updated_members:
        st.markdown(f"**Danh sách thành viên ({len(updated_members)})**")
        
        # Create table data
        table_data = []
        for i, member in enumerate(updated_members):
            table_data.append({
                "Tên": format_name(member.get('full_name') or member.get('name', '')),
                "Quan hệ": {
                    "Head": "Chủ hộ", "Spouse": "Vợ/Chồng", "Child": "Con", 
                    "Parent": "Cha/Mẹ", "Sibling": "Anh/Chị/Em", 
                    "Grandparent": "Ông/Bà", "Grandchild": "Cháu", "Other": "Khác"
                }.get(member.get('relation_to_head') or member.get('relationship'), member.get('relation_to_head') or member.get('relationship', '')),
                "CCCD": member.get('id_number') or (format_citizen_id(member.get('citizen_id', '')) if member.get('citizen_id') else 'Trống'),
                "Ngày sinh": member.get('birth_date') or (format_date(member.get('dob')) if member.get('dob') else 'Trống'),
                "Giới tính": member.get('gender', ''),
                "Tình trạng": member.get('citizen_status', ''),
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
                    member_names = [f"{i}: {member.get('full_name') or member.get('name', 'Unknown')}" for i, member in enumerate(updated_members)]
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
                    st.subheader(f"✏️ Đang sửa: {updated_members[edit_idx].get('full_name') or updated_members[edit_idx].get('name', 'Unknown')}")
                    
                    edited_data, edit_errors, edit_submitted = render_household_member_form(
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
                                if on_save:
                                    on_save(updated_members)
                                show_success_message(f"Đã cập nhật: {edited_data.get('full_name') or edited_data.get('name', 'Unknown')}")
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
                    st.write(f"Bạn có chắc chắn muốn xóa thành viên **{member_to_delete.get('full_name') or member_to_delete.get('name', 'Unknown')}** khỏi hộ khẩu?")
                    st.write("Hành động này không thể hoàn tác.")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Có, Xóa thành viên", key=f"confirm_delete_yes_{residence_uid}", type="primary"):
                            deleted_member = updated_members.pop(delete_idx)
                            action_taken = 'delete'
                            del st.session_state[f'confirm_delete_{residence_uid}']
                            if on_save:
                                on_save(updated_members)
                            show_success_message(f"Đã xóa thành viên: {deleted_member.get('full_name') or deleted_member.get('name', 'Unknown')}")
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
) -> Tuple[Dict[str, Any], List[str], bool]:
    """Render household member form."""
    form_data = {}
    validation_errors = []
    
    help_texts = {
        "full_name": "Họ và tên thành viên",
        "relation_to_head": "Quan hệ với chủ hộ",
        "id_number": "Số Citizen ID (CCCD)",
        "birth_date": "Ngày sinh (DD/MM/YYYY)",
        "gender": "Giới tính",
        "citizen_status": "Tình trạng cư trú"
    }
    
    with st.form(key=form_key):
        col1, col2 = st.columns(2)
        
        with col1:
            form_data['full_name'] = st.text_input(
                "Họ và tên *",
                value=member_data.get('full_name', member_data.get('name', '')) if member_data else '',
                help=help_texts['full_name']
            )
            
            form_data['relation_to_head'] = st.selectbox(
                "Quan hệ *",
                options=["", "Vợ", "Chồng", "Con", "Cha", "Mẹ", "Ông", "Bà", "Cháu", "Khác"],
                index=0 if not member_data or not member_data.get('relation_to_head', member_data.get('relationship', '')) else
                      ["", "Spouse", "Child", "Parent", "Grandparent", "Grandchild", "Other", "Vợ", "Chồng", "Con", "Cha", "Mẹ", "Ông", "Bà", "Cháu", "Khác"].index(member_data.get('relation_to_head', member_data.get('relationship', ''))) if member_data.get('relation_to_head', member_data.get('relationship')) in ["Spouse", "Child", "Parent", "Grandparent", "Grandchild", "Other", "Vợ", "Chồng", "Con", "Cha", "Mẹ", "Ông", "Bà", "Cháu", "Khác"] else 0,
                format_func=lambda x: {"": "Chọn quan hệ", "Vợ": "Vợ", "Chồng": "Chồng", "Con": "Con", "Cha": "Cha", "Mẹ": "Mẹ", "Ông": "Ông", "Bà": "Bà", "Cháu": "Cháu", "Khác": "Khác", "Spouse": "Vợ/Chồng", "Child": "Con", "Parent": "Cha/Mẹ", "Grandparent": "Ông/Bà", "Grandchild": "Cháu", "Other": "Khác"}.get(x, x)
            )

            form_data['gender'] = st.selectbox(
                "Giới tính *",
                options=["Nam", "Nữ"],
                index=["Nam", "Nữ"].index(member_data.get('gender', 'Nam')) if member_data and member_data.get('gender') in ["Nam", "Nữ"] else 0
            )
        
        with col2:
            form_data['id_number'] = st.text_input(
                "Số CCCD *",
                value=member_data.get('id_number', member_data.get('citizen_id', '')) if member_data else '',
                help=help_texts['id_number']
            )
            
            form_data['birth_date'] = st.text_input(
                "Ngày sinh (DD/MM/YYYY) *",
                value=member_data.get('birth_date', member_data.get('dob', '')) if member_data else '',
                placeholder="01/01/2000",
                help=help_texts['birth_date']
            )

            form_data['citizen_status'] = st.selectbox(
                "Tình trạng",
                options=["Thường trú", "Tạm trú", "Khác"],
                index=["Thường trú", "Tạm trú", "Khác"].index(member_data.get('citizen_status', 'Thường trú')) if member_data and member_data.get('citizen_status') in ["Thường trú", "Tạm trú", "Khác"] else 0
            )
        
        # Form submission
        submitted = st.form_submit_button(
            "Lưu thành viên" if member_data else "Thêm thành viên",
            type="primary"
        )
        
        if submitted:
            # Validate form data
            validation_result = validate_household_member_data(form_data)
            validation_errors = validation_result.get('errors', [])
            
            if validation_errors:
                for error in validation_errors:
                    show_error_message(error)
            else:
                show_success_message("Dữ liệu thành viên hợp lệ!")
                # Mark as submitted in session state for parent component
                # We extract the residence_uid from form_key if possible, or just use form_key
                st.session_state[f'{form_key}_submitted'] = True
                
                # Check if this is the new member form to set the specific flag expected by parent
                if "new_member_" in form_key:
                     # form_key is like "new_member_{residence_uid}"
                     st.session_state[f'{form_key}_submitted'.replace('_form', '')] = True # This might depend on how parent constructs key
                     # Actually, parent uses: f"new_member_{residence_uid}" as form_key
                     # Parent expects: f'new_member_submitted_{residence_uid}'
                     # Let's align keys: form_key is "new_member_UID". we set "new_member_submitted_UID"
                     uid_part = form_key.replace("new_member_", "")
                     st.session_state[f'new_member_submitted_{uid_part}'] = True

    return form_data, validation_errors, submitted


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