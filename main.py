"""
Firebase Admin Dashboard - Main Application Entry Point
"""

import streamlit as st
import sys
import os
from datetime import datetime
import traceback

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import authentication functions (Auth is bypassed)
from modules.auth import (
    require_authentication,
    get_current_admin,
    is_authenticated,
    display_auth_status
)

# Import user management and UI components
from modules.user_management import UserManager
from modules.ui_components import (
    render_user_search_filters,
    render_user_table,
    show_success_message,
    show_error_message,
    show_info_message,
    render_breadcrumb,
    render_section_header,
    render_data_summary_cards,
    render_empty_state,
    render_operation_feedback,
    render_enhanced_loading_indicator,
    render_user_form,
    render_citizen_card_form,
    render_residence_form,
    render_household_members_table
)

# Import enhanced error handling (package-safe)
try:
    from firebase_admin_dashboard.utils.error_handler import (
        error_handler,
        ErrorType,
        LoadingManager,
        safe_execute,
    )
except ImportError:
    from utils.error_handler import (
        error_handler,
        ErrorType,
        LoadingManager,
        safe_execute,
    )

# Import Firebase configuration (package-safe)
try:
    from firebase_admin_dashboard.config.firebase_config import get_db
except ImportError:
    from config.firebase_config import get_db


# Backward-compatible alias expected by several call sites
def get_firestore_client():
    return get_db()


def load_custom_css():
    """Load custom CSS styles for the dashboard."""
    css_path = os.path.join(os.path.dirname(__file__), 'styles', 'custom.css')
    
    try:
        # Basic styling if file not found or empty
        st.markdown("""
        <style>
        .stButton button {
            width: 100%;
            border-radius: 8px;
            font-weight: 600;
        }
        .main .block-container {
            padding-top: 2rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        if os.path.exists(css_path):
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
            st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
        
        # Add Google Fonts for better typography
        st.markdown("""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        """, unsafe_allow_html=True)
        
    except Exception as e:
        pass


def initialize_session_state():
    """Initialize session state variables for the application."""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    if 'selected_user_uid' not in st.session_state:
        st.session_state.selected_user_uid = None
    if 'page_view' not in st.session_state:
        st.session_state.page_view = 'user_list'
    # Initialize form data containers if not present
    if 'user_profile_data' not in st.session_state:
        st.session_state.user_profile_data = {}
    if 'citizen_card_data' not in st.session_state:
        st.session_state.citizen_card_data = {}
    if 'residence_data' not in st.session_state:
        st.session_state.residence_data = {}


def render_navigation_sidebar():
    """Render the navigation sidebar with menu options."""
    with st.sidebar:
        st.header("🧭 Điều hướng")
        
        # Main navigation menu
        page_options = {
            'user_list': '👥 Danh sách người dùng',
            'create_user': '➕ Tạo người dùng mới',
            'audit_logs': '📋 Nhật ký hoạt động'
        }
        
        sorted_keys = ['user_list', 'create_user'] # Hidden audit logs for simplicity or add back if needed
        
        # Don't show sidebar navigation when editing/viewing user detail
        if st.session_state.page_view in ['edit_user', 'user_detail']:
            st.info("Đang xem/chỉnh sửa người dùng")
            if st.button("← Về danh sách", key="sidebar_back"):
                st.session_state.page_view = 'user_list'
                st.session_state.selected_user_uid = None
                st.rerun()
        else:
            selected_page = st.selectbox(
                "Chọn trang:",
                options=sorted_keys,
                format_func=lambda x: page_options[x],
                index=sorted_keys.index(st.session_state.page_view) if st.session_state.page_view in sorted_keys else 0
            )
            
            if selected_page != st.session_state.page_view:
                st.session_state.page_view = selected_page
                st.session_state.selected_user_uid = None  # Clear user selection when changing pages
                st.rerun()
        
        # Quick actions
        st.markdown("---")
        st.subheader("⚡ Thao tác nhanh")
        
        if st.button("🔄 Làm mới dữ liệu"):
            # Clear any cached data
            st.cache_data.clear()
            show_success_message("Dữ liệu đã được làm mới!")
            st.rerun()
        
        if st.button("➕ Người dùng mới"):
            st.session_state.page_view = 'create_user'
            st.rerun()
        
        # System info
        st.markdown("---")
        st.caption(f"Cập nhật lần cuối: {datetime.now().strftime('%H:%M:%S')}")


def render_user_list_page():
    """Render the main user list page with search and navigation."""
    try:
        # Page header
        st.title("👥 Quản lý người dùng")
        st.markdown("Xem và quản lý tất cả người dùng trong hệ thống")
        st.markdown("---")
        
        # Initialize Firebase connection
        db = get_firestore_client()
        user_manager = UserManager(db)
        
        # Render search and filter controls
        search_params = render_user_search_filters()
        
        # Prepare search parameters for UserManager
        search_term = search_params.get('search_term', '')
        
        # Smart Search Logic
        search_field = 'all'
        if search_term:
            if search_term.isdigit():
                search_field = 'citizen_id'
            else:
                search_field = 'name'
        
        # no date filter anymore
        date_filter = {}
        
        # Get users from database
        def load_users():
            users, total_count = user_manager.get_all_users(
                search_term=search_term if search_term else None,
                date_filter=None,
                limit=100,  # Adjust as needed
                offset=0,
                search_field=search_field
            )
            
            # Convert UserProfile objects to dictionaries for the table
            users_data = []
            for user in users:
                # Safely format datetime fields
                created = user.created_at
                updated = user.updated_at
                if hasattr(created, 'strftime'):
                    created = created.strftime('%Y-%m-%d %H:%M')
                elif created:
                    created = str(created)[:16]
                
                if hasattr(updated, 'strftime'):
                    updated = updated.strftime('%Y-%m-%d %H:%M')
                elif updated:
                    updated = str(updated)[:16]
                
                # Fetch DOB from profile, maybe need more robust way if deep nested
                dob = '--'
                if hasattr(user, 'dob') and user.dob:
                    if hasattr(user.dob, 'strftime'):
                        dob = user.dob.strftime('%d/%m/%Y')
                    else:
                        dob = str(user.dob)[:10]

                user_dict = {
                    'uid': user.uid,
                    'name': user.name,
                    'email': user.email,
                    'citizen_id': user.citizen_id,
                    'phone': user.phone,
                    'dob': dob,
                    'created_at': created or '--',
                    'updated_at': updated or '--'
                }
                users_data.append(user_dict)
            
            return users_data, total_count
        
        with LoadingManager.loading_spinner("Đang tải danh sách người dùng..."):
            result = safe_execute(
                load_users,
                error_handler,
                ErrorType.DATABASE,
                "Không thể tải danh sách người dùng. Vui lòng kiểm tra kết nối.",
                show_details=True,
                default_return=([], 0)
            )
            
            if result:
                users_data, total_count = result
                
                # Render user table
                if len(users_data) > 0:
                    # Dropdown to select user for editing
                    st.markdown("### 📝 Chọn người dùng để chỉnh sửa")
                    user_options = {f"{u.get('name', 'N/A')} - {u.get('citizen_id', 'NoID')}": u.get('uid') for u in users_data}
                    
                    col_select, col_btn = st.columns([3, 1])
                    with col_select:
                        selected_display = st.selectbox(
                            "Chọn người dùng:",
                            options=list(user_options.keys()),
                            key="user_select_dropdown",
                            label_visibility="collapsed"
                        )
                    with col_btn:
                        if st.button("✏️ Chỉnh sửa", type="primary", use_container_width=True):
                            if selected_display:
                                st.session_state.selected_user_uid = user_options[selected_display]
                                st.session_state.page_view = 'edit_user'
                                st.rerun()
                    
                    st.markdown("---")
                    
                    # Also show the table for reference
                    selected_user_uid = render_user_table(users_data, page_size=20)
                    
                    # Handle user selection from table click
                    if selected_user_uid:
                        st.session_state.selected_user_uid = selected_user_uid
                        st.session_state.page_view = 'edit_user' # Direct to edit page as requested (Requirement 5)
                        st.rerun()
                elif total_count > 0 and len(users_data) == 0:
                    st.warning("Có dữ liệu người dùng nhưng không thể hiển thị. Có thể do lỗi định dạng dữ liệu.")
                else:
                    # Show empty state
                    if search_term:
                        render_empty_state(
                            "Không tìm thấy người dùng",
                            f"Không có kết quả nào cho '{search_term}'.",
                            "Thử lại",
                            lambda: st.rerun()
                        )
                    else:
                        render_empty_state(
                            "Chưa có người dùng",
                            "Hệ thống chưa có dữ liệu người dùng nào.",
                            "Tạo người dùng đầu tiên",
                            lambda: setattr(st.session_state, 'page_view', 'create_user')
                        )
    
    except Exception as e:
        show_error_message(f"Lỗi khi khởi tạo trang danh sách: {str(e)}")


def render_user_detail_page():
    """Render comprehensive user detail page with edit functionality."""
    if not st.session_state.selected_user_uid:
        st.session_state.page_view = 'user_list'
        st.rerun()
        return
    
    uid = st.session_state.selected_user_uid
    
    try:
        # Initialize Firebase connection
        db = get_firestore_client()
        user_manager = UserManager(db)
        
        # Load user data
        def load_user_data():
            return user_manager.get_user_by_id(uid)
        
        with LoadingManager.loading_spinner("Đang tải thông tin chi tiết..."):
            user_data = safe_execute(
                load_user_data,
                error_handler,
                ErrorType.DATABASE,
                f"Không thể tải thông tin cho ID {uid}",
                show_details=True,
                default_return=None
            )
            
            if not user_data:
                st.error(f"Không tìm thấy người dùng: {uid}")
                if st.button("← Quay lại danh sách"):
                    st.session_state.page_view = 'user_list'
                    st.session_state.selected_user_uid = None
                    st.rerun()
                return
        
        # Breadcrumb navigation
        user_name = "Người dùng"
        profile = user_data.get('profile')
        if profile and hasattr(profile, 'full_name'):
            user_name = profile.full_name or user_name
        
        render_breadcrumb([
            ("Danh sách", None),
            (f"{user_name}", None)
        ])
        
        # Page header with action buttons
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.title(f"👤 {user_name}")
            st.caption(f"ID: {uid}")
        
        with col2:
            if st.button("← Quay lại"):
                st.session_state.page_view = 'user_list'
                st.session_state.selected_user_uid = None
                st.rerun()
        
        st.markdown("---")
        
        # Use tabs for clean organization
        tabs = st.tabs(["📋 Thông tin chung", "🆔 CCCD", "🏠 Cư trú", "✏️ Chỉnh sửa"])
        
        with tabs[0]:
            render_user_view_profile(user_data)
        
        with tabs[1]:
            render_user_view_citizen_card(user_data)
        
        with tabs[2]:
            render_user_view_residence(user_data)
            
        with tabs[3]:
            render_user_edit_forms(uid, user_data, user_manager)
            
    except Exception as e:
        show_error_message(f"Lỗi hiển thị chi tiết: {str(e)}")


def render_user_edit_forms(uid: str, user_data: dict, user_manager):
    """Render edit forms for user data."""
    st.subheader("✏️ Chỉnh sửa thông tin")
    
    edit_section = st.selectbox(
        "Chọn phần cần chỉnh sửa",
        ["Hồ sơ cá nhân", "Thẻ CCCD", "Thông tin cư trú"]
    )
    
    if edit_section == "Hồ sơ cá nhân":
        render_profile_edit_form(uid, user_data, user_manager)
    elif edit_section == "Thẻ CCCD":
        render_citizen_card_edit_form(uid, user_data, user_manager)
    else:
        render_residence_edit_form(uid, user_data, user_manager)


def render_profile_edit_form(uid: str, user_data: dict, user_manager):
    """Render profile edit form."""
    profile = user_data.get('profile')
    if not profile:
        st.warning("Không có dữ liệu hồ sơ")
        return
    
    p = {}
    if hasattr(profile, 'full_name'):
        p = {
            'full_name': profile.full_name,
            'email': profile.email,
            'phone_number': profile.phone_number,
            'citizen_id': profile.citizen_id,
            'gender': profile.gender or '',
            'dob': profile.dob or '',
            'address': profile.address or '',
            'passcode': profile.passcode or '789789',
        }
    
    with st.form("edit_profile_form"):
        full_name = st.text_input("Họ và tên", value=p.get('full_name', ''))
        email = st.text_input("Email", value=p.get('email', ''))
        phone_number = st.text_input("Số điện thoại", value=p.get('phone_number', ''))
        gender = st.selectbox("Giới tính", ["Nam", "Nữ"], index=0)
        dob = st.text_input("Ngày sinh (dd/mm/yyyy)", value=p.get('dob', ''))
        address = st.text_input("Địa chỉ", value=p.get('address', ''))
        passcode = st.text_input("Mật mã (6 số)", value=p.get('passcode', '789789'))
        
        submitted = st.form_submit_button("💾 Lưu thay đổi", type="primary")
        
        if submitted:
            update_data = {
                'full_name': full_name,
                'email': email,
                'phone_number': phone_number,
                'gender': gender,
                'dob': dob,
                'address': address,
                'passcode': passcode or '789789',
                'updated_at': datetime.now(),
            }
            try:
                user_manager.update_user_profile(uid, update_data)
                show_success_message("Cập nhật hồ sơ thành công!")
                st.rerun()
            except Exception as e:
                show_error_message(f"Lỗi: {str(e)}")


def render_citizen_card_edit_form(uid: str, user_data: dict, user_manager):
    """Render citizen card edit form."""
    card = user_data.get('citizen_card')
    
    c = {}
    if card and hasattr(card, 'full_name'):
        c = {
            'full_name': card.full_name,
            'citizen_id': card.citizen_id,
            'date_of_birth': card.date_of_birth or '',
            'nationality': card.nationality or 'Việt Nam',
            'hometown': card.hometown or '',
            'permanent_address': card.permanent_address or '',
            'ethnicity': card.ethnicity or 'Kinh',
            'religion': card.religion or 'Không',
            'issue_date': card.issue_date or '',
            'issue_place': card.issue_place or '',
        }
    
    with st.form("edit_citizen_card_form"):
        full_name = st.text_input("Họ và tên", value=c.get('full_name', ''))
        citizen_id = st.text_input("Số CCCD", value=c.get('citizen_id', uid))
        date_of_birth = st.text_input("Ngày sinh", value=c.get('date_of_birth', ''))
        nationality = st.text_input("Quốc tịch", value=c.get('nationality', 'Việt Nam'))
        hometown = st.text_input("Quê quán", value=c.get('hometown', ''))
        permanent_address = st.text_area("Địa chỉ thường trú", value=c.get('permanent_address', ''))
        ethnicity = st.text_input("Dân tộc", value=c.get('ethnicity', 'Kinh'))
        religion = st.text_input("Tôn giáo", value=c.get('religion', 'Không'))
        issue_date = st.text_input("Ngày cấp", value=c.get('issue_date', ''))
        issue_place = st.text_input("Nơi cấp", value=c.get('issue_place', ''))
        
        submitted = st.form_submit_button("💾 Lưu thay đổi", type="primary")
        
        if submitted:
            update_data = {
                'full_name': full_name,
                'citizen_id': citizen_id,
                'date_of_birth': date_of_birth,
                'nationality': nationality,
                'hometown': hometown,
                'permanent_address': permanent_address,
                'ethnicity': ethnicity,
                'religion': religion,
                'issue_date': issue_date,
                'issue_place': issue_place,
                'updated_at': datetime.now(),
            }
            try:
                user_manager.update_citizen_card(uid, update_data)
                show_success_message("Cập nhật CCCD thành công!")
                st.rerun()
            except Exception as e:
                show_error_message(f"Lỗi: {str(e)}")


def render_residence_edit_form(uid: str, user_data: dict, user_manager):
    """Render residence edit form."""
    res = user_data.get('residence')
    
    r = {}
    if res and hasattr(res, 'full_name'):
        r = {
            'full_name': res.full_name,
            'permanent_address': res.permanent_address,
            'current_address': res.current_address,
            'household_id': res.household_id or '',
            'head_of_household': res.head_of_household or '',
            'relationship_to_head': res.relationship_to_head or '',
        }
    
    with st.form("edit_residence_form"):
        full_name = st.text_input("Họ và tên", value=r.get('full_name', ''))
        permanent_address = st.text_area("Địa chỉ thường trú", value=r.get('permanent_address', ''))
        current_address = st.text_area("Nơi ở hiện tại", value=r.get('current_address', ''))
        household_id = st.text_input("Mã hộ khẩu", value=r.get('household_id', ''))
        head_of_household = st.text_input("Chủ hộ", value=r.get('head_of_household', ''))
        relationship_to_head = st.text_input("Quan hệ với chủ hộ", value=r.get('relationship_to_head', ''))
        
        submitted = st.form_submit_button("💾 Lưu thay đổi", type="primary")
        
        if submitted:
            update_data = {
                'full_name': full_name,
                'citizen_id': uid,
                'permanent_address': permanent_address,
                'current_address': current_address,
                'household_id': household_id,
                'head_of_household': head_of_household,
                'relationship_to_head': relationship_to_head,
                'updated_at': datetime.now(),
            }
            try:
                user_manager.update_residence(uid, update_data)
                show_success_message("Cập nhật thông tin cư trú thành công!")
                st.rerun()
            except Exception as e:
                show_error_message(f"Lỗi: {str(e)}")


def get_attr(obj, key, default='--'):
    """Helper to get attribute from object or dict."""
    if hasattr(obj, key):
        val = getattr(obj, key)
        return val if val else default
    if isinstance(obj, dict):
        return obj.get(key, default) or default
    return default


def render_user_view_profile(user_data: dict):
    """Render user profile view tab."""
    profile = user_data.get('profile')
    if not profile:
        st.info("Chưa có thông tin hồ sơ")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Thông tin cá nhân")
        st.write(f"**Họ và tên:** {get_attr(profile, 'full_name')}")
        st.write(f"**Email:** {get_attr(profile, 'email')}")
        st.write(f"**SĐT:** {get_attr(profile, 'phone_number')}")
        st.write(f"**CCCD:** {get_attr(profile, 'citizen_id')}")
        st.write(f"**Địa chỉ:** {get_attr(profile, 'address')}")
    
    with col2:
        st.markdown("### Thông tin khác")
        st.write(f"**Ngày sinh:** {get_attr(profile, 'dob')}")
        st.write(f"**Giới tính:** {get_attr(profile, 'gender')}")
        st.write(f"**Quốc tịch:** {get_attr(profile, 'nationality')}")


def render_user_view_citizen_card(user_data: dict):
    """Render citizen card view tab."""
    card = user_data.get('citizen_card')
    if not card:
        st.info("Chưa có thông tin CCCD")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Số CCCD:** {get_attr(card, 'citizen_id')}")
        st.write(f"**Họ và tên:** {get_attr(card, 'full_name')}")
        st.write(f"**Ngày sinh:** {get_attr(card, 'date_of_birth')}")
        st.write(f"**Quê quán:** {get_attr(card, 'hometown')}")
    
    with col2:
        st.write(f"**Quốc tịch:** {get_attr(card, 'nationality')}")
        st.write(f"**Ngày cấp:** {get_attr(card, 'issue_date')}")
        st.write(f"**Nơi thường trú:** {get_attr(card, 'permanent_address')}")


def render_user_view_residence(user_data: dict):
    """Render residence view tab."""
    res = user_data.get('residence')
    if not res:
        st.info("Chưa có thông tin cư trú")
        return
    
    st.write(f"**Thường trú:** {get_attr(res, 'permanent_address')}")
    st.write(f"**Nơi ở hiện tại:** {get_attr(res, 'current_address')}")
    st.write(f"**Chủ hộ:** {get_attr(res, 'head_of_household')}")


def render_edit_user_page():
    """Render edit user page with tabs for Profile, CCCD, and Residence."""
    uid = st.session_state.get('selected_user_uid')
    if not uid:
        st.session_state.page_view = 'user_list'
        st.rerun()
        return
    
    st.title("✏️ Chỉnh sửa người dùng")
    
    if st.button("← Quay lại danh sách"):
        st.session_state.page_view = 'user_list'
        st.session_state.selected_user_uid = None
        st.rerun()
    
    st.markdown("---")
    
    # Load user data
    try:
        db = get_firestore_client()
        user_manager = UserManager(db)
        user_data = user_manager.get_user_by_id(uid)
        
        if not user_data:
            show_error_message(f"Không tìm thấy người dùng: {uid}")
            return
    except Exception as e:
        show_error_message(f"Lỗi tải dữ liệu: {str(e)}")
        return
    
    # Extract data from user_data
    profile = user_data.get('profile')
    card = user_data.get('citizen_card')
    residence = user_data.get('residence')
    
    # Get user name for display
    user_name = "Người dùng"
    if profile and hasattr(profile, 'full_name'):
        user_name = profile.full_name or user_name
    
    st.info(f"Đang chỉnh sửa: **{user_name}** (ID: {uid})")
    
    # Pre-load profile data for syncing across tabs
    p = {}
    if profile:
        p = profile.to_dict()
    profile_data = p

    tabs = st.tabs(["🔵 1. Thông tin Profile", "⚪ 2. Thẻ CCCD", "⚪ 3. Thông tin Cư trú"])
    
    # Tab 1: Profile
    with tabs[0]:
        st.header("Thông tin hồ sơ")
        
        # Use reusable component
        updated_profile_data, profile_errors, submitted = render_user_form(
            user_data=profile_data,
            form_key="edit_profile_form"
        )
        
        if submitted and not profile_errors:
            # Prepare update data mapping (some fields might need specific handling or are direct)
            # The form_data keys match the schema/legacy mix we support in UserManager
            
            # Add updated timestamp
            updated_profile_data['updated_at'] = datetime.now()
            
            # Additional logic: Ensure ID match if provided (though form handles it)
            if updated_profile_data.get('citizen_id') != p.get('citizen_id'):
                # Handle ID change warning or logic (usually careful with this)
                pass # UserManager handles consistency checks if implemented
            
            try:
                user_manager.update_user_profile(uid, updated_profile_data)
                show_success_message("✅ Đã cập nhật thông tin Profile!")
                st.rerun()
            except Exception as e:
                show_error_message(f"Lỗi cập nhật: {str(e)}")
    
    # Tab 2: Citizen Card
    with tabs[1]:
        st.header("Thông tin Căn cước công dân")
        
        # Pre-load card data
        c = {}
        if card:
             c = card.to_dict()
        else:
             c = {}
        
        updated_card_data, card_errors, submitted_card = render_citizen_card_form(
            card_data=c,
            linked_profile_data=profile_data,
            form_key="edit_card_form"
        )
        
        if submitted_card and not card_errors:
            # Prepare update data
            update_data = updated_card_data.copy()
            update_data['updated_at'] = datetime.now()
            
            try:
                user_manager.update_citizen_card(uid, update_data)
                show_success_message("✅ Đã cập nhật thông tin CCCD!")
                st.rerun()
            except Exception as e:
                show_error_message(f"Lỗi: {str(e)}")
    
    # Tab 3: Residence
    with tabs[2]:
        st.header("Thông tin Cư trú")
        
        # Prepare residence data
        r_data = {}
        household_members_data = []
        
        if residence:
            r_data = residence.to_dict()
            # If to_dict doesn't include members, getting them from object
            if hasattr(residence, 'household_members') and residence.household_members:
                household_members_data = [m.to_dict() for m in residence.household_members]

        # 1. Residence Main Form
        form_data, errors, submitted = render_residence_form(
            residence_data=r_data if residence else None,
            linked_profile_data=profile_data,
            form_key="residence_form"
        )
        
        if submitted and not errors:
            try:
                # Ensure UID match
                form_data['uid'] = uid
                user_manager.update_residence(uid, form_data)
                show_success_message("✅ Đã cập nhật thông tin cư trú!")
                st.rerun()
            except Exception as e:
                show_error_message(f"Lỗi cập nhật cư trú: {str(e)}")

        st.markdown("---")
        
        # 2. Household Members Table
        def save_members(new_members):
            try:
                user_manager.update_household_members_collection(uid, new_members)
            except Exception as e:
                show_error_message(f"Lỗi cập nhật thành viên: {str(e)}")
                raise e

        render_household_members_table(household_members_data, uid, on_save=save_members)


def render_create_user_page():
    """
    Render progressive user creation workflow.
    Step 1: Create Profile (Essential) -> Commit to DB.
    Step 2: Redirect to Edit Page for Card & Residence details.
    """
    st.title("➕ Tạo người dùng mới")
    
    if st.button("← Quay lại danh sách"):
        st.session_state.page_view = 'user_list'
        st.rerun()
    
    st.markdown("---")
    
    st.info("ℹ️ Vui lòng tạo thông tin Hồ sơ trước. Sau khi tạo thành công, bạn sẽ được chuyển đến trang Chỉnh sửa để thêm thẻ CCCD và thông tin Cư trú.")
    
    # Render only User Profile form
    profile_data, profile_errors, submitted_profile = render_user_form(
        user_data=st.session_state.user_profile_data,
        form_key="create_profile_form"
    )
    
    # Sync state for persistence if page reruns
    if profile_data:
        st.session_state.user_profile_data = profile_data

    # Handle Submission
    if submitted_profile:
        if not profile_errors:
            try:
                # Initialize manager
                db = get_firestore_client()
                user_manager = UserManager(db)
                
                # Create user in Firestore immediately
                with st.spinner("Đang tạo người dùng..."):
                    new_uid = user_manager.create_user(
                        user_data=profile_data,
                        citizen_card_data=None, # Will be added in Edit step
                        residence_data=None     # Will be added in Edit step
                    )
                
                # Success & Redirect
                show_success_message("✅ Tạo người dùng thành công! Đang chuyển hướng...")
                
                # Set state for redirection
                st.session_state.selected_user_uid = new_uid
                st.session_state.page_view = 'edit_user'
                
                # Clear create form state
                st.session_state.user_profile_data = {}
                st.session_state.citizen_card_data = {}
                st.session_state.residence_data = {}
                
                st.rerun()
                
            except Exception as e:
                show_error_message(f"Không thể tạo người dùng: {str(e)}")
        else:
            show_error_message("Vui lòng sửa các lỗi trong form trước khi tạo.")




def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="VNeID Admin Dashboard",
        page_icon="🇻🇳",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    load_custom_css()
    initialize_session_state()
    
    render_navigation_sidebar()
    
    # Router
    if st.session_state.page_view == 'user_list':
        render_user_list_page()
    elif st.session_state.page_view == 'create_user':
        render_create_user_page()
    elif st.session_state.page_view == 'edit_user':
        render_edit_user_page()
    elif st.session_state.page_view == 'user_detail':
        render_user_detail_page()
    else:
        render_user_list_page()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("Lỗi nghiêm trọng:")
        st.code(traceback.format_exc())
