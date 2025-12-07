# Firebase Admin Dashboard

A Streamlit-based admin dashboard for managing users in the vneid Firebase application.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
streamlit run main.py
```

### 3. Access the Dashboard
- Open your browser to `http://localhost:8501`
- Login with admin credentials:
  - Email: `admin@vneid.com`
  - Password: `admin123`

## Features

- **User Management**: Create, read, update, and delete user profiles
- **Citizen Card Management**: Manage citizen identification documents
- **Residence Management**: Handle residence information and household members
- **Audit Logging**: Track all administrative actions
- **Search & Filter**: Find users quickly with advanced search

## Configuration

The application is pre-configured for the `expense-tracking-app-27ae6` Firebase project.

### Firebase Collections
- `users` - User profiles
- `citizen_cards` - Citizen identification documents
- `residence` - Residence information
- `admin_audit_logs` - Audit trail

### Admin Access
- Default admin email: `admin@vneid.com`
- Default password: `admin123` (change this in production)

## Project Structure

```
firebase_admin_dashboard/
├── main.py                 # Main Streamlit application
├── config/                 # Configuration files
├── modules/                # Core application modules
├── utils/                  # Utility functions
├── styles/                 # CSS styling
└── .streamlit/            # Streamlit configuration
```

## Security Notes

- Change the default admin password in `.streamlit/secrets.toml`
- The Firebase service account key is already configured
- All admin actions are logged for audit purposes

## Support

For issues or questions, check the application logs or Firebase console for detailed error information.