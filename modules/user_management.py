"""
User Management Module

This module provides the UserManager class for comprehensive CRUD operations
on user data across all Firebase collections (users, citizen_cards, residence).
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

try:
    from firebase_admin_dashboard.utils.models import UserProfile, CitizenCard, Residence, HouseholdMember
    from firebase_admin_dashboard.utils.validators import (
        validate_user_profile,
        validate_citizen_card,
        validate_residence,
        validate_household_member_data,
    )
except ImportError:
    from utils.models import UserProfile, CitizenCard, Residence, HouseholdMember
    from utils.validators import (
        validate_user_profile,
        validate_citizen_card,
        validate_residence,
        validate_household_member_data,
    )

logger = logging.getLogger(__name__)


class UserManager:
    """
    Manages CRUD operations for user data across all Firebase collections.
    
    This class provides methods to create, read, update, and delete users
    along with their related data (citizen cards, residence information).
    """
    
    def __init__(self, db: firestore.Client):
        """
        Initialize UserManager with Firestore database client.
        
        Args:
            db: Firestore database client instance
        """
        self.db = db
        self.users_collection = db.collection('users')
        self.citizen_cards_collection = db.collection('citizen_cards')
        self.residence_collection = db.collection('residence')
    
    def get_all_users(self, search_term: Optional[str] = None, 
                     date_filter: Optional[Dict[str, datetime]] = None,
                     limit: int = 100, offset: int = 0,
                     search_field: str = 'all') -> Tuple[List[UserProfile], int]:
        """
        Retrieve all users with optional search and filtering capabilities.
        
        Args:
            search_term: Optional search term to filter by name, email, or citizen_id
            date_filter: Optional date range filter with 'start_date' and 'end_date' keys
            limit: Maximum number of users to return (default: 100)
            offset: Number of users to skip for pagination (default: 0)
            search_field: Field to search in ('all', 'name', 'email', 'citizen_id')
            
        Returns:
            Tuple of (list of UserProfile objects, total count)
            
        Requirements: 2.1, 2.2, 2.3
        """
        try:
            logger.info(f"Retrieving users with search_term='{search_term}' in field='{search_field}', "
                       f"date_filter={date_filter}, limit={limit}, offset={offset}")
            
            # Start with base query
            query = self.users_collection
            
            # Apply date filter if provided
            if date_filter:
                if 'start_date' in date_filter:
                    query = query.where(
                        filter=FieldFilter('created_at', '>=', date_filter['start_date'])
                    )
                if 'end_date' in date_filter:
                    query = query.where(
                        filter=FieldFilter('created_at', '<=', date_filter['end_date'])
                    )
            
            # Order by created_at for consistent pagination
            query = query.order_by('created_at', direction=firestore.Query.DESCENDING)
            
            # Get total count for pagination (without limit/offset)
            total_count = len(list(query.stream()))
            
            # Apply pagination
            if offset > 0:
                query = query.offset(offset)
            query = query.limit(limit)
            
            # Execute query
            docs = query.stream()
            users = []
            
            for doc in docs:
                try:
                    user_data = doc.to_dict()
                    user_data['uid'] = doc.id  # Ensure uid is set from document ID
                    user = UserProfile.from_dict(user_data)
                    
                    # Apply search filter in memory
                    if search_term:
                        search_lower = search_term.lower()
                        match = False
                        
                        if search_field == 'name':
                            match = search_lower in user.name.lower()
                        elif search_field == 'email':
                            match = search_lower in user.email.lower()
                        elif search_field == 'citizen_id':
                            match = search_lower in user.citizen_id.lower()
                        else:  # 'all'
                            match = (search_lower in user.name.lower() or 
                                     search_lower in user.email.lower() or 
                                     search_lower in user.citizen_id.lower())
                        
                        if not match:
                            continue
                    
                    users.append(user)
                    
                except Exception as e:
                    logger.warning(f"Error parsing user document {doc.id}: {str(e)}")
                    continue
            
            # Adjust total count if search filter was applied
            if search_term:
                # Re-run query without pagination to get accurate search count
                all_docs = self.users_collection.order_by('created_at', 
                                                         direction=firestore.Query.DESCENDING).stream()
                search_count = 0
                for doc in all_docs:
                    try:
                        user_data = doc.to_dict()
                        user_data['uid'] = doc.id
                        user = UserProfile.from_dict(user_data)
                        
                        search_lower = search_term.lower()
                        match = False
                        
                        if search_field == 'name':
                            match = search_lower in user.name.lower()
                        elif search_field == 'email':
                            match = search_lower in user.email.lower()
                        elif search_field == 'citizen_id':
                            match = search_lower in user.citizen_id.lower()
                        else:
                            match = (search_lower in user.name.lower() or 
                                     search_lower in user.email.lower() or 
                                     search_lower in user.citizen_id.lower())
                        
                        if match:
                            search_count += 1
                    except Exception:
                        continue
                total_count = search_count
            
            logger.info(f"Retrieved {len(users)} users out of {total_count} total")
            return users, total_count
            
        except Exception as e:
            logger.error(f"Error retrieving users: {str(e)}")
            raise Exception(f"Failed to retrieve users: {str(e)}")
    
    def get_user_by_id(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve complete user data including all related documents.
        
        Args:
            uid: User ID to retrieve
            
        Returns:
            Dictionary containing user profile, citizen card, and residence data,
            or None if user not found
            
        Requirements: 4.1, 4.2, 4.3
        """
        try:
            logger.info(f"Retrieving complete user data for uid: {uid}")
            
            # Get user profile
            user_doc = self.users_collection.document(uid).get()
            if not user_doc.exists:
                logger.warning(f"User not found: {uid}")
                return None
            
            user_data = user_doc.to_dict()
            user_data['uid'] = uid
            user_profile = UserProfile.from_dict(user_data)
            
            result = {
                'profile': user_profile,
                'citizen_card': None,
                'residence': None
            }
            
            # Get citizen card if exists
            try:
                citizen_card_doc = self.citizen_cards_collection.document(uid).get()
                if citizen_card_doc.exists:
                    card_data = citizen_card_doc.to_dict()
                    card_data['uid'] = uid
                    result['citizen_card'] = CitizenCard.from_dict(card_data)
            except Exception as e:
                logger.warning(f"Error retrieving citizen card for {uid}: {str(e)}")
            
            # Get residence if exists
            try:
                residence_doc = self.residence_collection.document(uid).get()
                if residence_doc.exists:
                    residence_data = residence_doc.to_dict()
                    residence_data['uid'] = uid
                    
                    # Get household members from subcollection
                    household_members = []
                    members_ref = residence_doc.reference.collection('household_members')
                    for member_doc in members_ref.stream():
                        member_data = member_doc.to_dict()
                        household_members.append(HouseholdMember.from_dict(member_data))
                    
                    residence_data['household_members'] = household_members
                    result['residence'] = Residence.from_dict(residence_data)
            except Exception as e:
                logger.warning(f"Error retrieving residence for {uid}: {str(e)}")
            
            logger.info(f"Successfully retrieved complete user data for {uid}")
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving user {uid}: {str(e)}")
            raise Exception(f"Failed to retrieve user {uid}: {str(e)}")
    
    def search_users_by_citizen_id(self, citizen_id: str) -> List[UserProfile]:
        """
        Search for users by citizen ID (for uniqueness validation).
        
        Args:
            citizen_id: Citizen ID to search for
            
        Returns:
            List of UserProfile objects with matching citizen_id
        """
        try:
            logger.info(f"Searching for users with citizen_id: {citizen_id}")
            
            query = self.users_collection.where(
                filter=FieldFilter('citizen_id', '==', citizen_id)
            )
            
            users = []
            for doc in query.stream():
                user_data = doc.to_dict()
                user_data['uid'] = doc.id
                users.append(UserProfile.from_dict(user_data))
            
            logger.info(f"Found {len(users)} users with citizen_id: {citizen_id}")
            return users
            
        except Exception as e:
            logger.error(f"Error searching users by citizen_id {citizen_id}: {str(e)}")
            raise Exception(f"Failed to search users by citizen_id: {str(e)}")
    
    def get_users_count(self) -> int:
        """
        Get total count of users in the system.
        
        Returns:
            Total number of users
        """
        try:
            # Use a more efficient count method if available, otherwise count documents
            docs = list(self.users_collection.stream())
            count = len(docs)
            logger.info(f"Total users count: {count}")
            return count
            
        except Exception as e:
            logger.error(f"Error getting users count: {str(e)}")
            raise Exception(f"Failed to get users count: {str(e)}")
    
    def validate_user_data(self, user_data: Dict[str, Any], 
                          citizen_card_data: Optional[Dict[str, Any]] = None,
                          residence_data: Optional[Dict[str, Any]] = None) -> Dict[str, List[str]]:
        """
        Validate user data across all collections.
        
        Args:
            user_data: User profile data to validate
            citizen_card_data: Optional citizen card data to validate
            residence_data: Optional residence data to validate
            
        Returns:
            Dictionary with validation errors by section
        """
        errors = {
            'profile': [],
            'citizen_card': [],
            'residence': []
        }
        
        try:
            # Validate user profile
            profile_errors = validate_user_profile(user_data)
            if profile_errors:
                errors['profile'] = profile_errors
            
            # Validate citizen card if provided
            if citizen_card_data:
                card_errors = validate_citizen_card(citizen_card_data)
                if card_errors:
                    errors['citizen_card'] = card_errors
            
            # Validate residence if provided
            if residence_data:
                residence_errors = validate_residence(residence_data)
                if residence_errors:
                    errors['residence'] = residence_errors
            
            # Cross-validation between documents
            if citizen_card_data and user_data:
                # Ensure citizen_id matches between profile and card
                if user_data.get('citizen_id') != citizen_card_data.get('citizen_id'):
                    errors['citizen_card'].append("Citizen ID must match user profile")
                
                # Ensure names are consistent
                if user_data.get('name') != citizen_card_data.get('full_name'):
                    errors['citizen_card'].append("Full name should match user profile name")
            
            if residence_data and user_data:
                # Ensure citizen_id matches between profile and residence
                if user_data.get('citizen_id') != residence_data.get('citizen_id'):
                    errors['residence'].append("Citizen ID must match user profile")
                
                # Ensure names are consistent
                if user_data.get('name') != residence_data.get('full_name'):
                    errors['residence'].append("Full name should match user profile name")
            
        except Exception as e:
            logger.error(f"Error during validation: {str(e)}")
            errors['profile'].append(f"Validation error: {str(e)}")
        
        return errors
    
    def create_user(self, user_data: Dict[str, Any], 
                   citizen_card_data: Optional[Dict[str, Any]] = None,
                   residence_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new user with all related documents across collections.
        
        Args:
            user_data: User profile data
            citizen_card_data: Optional citizen card data
            residence_data: Optional residence data
            
        Returns:
            UID of the created user
            
        Raises:
            ValueError: If validation fails or citizen_id is not unique
            Exception: If creation fails
            
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
        """
        try:
            logger.info(f"Creating new user with email: {user_data.get('email')}")
            
            # Validate all data first
            validation_errors = self.validate_user_data(user_data, citizen_card_data, residence_data)
            if any(errors for errors in validation_errors.values()):
                error_msg = "Validation failed: " + str(validation_errors)
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Check citizen_id uniqueness and use as UID
            citizen_id = user_data.get('citizen_id')
            if not citizen_id:
                raise ValueError("Citizen ID is required for creating a user.")

            if not self.check_citizen_id_uniqueness(citizen_id):
                error_msg = f"Citizen ID {citizen_id} already exists in the system"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Use Citizen ID as UID
            uid = citizen_id
            user_data['uid'] = uid
            
            # Generate default QR payloads if not provided
            user_data = self._generate_default_qr_payloads(user_data, uid)
            
            # Set default passcode if not provided
            if not user_data.get('passcode'):
                user_data['passcode'] = '789789'
            
            # Create UserProfile object
            user_profile = UserProfile.from_dict(user_data)
            
            # Use batch write for atomicity
            batch = self.db.batch()
            
            # Create user profile document with explicit UID
            user_ref = self.users_collection.document(uid)
            batch.set(user_ref, user_profile.to_dict())
            
            # Create citizen card document if provided
            if citizen_card_data:
                citizen_card_data['uid'] = uid
                citizen_card = CitizenCard.from_dict(citizen_card_data)
                citizen_card_ref = self.citizen_cards_collection.document(uid)
                batch.set(citizen_card_ref, citizen_card.to_dict())
            
            # Create residence document if provided
            if residence_data:
                residence_data['uid'] = uid
                residence = Residence.from_dict(residence_data)
                residence_ref = self.residence_collection.document(uid)
                batch.set(residence_ref, residence.to_dict())
                
                # Add household members if provided
                if residence.household_members:
                    for member in residence.household_members:
                        member_ref = residence_ref.collection('household_members').document(member.member_id)
                        batch.set(member_ref, member.to_dict())
            
            # Commit the batch
            batch.commit()
            
            logger.info(f"Successfully created user with UID: {uid}")
            return uid
            
        except ValueError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise Exception(f"Failed to create user: {str(e)}")
    
    def _generate_default_qr_payloads(self, user_data: Dict[str, Any], uid: str) -> Dict[str, Any]:
        """
        Generate default QR payloads if not provided.
        
        Args:
            user_data: User data dictionary
            uid: User ID to use as fallback
            
        Returns:
            Updated user data with default QR payloads
            
        Requirements: 3.4
        """
        qr_fields = ['qr_home', 'qr_card', 'qr_id_detail', 'qr_residence']
        
        for field in qr_fields:
            if not user_data.get(field):
                # Use UID as default QR payload
                user_data[field] = uid
                logger.debug(f"Generated default QR payload for {field}: {uid}")
        
        return user_data
    
    def create_user_batch(self, users_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple users in a batch operation.
        
        Args:
            users_data: List of user data dictionaries
            
        Returns:
            Dictionary with creation results and any errors
        """
        try:
            logger.info(f"Creating batch of {len(users_data)} users")
            
            results = {
                'successful': [],
                'failed': [],
                'errors': []
            }
            
            for i, user_data in enumerate(users_data):
                try:
                    uid = self.create_user(user_data)
                    results['successful'].append({
                        'index': i,
                        'uid': uid,
                        'email': user_data.get('email')
                    })
                except Exception as e:
                    results['failed'].append({
                        'index': i,
                        'email': user_data.get('email'),
                        'error': str(e)
                    })
                    results['errors'].append(f"User {i} ({user_data.get('email')}): {str(e)}")
            
            logger.info(f"Batch creation completed: {len(results['successful'])} successful, "
                       f"{len(results['failed'])} failed")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch user creation: {str(e)}")
            raise Exception(f"Failed to create users in batch: {str(e)}")
    
    def generate_unique_citizen_id(self, base_id: Optional[str] = None) -> str:
        """
        Generate a unique citizen ID.
        
        Args:
            base_id: Optional base ID to start with
            
        Returns:
            Unique citizen ID
        """
        import random
        import string
        
        if base_id and self.check_citizen_id_uniqueness(base_id):
            return base_id
        
        # Generate random citizen ID format: YYYYMMDDXXXXX
        from datetime import datetime
        
        attempts = 0
        max_attempts = 100
        
        while attempts < max_attempts:
            # Use current date + random 5 digits
            date_part = datetime.now().strftime('%Y%m%d')
            random_part = ''.join(random.choices(string.digits, k=5))
            candidate_id = f"{date_part}{random_part}"
            
            if self.check_citizen_id_uniqueness(candidate_id):
                logger.info(f"Generated unique citizen ID: {candidate_id}")
                return candidate_id
            
            attempts += 1
        
        # Fallback to UUID-based ID if random generation fails
        import uuid
        fallback_id = str(uuid.uuid4()).replace('-', '')[:13].upper()
        logger.warning(f"Using fallback citizen ID: {fallback_id}")
        return fallback_id
    
    def update_user_profile(self, uid: str, profile_data: Dict[str, Any]) -> bool:
        """
        Update user profile information.
        
        Args:
            uid: User ID to update
            profile_data: Updated profile data (excluding uid)
            
        Returns:
            True if update was successful
            
        Raises:
            ValueError: If validation fails
            Exception: If update fails
            
        Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
        """
        try:
            logger.info(f"Updating user profile for UID: {uid}")
            
            # Get current user data
            current_user = self.get_user_by_id(uid)
            if not current_user:
                raise ValueError(f"User not found: {uid}")
            
            # Prepare updated data
            updated_data = current_user['profile'].to_dict()
            updated_data.update(profile_data)
            updated_data['uid'] = uid  # Ensure UID is not changed
            updated_data['updated_at'] = datetime.utcnow()
            
            # Validate updated data
            validation_errors = validate_user_profile(updated_data)
            if validation_errors:
                error_msg = f"Validation failed: {validation_errors}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Check citizen_id uniqueness if it's being changed
            new_citizen_id = updated_data.get('citizen_id')
            current_citizen_id = current_user['profile'].citizen_id
            if new_citizen_id != current_citizen_id:
                if not self.check_citizen_id_uniqueness(new_citizen_id, exclude_uid=uid):
                    raise ValueError(f"Citizen ID {new_citizen_id} already exists")
            
            # Update the document
            user_ref = self.users_collection.document(uid)
            user_ref.update(updated_data)
            
            # Update related documents if citizen_id or name changed
            if (new_citizen_id != current_citizen_id or 
                updated_data.get('name') != current_user['profile'].name):
                self._update_related_documents_consistency(uid, updated_data)
            
            logger.info(f"Successfully updated user profile for UID: {uid}")
            return True
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error updating user profile {uid}: {str(e)}")
            raise Exception(f"Failed to update user profile: {str(e)}")
    
    def update_citizen_card(self, uid: str, card_data: Dict[str, Any]) -> bool:
        """
        Update citizen card information.
        
        Args:
            uid: User ID
            card_data: Updated citizen card data
            
        Returns:
            True if update was successful
            
        Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
        """
        try:
            logger.info(f"Updating citizen card for UID: {uid}")
            
            # Get current user data for consistency validation
            current_user = self.get_user_by_id(uid)
            if not current_user:
                raise ValueError(f"User not found: {uid}")
            
            # Prepare updated card data
            updated_card_data = card_data.copy()
            updated_card_data['uid'] = uid
            updated_card_data['updated_at'] = datetime.utcnow()
            
            # Validate updated data
            validation_errors = validate_citizen_card(updated_card_data)
            if validation_errors:
                error_msg = f"Validation failed: {validation_errors}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Data consistency validation
            user_profile = current_user['profile']
            if updated_card_data.get('citizen_id') != user_profile.citizen_id:
                raise ValueError("Citizen ID must match user profile")
            
            # Create or update citizen card document
            card_ref = self.citizen_cards_collection.document(uid)
            
            # Check if document exists
            if card_ref.get().exists:
                card_ref.update(updated_card_data)
            else:
                # Create new citizen card document
                citizen_card = CitizenCard.from_dict(updated_card_data)
                card_ref.set(citizen_card.to_dict())
            
            logger.info(f"Successfully updated citizen card for UID: {uid}")
            return True
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error updating citizen card {uid}: {str(e)}")
            raise Exception(f"Failed to update citizen card: {str(e)}")
    
    def update_residence(self, uid: str, residence_data: Dict[str, Any]) -> bool:
        """
        Update residence information.
        
        Args:
            uid: User ID
            residence_data: Updated residence data
            
        Returns:
            True if update was successful
            
        Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
        """
        try:
            logger.info(f"Updating residence for UID: {uid}")
            
            # Get current user data for consistency validation
            current_user = self.get_user_by_id(uid)
            if not current_user:
                raise ValueError(f"User not found: {uid}")
            
            # Prepare updated residence data
            updated_residence_data = residence_data.copy()
            updated_residence_data['uid'] = uid
            updated_residence_data['updated_at'] = datetime.utcnow()
            
            # Validate updated data
            validation_errors = validate_residence(updated_residence_data)
            if validation_errors:
                error_msg = f"Validation failed: {validation_errors}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Data consistency validation
            user_profile = current_user['profile']
            
            # Check ID match (handle both id_number and citizen_id keys)
            res_id = updated_residence_data.get('id_number') or updated_residence_data.get('citizen_id')
            if res_id and res_id != user_profile.citizen_id:
                raise ValueError(f"Citizen ID ({res_id}) must match user profile ({user_profile.citizen_id})")
            
            # Ensure id_number is set for Schema compliance
            if not updated_residence_data.get('id_number') and updated_residence_data.get('citizen_id'):
                updated_residence_data['id_number'] = updated_residence_data['citizen_id']

            # Create or update residence document
            residence_ref = self.residence_collection.document(uid)
            
            # Check if document exists
            if residence_ref.get().exists:
                residence_ref.update(updated_residence_data)
            else:
                # Create new residence document
                residence = Residence.from_dict(updated_residence_data)
                residence_ref.set(residence.to_dict())
            
            logger.info(f"Successfully updated residence for UID: {uid}")
            return True
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error updating residence {uid}: {str(e)}")
            raise Exception(f"Failed to update residence: {str(e)}")
    
    def _update_related_documents_consistency(self, uid: str, user_data: Dict[str, Any]) -> None:
        """
        Update related documents to maintain data consistency.
        
        Args:
            uid: User ID
            user_data: Updated user profile data
        """
        try:
            batch = self.db.batch()
            
            # Update citizen card if exists
            citizen_card_ref = self.citizen_cards_collection.document(uid)
            citizen_card_doc = citizen_card_ref.get()
            if citizen_card_doc.exists:
                updates = {
                    'citizen_id': user_data.get('citizen_id'),
                    'full_name': user_data.get('name'),
                    'updated_at': datetime.utcnow()
                }
                batch.update(citizen_card_ref, updates)
            
            # Update residence if exists
            residence_ref = self.residence_collection.document(uid)
            residence_doc = residence_ref.get()
            if residence_doc.exists:
                updates = {
                    'citizen_id': user_data.get('citizen_id'),
                    'full_name': user_data.get('name'),
                    'updated_at': datetime.utcnow()
                }
                batch.update(residence_ref, updates)
            
            # Commit batch updates
            batch.commit()
            logger.info(f"Updated related documents for consistency: {uid}")
            
        except Exception as e:
            logger.warning(f"Error updating related documents for {uid}: {str(e)}")
            # Don't raise exception as this is a consistency operation
    
    def update_user_qr_payloads(self, uid: str, qr_payloads: Dict[str, str]) -> bool:
        """
        Update QR payloads for a user.
        
        Args:
            uid: User ID
            qr_payloads: Dictionary with QR payload updates
            
        Returns:
            True if update was successful
        """
        try:
            logger.info(f"Updating QR payloads for UID: {uid}")
            
            # Validate QR payload fields
            valid_qr_fields = ['qr_home', 'qr_card', 'qr_id_detail', 'qr_residence']
            updates = {}
            
            for field, value in qr_payloads.items():
                if field in valid_qr_fields:
                    updates[field] = value
            
            if updates:
                updates['updated_at'] = datetime.utcnow()
                
                # Update user profile
                user_ref = self.users_collection.document(uid)
                user_ref.update(updates)
                
                # Also update related docs if they store QR payload (legacy)
                # But mostly it's on user profile now.
                
                logger.info(f"Successfully updated QR payloads for UID: {uid}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating QR payloads for {uid}: {str(e)}")
            raise Exception(f"Failed to update QR payloads: {str(e)}")

    def update_household_members_collection(self, uid: str, members_data: List[Dict[str, Any]]) -> bool:
        """
        Update household members subcollection (Add/Update/Delete).
        
        Args:
            uid: User ID
            members_data: List of member dictionaries
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Updating household members for UID: {uid}")
            residence_ref = self.residence_collection.document(uid)
            members_ref = residence_ref.collection('household_members')
            
            batch = self.db.batch()
            
            # 1. Identify current members in DB
            current_member_ids = set()
            for doc in members_ref.stream():
                current_member_ids.add(doc.id)
            
            # 2. Identify new members from input
            new_members_map = {}
            for member_dict in members_data:
                # Ensure member_id exists
                if not member_dict.get('member_id'):
                    member_dict['member_id'] = str(uuid.uuid4())
                
                member_id = member_dict['member_id']
                new_members_map[member_id] = member_dict
            
            # 3. Delete removed members
            for mid in current_member_ids:
                if mid not in new_members_map:
                    batch.delete(members_ref.document(mid))
            
            # 4. Set/Update new members
            for mid, m_data in new_members_map.items():
                # Validate member data using helper or model
                member_obj = HouseholdMember.from_dict(m_data) # ensures validation/defaults
                batch.set(members_ref.document(mid), member_obj.to_dict())
            
            batch.commit()
            logger.info(f"Successfully synced household members for UID: {uid}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating household members for {uid}: {str(e)}")
            raise Exception(f"Failed to update household members: {str(e)}")
    
    def bulk_update_users(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform bulk updates on multiple users.
        
        Args:
            updates: List of update dictionaries with 'uid' and update data
            
        Returns:
            Dictionary with update results
        """
        try:
            logger.info(f"Performing bulk update on {len(updates)} users")
            
            results = {
                'successful': [],
                'failed': [],
                'errors': []
            }
            
            for update_data in updates:
                uid = update_data.get('uid')
                if not uid:
                    results['failed'].append({'error': 'Missing UID'})
                    continue
                
                try:
                    profile_data = {k: v for k, v in update_data.items() if k != 'uid'}
                    self.update_user_profile(uid, profile_data)
                    results['successful'].append({'uid': uid})
                except Exception as e:
                    results['failed'].append({'uid': uid, 'error': str(e)})
                    results['errors'].append(f"User {uid}: {str(e)}")
            
            logger.info(f"Bulk update completed: {len(results['successful'])} successful, "
                       f"{len(results['failed'])} failed")
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk user update: {str(e)}")
            raise Exception(f"Failed to perform bulk update: {str(e)}")
    
    def delete_user(self, uid: str, confirmation_data: Optional[Dict[str, str]] = None) -> bool:
        """
        Delete user and all related documents with cascade operations.
        
        Args:
            uid: User ID to delete
            confirmation_data: Optional confirmation data (name or citizen_id)
            
        Returns:
            True if deletion was successful
            
        Raises:
            ValueError: If confirmation fails or user not found
            Exception: If deletion fails
            
        Requirements: 6.1, 6.2, 6.4, 6.5
        """
        try:
            logger.info(f"Deleting user with UID: {uid}")
            
            # Get user data for confirmation and cascade deletion
            user_data = self.get_user_by_id(uid)
            if not user_data:
                raise ValueError(f"User not found: {uid}")
            
            user_profile = user_data['profile']
            
            # Confirmation validation if provided
            if confirmation_data:
                self._validate_deletion_confirmation(user_profile, confirmation_data)
            
            # Perform cascade deletion using batch operation for atomicity
            batch = self.db.batch()
            deletion_results = {
                'user_profile': False,
                'citizen_card': False,
                'residence': False,
                'household_members': 0,
                'errors': []
            }
            
            try:
                # Delete user profile
                user_ref = self.users_collection.document(uid)
                batch.delete(user_ref)
                deletion_results['user_profile'] = True
                
                # Delete citizen card if exists
                citizen_card_ref = self.citizen_cards_collection.document(uid)
                if citizen_card_ref.get().exists:
                    batch.delete(citizen_card_ref)
                    deletion_results['citizen_card'] = True
                
                # Delete residence and household members if exists
                residence_ref = self.residence_collection.document(uid)
                residence_doc = residence_ref.get()
                if residence_doc.exists:
                    # Delete household members first
                    members_count = self._delete_household_members_batch(batch, residence_ref)
                    deletion_results['household_members'] = members_count
                    
                    # Delete residence document
                    batch.delete(residence_ref)
                    deletion_results['residence'] = True
                
                # Commit all deletions
                batch.commit()
                
                logger.info(f"Successfully deleted user {uid} and all related data: {deletion_results}")
                return True
                
            except Exception as e:
                error_msg = f"Partial deletion failure for user {uid}: {str(e)}"
                logger.error(error_msg)
                deletion_results['errors'].append(error_msg)
                raise Exception(f"Deletion failed with partial completion: {deletion_results}")
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error deleting user {uid}: {str(e)}")
            raise Exception(f"Failed to delete user: {str(e)}")
    
    def _validate_deletion_confirmation(self, user_profile: UserProfile, 
                                      confirmation_data: Dict[str, str]) -> None:
        """
        Validate deletion confirmation data.
        
        Args:
            user_profile: User profile to validate against
            confirmation_data: Confirmation data to validate
            
        Raises:
            ValueError: If confirmation fails
        """
        confirmation_name = confirmation_data.get('name', '').strip().lower()
        confirmation_citizen_id = confirmation_data.get('citizen_id', '').strip()
        
        name_match = confirmation_name == user_profile.name.lower()
        citizen_id_match = confirmation_citizen_id == user_profile.citizen_id
        
        if not (name_match or citizen_id_match):
            raise ValueError(
                "Confirmation failed. Please provide the correct name or citizen ID."
            )
        
        logger.info(f"Deletion confirmation validated for user: {user_profile.uid}")
    
    def _delete_household_members_batch(self, batch, residence_ref) -> int:
        """
        Add household member deletions to batch operation.
        
        Args:
            batch: Firestore batch object
            residence_ref: Reference to residence document
            
        Returns:
            Number of household members deleted
        """
        try:
            members_collection = residence_ref.collection('household_members')
            members_docs = list(members_collection.stream())
            
            for member_doc in members_docs:
                batch.delete(member_doc.reference)
            
            logger.info(f"Added {len(members_docs)} household member deletions to batch")
            return len(members_docs)
            
        except Exception as e:
            logger.warning(f"Error preparing household member deletions: {str(e)}")
            return 0
    
    def delete_multiple_users(self, uids: List[str], 
                            confirmation_required: bool = True) -> Dict[str, Any]:
        """
        Delete multiple users with cascade operations.
        
        Args:
            uids: List of user IDs to delete
            confirmation_required: Whether to require confirmation for each user
            
        Returns:
            Dictionary with deletion results
        """
        try:
            logger.info(f"Deleting multiple users: {len(uids)} users")
            
            results = {
                'successful': [],
                'failed': [],
                'errors': [],
                'total_processed': len(uids)
            }
            
            for uid in uids:
                try:
                    # Skip confirmation for batch operations unless specifically required
                    confirmation_data = None
                    if confirmation_required:
                        # In batch operations, we might skip individual confirmations
                        # This would be handled by the UI layer
                        pass
                    
                    self.delete_user(uid, confirmation_data)
                    results['successful'].append(uid)
                    
                except Exception as e:
                    results['failed'].append({'uid': uid, 'error': str(e)})
                    results['errors'].append(f"User {uid}: {str(e)}")
            
            logger.info(f"Batch deletion completed: {len(results['successful'])} successful, "
                       f"{len(results['failed'])} failed")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch user deletion: {str(e)}")
            raise Exception(f"Failed to delete users in batch: {str(e)}")
    
    def soft_delete_user(self, uid: str, admin_email: str) -> bool:
        """
        Soft delete a user by marking as deleted instead of removing.
        
        Args:
            uid: User ID to soft delete
            admin_email: Admin performing the deletion
            
        Returns:
            True if soft deletion was successful
        """
        try:
            logger.info(f"Soft deleting user {uid} by admin {admin_email}")
            
            # Check if user exists
            user_data = self.get_user_by_id(uid)
            if not user_data:
                raise ValueError(f"User not found: {uid}")
            
            # Mark user as deleted
            updates = {
                'deleted': True,
                'deleted_at': datetime.utcnow(),
                'deleted_by': admin_email,
                'updated_at': datetime.utcnow()
            }
            
            user_ref = self.users_collection.document(uid)
            user_ref.update(updates)
            
            logger.info(f"Successfully soft deleted user: {uid}")
            return True
            
        except Exception as e:
            logger.error(f"Error soft deleting user {uid}: {str(e)}")
            raise Exception(f"Failed to soft delete user: {str(e)}")
    
    def restore_soft_deleted_user(self, uid: str, admin_email: str) -> bool:
        """
        Restore a soft-deleted user.
        
        Args:
            uid: User ID to restore
            admin_email: Admin performing the restoration
            
        Returns:
            True if restoration was successful
        """
        try:
            logger.info(f"Restoring soft deleted user {uid} by admin {admin_email}")
            
            # Check if user exists and is soft deleted
            user_ref = self.users_collection.document(uid)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                raise ValueError(f"User not found: {uid}")
            
            user_data = user_doc.to_dict()
            if not user_data.get('deleted', False):
                raise ValueError(f"User {uid} is not soft deleted")
            
            # Remove deletion markers
            updates = {
                'deleted': firestore.DELETE_FIELD,
                'deleted_at': firestore.DELETE_FIELD,
                'deleted_by': firestore.DELETE_FIELD,
                'restored_at': datetime.utcnow(),
                'restored_by': admin_email,
                'updated_at': datetime.utcnow()
            }
            
            user_ref.update(updates)
            
            logger.info(f"Successfully restored user: {uid}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring user {uid}: {str(e)}")
            raise Exception(f"Failed to restore user: {str(e)}")
    
    def get_deletion_impact(self, uid: str) -> Dict[str, Any]:
        """
        Get information about what will be deleted when removing a user.
        
        Args:
            uid: User ID to analyze
            
        Returns:
            Dictionary with deletion impact information
        """
        try:
            logger.info(f"Analyzing deletion impact for user: {uid}")
            
            user_data = self.get_user_by_id(uid)
            if not user_data:
                return {'error': 'User not found'}
            
            impact = {
                'user_profile': {
                    'exists': True,
                    'name': user_data['profile'].name,
                    'email': user_data['profile'].email,
                    'citizen_id': user_data['profile'].citizen_id
                },
                'citizen_card': {
                    'exists': user_data['citizen_card'] is not None,
                    'details': user_data['citizen_card'].to_dict() if user_data['citizen_card'] else None
                },
                'residence': {
                    'exists': user_data['residence'] is not None,
                    'household_members_count': len(user_data['residence'].household_members) if user_data['residence'] else 0,
                    'household_members': [m.to_dict() for m in user_data['residence'].household_members] if user_data['residence'] else []
                },
                'total_documents': 1,  # Always have user profile
                'warning_messages': []
            }
            
            # Count total documents that will be deleted
            if impact['citizen_card']['exists']:
                impact['total_documents'] += 1
            
            if impact['residence']['exists']:
                impact['total_documents'] += 1 + impact['residence']['household_members_count']
            
            # Add warning messages
            if impact['residence']['household_members_count'] > 0:
                impact['warning_messages'].append(
                    f"This will also delete {impact['residence']['household_members_count']} household members"
                )
            
            if impact['total_documents'] > 3:
                impact['warning_messages'].append(
                    f"This operation will delete {impact['total_documents']} total documents"
                )
            
            logger.info(f"Deletion impact analysis completed for {uid}: {impact['total_documents']} documents")
            return impact
            
        except Exception as e:
            logger.error(f"Error analyzing deletion impact for {uid}: {str(e)}")
            return {'error': f"Failed to analyze deletion impact: {str(e)}"}
    
    def permanently_delete_soft_deleted_users(self, days_threshold: int = 30) -> Dict[str, Any]:
        """
        Permanently delete users that have been soft deleted for a specified period.
        
        Args:
            days_threshold: Number of days after which soft deleted users are permanently deleted
            
        Returns:
            Dictionary with cleanup results
        """
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
            logger.info(f"Permanently deleting users soft deleted before {cutoff_date}")
            
            # Find soft deleted users older than threshold
            query = self.users_collection.where(
                filter=FieldFilter('deleted', '==', True)
            ).where(
                filter=FieldFilter('deleted_at', '<=', cutoff_date)
            )
            
            users_to_delete = []
            for doc in query.stream():
                users_to_delete.append(doc.id)
            
            if not users_to_delete:
                logger.info("No soft deleted users found for permanent deletion")
                return {'deleted_count': 0, 'errors': []}
            
            # Permanently delete the users
            results = self.delete_multiple_users(users_to_delete, confirmation_required=False)
            
            logger.info(f"Permanent deletion cleanup completed: {len(results['successful'])} users deleted")
            return {
                'deleted_count': len(results['successful']),
                'failed_count': len(results['failed']),
                'errors': results['errors']
            }
            
        except Exception as e:
            logger.error(f"Error in permanent deletion cleanup: {str(e)}")
            raise Exception(f"Failed to perform permanent deletion cleanup: {str(e)}")
    
    def check_citizen_id_uniqueness(self, citizen_id: str, exclude_uid: Optional[str] = None) -> bool:
        """
        Check if citizen_id is unique in the system.
        
        Args:
            citizen_id: Citizen ID to check
            exclude_uid: Optional UID to exclude from check (for updates)
            
        Returns:
            True if citizen_id is unique, False otherwise
        """
        try:
            existing_users = self.search_users_by_citizen_id(citizen_id)
            
            if exclude_uid:
                # Filter out the user being updated
                existing_users = [u for u in existing_users if u.uid != exclude_uid]
            
            is_unique = len(existing_users) == 0
            logger.info(f"Citizen ID {citizen_id} uniqueness check: {is_unique}")
            return is_unique
            
        except Exception as e:
            logger.error(f"Error checking citizen_id uniqueness: {str(e)}")
            # In case of error, assume not unique for safety
            return False
    
    def get_user_summary(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        Get a summary of user information for list displays.
        
        Args:
            uid: User ID
            
        Returns:
            Dictionary with summary information or None if not found
        """
        try:
            user_doc = self.users_collection.document(uid).get()
            if not user_doc.exists:
                return None
            
            user_data = user_doc.to_dict()
            
            return {
                'uid': uid,
                'name': user_data.get('name', ''),
                'email': user_data.get('email', ''),
                'citizen_id': user_data.get('citizen_id', ''),
                'phone': user_data.get('phone', ''),
                'created_at': user_data.get('created_at'),
                'updated_at': user_data.get('updated_at')
            }
            
        except Exception as e:
            logger.error(f"Error getting user summary for {uid}: {str(e)}")
            return None
    
    def batch_get_users(self, uids: List[str]) -> Dict[str, UserProfile]:
        """
        Retrieve multiple users by their UIDs in a batch operation.
        
        Args:
            uids: List of user IDs to retrieve
            
        Returns:
            Dictionary mapping UID to UserProfile objects
        """
        try:
            logger.info(f"Batch retrieving {len(uids)} users")
            
            users = {}
            
            # Firestore batch get (more efficient than individual gets)
            docs = self.db.get_all([self.users_collection.document(uid) for uid in uids])
            
            for doc in docs:
                if doc.exists:
                    try:
                        user_data = doc.to_dict()
                        user_data['uid'] = doc.id
                        users[doc.id] = UserProfile.from_dict(user_data)
                    except Exception as e:
                        logger.warning(f"Error parsing user document {doc.id}: {str(e)}")
            
            logger.info(f"Successfully retrieved {len(users)} out of {len(uids)} users")
            return users
            
        except Exception as e:
            logger.error(f"Error in batch get users: {str(e)}")
            raise Exception(f"Failed to batch retrieve users: {str(e)}")
    
    def get_users_by_email_domain(self, domain: str) -> List[UserProfile]:
        """
        Get users by email domain (useful for organization-based filtering).
        
        Args:
            domain: Email domain to filter by (e.g., 'company.com')
            
        Returns:
            List of UserProfile objects with matching email domain
        """
        try:
            logger.info(f"Retrieving users with email domain: {domain}")
            
            # Since Firestore doesn't support regex queries, we'll get all users
            # and filter in memory (not ideal for large datasets)
            all_users, _ = self.get_all_users(limit=1000)  # Reasonable limit
            
            domain_users = []
            for user in all_users:
                if user.email.endswith(f'@{domain}'):
                    domain_users.append(user)
            
            logger.info(f"Found {len(domain_users)} users with domain {domain}")
            return domain_users
            
        except Exception as e:
            logger.error(f"Error retrieving users by domain {domain}: {str(e)}")
            raise Exception(f"Failed to retrieve users by domain: {str(e)}")
    
    def get_recent_users(self, days: int = 7, limit: int = 50) -> List[UserProfile]:
        """
        Get recently created users.
        
        Args:
            days: Number of days to look back (default: 7)
            limit: Maximum number of users to return (default: 50)
            
        Returns:
            List of recently created UserProfile objects
        """
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            logger.info(f"Retrieving users created since {cutoff_date}")
            
            query = self.users_collection.where(
                filter=FieldFilter('created_at', '>=', cutoff_date)
            ).order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit)
            
            users = []
            for doc in query.stream():
                try:
                    user_data = doc.to_dict()
                    user_data['uid'] = doc.id
                    users.append(UserProfile.from_dict(user_data))
                except Exception as e:
                    logger.warning(f"Error parsing recent user document {doc.id}: {str(e)}")
            
            logger.info(f"Retrieved {len(users)} recent users")
            return users
            
        except Exception as e:
            logger.error(f"Error retrieving recent users: {str(e)}")
            raise Exception(f"Failed to retrieve recent users: {str(e)}")
    
    def manage_household_members(self, uid: str, operation: str, member_data: Optional[Dict[str, Any]] = None, 
                               member_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Manage household members for a residence record with CRUD operations.
        
        Args:
            uid: User ID for the residence
            operation: Operation type ('list', 'add', 'update', 'delete')
            member_data: Member data for add/update operations
            member_id: Member ID for update/delete operations
            
        Returns:
            Dictionary with operation results and household member data
            
        Raises:
            ValueError: If validation fails or member not found
            Exception: If operation fails
            
        Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
        """
        try:
            logger.info(f"Managing household members for UID {uid}, operation: {operation}")
            
            # Get residence document
            residence_ref = self.residence_collection.document(uid)
            residence_doc = residence_ref.get()
            
            if not residence_doc.exists:
                raise ValueError(f"Residence not found for user: {uid}")
            
            members_collection = residence_ref.collection('household_members')
            
            if operation == 'list':
                return self._list_household_members(members_collection)
            
            elif operation == 'add':
                if not member_data:
                    raise ValueError("Member data is required for add operation")
                return self._add_household_member(residence_ref, members_collection, member_data)
            
            elif operation == 'update':
                if not member_id or not member_data:
                    raise ValueError("Member ID and member data are required for update operation")
                return self._update_household_member(residence_ref, members_collection, member_id, member_data)
            
            elif operation == 'delete':
                if not member_id:
                    raise ValueError("Member ID is required for delete operation")
                return self._delete_household_member(residence_ref, members_collection, member_id)
            
            else:
                raise ValueError(f"Invalid operation: {operation}. Must be 'list', 'add', 'update', or 'delete'")
                
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error managing household members for {uid}: {str(e)}")
            raise Exception(f"Failed to manage household members: {str(e)}")
    
    def _list_household_members(self, members_collection) -> Dict[str, Any]:
        """
        List all household members for a residence.
        
        Args:
            members_collection: Firestore collection reference for household members
            
        Returns:
            Dictionary with list of household members
            
        Requirements: 7.1
        """
        try:
            members = []
            for member_doc in members_collection.stream():
                member_data = member_doc.to_dict()
                member = HouseholdMember.from_dict(member_data)
                members.append(member.to_dict())
            
            logger.info(f"Retrieved {len(members)} household members")
            return {
                'success': True,
                'members': members,
                'count': len(members)
            }
            
        except Exception as e:
            logger.error(f"Error listing household members: {str(e)}")
            raise Exception(f"Failed to list household members: {str(e)}")
    
    def _add_household_member(self, residence_ref, members_collection, member_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new household member to the residence.
        
        Args:
            residence_ref: Firestore document reference for residence
            members_collection: Firestore collection reference for household members
            member_data: Data for the new household member
            
        Returns:
            Dictionary with operation results
            
        Requirements: 7.2, 7.5
        """
        try:
            # Validate household member data
            from ..utils.validators import validate_household_member_data
            validation_result = validate_household_member_data(member_data)
            if not validation_result['valid']:
                raise ValueError(f"Validation failed: {validation_result['errors']}")
            
            # Create HouseholdMember object
            member = HouseholdMember.from_dict(member_data)
            
            # Use batch operation for atomicity
            batch = self.db.batch()
            
            # Add household member document
            member_ref = members_collection.document(member.member_id)
            batch.set(member_ref, member.to_dict())
            
            # Update residence updated_at timestamp
            batch.update(residence_ref, {'updated_at': datetime.utcnow()})
            
            # Commit the batch
            batch.commit()
            
            logger.info(f"Successfully added household member: {member.member_id}")
            return {
                'success': True,
                'member_id': member.member_id,
                'member': member.to_dict(),
                'message': f"Household member '{member.name}' added successfully"
            }
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error adding household member: {str(e)}")
            raise Exception(f"Failed to add household member: {str(e)}")
    
    def _update_household_member(self, residence_ref, members_collection, member_id: str, 
                               member_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing household member.
        
        Args:
            residence_ref: Firestore document reference for residence
            members_collection: Firestore collection reference for household members
            member_id: ID of the member to update
            member_data: Updated member data
            
        Returns:
            Dictionary with operation results
            
        Requirements: 7.3, 7.5
        """
        try:
            # Check if member exists
            member_ref = members_collection.document(member_id)
            member_doc = member_ref.get()
            
            if not member_doc.exists:
                raise ValueError(f"Household member not found: {member_id}")
            
            # Validate updated member data
            from ..utils.validators import validate_household_member_data
            updated_data = member_data.copy()
            updated_data['member_id'] = member_id  # Ensure member_id is preserved
            
            validation_result = validate_household_member_data(updated_data)
            if not validation_result['valid']:
                raise ValueError(f"Validation failed: {validation_result['errors']}")
            
            # Create updated HouseholdMember object
            updated_member = HouseholdMember.from_dict(updated_data)
            
            # Use batch operation for atomicity
            batch = self.db.batch()
            
            # Update household member document
            batch.update(member_ref, updated_member.to_dict())
            
            # Update residence updated_at timestamp
            batch.update(residence_ref, {'updated_at': datetime.utcnow()})
            
            # Commit the batch
            batch.commit()
            
            logger.info(f"Successfully updated household member: {member_id}")
            return {
                'success': True,
                'member_id': member_id,
                'member': updated_member.to_dict(),
                'message': f"Household member '{updated_member.name}' updated successfully"
            }
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error updating household member {member_id}: {str(e)}")
            raise Exception(f"Failed to update household member: {str(e)}")
    
    def _delete_household_member(self, residence_ref, members_collection, member_id: str) -> Dict[str, Any]:
        """
        Delete a household member with confirmation.
        
        Args:
            residence_ref: Firestore document reference for residence
            members_collection: Firestore collection reference for household members
            member_id: ID of the member to delete
            
        Returns:
            Dictionary with operation results
            
        Requirements: 7.4, 7.5
        """
        try:
            # Check if member exists and get member info for confirmation
            member_ref = members_collection.document(member_id)
            member_doc = member_ref.get()
            
            if not member_doc.exists:
                raise ValueError(f"Household member not found: {member_id}")
            
            member_data = member_doc.to_dict()
            member_name = member_data.get('name', 'Unknown')
            
            # Use batch operation for atomicity
            batch = self.db.batch()
            
            # Delete household member document
            batch.delete(member_ref)
            
            # Update residence updated_at timestamp
            batch.update(residence_ref, {'updated_at': datetime.utcnow()})
            
            # Commit the batch
            batch.commit()
            
            logger.info(f"Successfully deleted household member: {member_id}")
            return {
                'success': True,
                'member_id': member_id,
                'deleted_member_name': member_name,
                'message': f"Household member '{member_name}' deleted successfully"
            }
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error deleting household member {member_id}: {str(e)}")
            raise Exception(f"Failed to delete household member: {str(e)}")
    
    def get_household_member_by_id(self, uid: str, member_id: str) -> Optional[HouseholdMember]:
        """
        Get a specific household member by ID.
        
        Args:
            uid: User ID for the residence
            member_id: ID of the household member
            
        Returns:
            HouseholdMember object or None if not found
        """
        try:
            logger.info(f"Retrieving household member {member_id} for user {uid}")
            
            residence_ref = self.residence_collection.document(uid)
            member_ref = residence_ref.collection('household_members').document(member_id)
            member_doc = member_ref.get()
            
            if not member_doc.exists:
                logger.warning(f"Household member not found: {member_id}")
                return None
            
            member_data = member_doc.to_dict()
            member = HouseholdMember.from_dict(member_data)
            
            logger.info(f"Successfully retrieved household member: {member_id}")
            return member
            
        except Exception as e:
            logger.error(f"Error retrieving household member {member_id}: {str(e)}")
            raise Exception(f"Failed to retrieve household member: {str(e)}")
    
    def validate_household_member_uniqueness(self, uid: str, member_data: Dict[str, Any], 
                                           exclude_member_id: Optional[str] = None) -> bool:
        """
        Validate that household member data doesn't create duplicates.
        
        Args:
            uid: User ID for the residence
            member_data: Member data to validate
            exclude_member_id: Optional member ID to exclude from check (for updates)
            
        Returns:
            True if member data is unique, False otherwise
        """
        try:
            # Get all existing household members
            result = self.manage_household_members(uid, 'list')
            existing_members = result.get('members', [])
            
            # Check for duplicate citizen_id if provided
            new_citizen_id = member_data.get('citizen_id')
            if new_citizen_id:
                for member in existing_members:
                    if (member.get('citizen_id') == new_citizen_id and 
                        member.get('member_id') != exclude_member_id):
                        logger.warning(f"Duplicate citizen_id found in household: {new_citizen_id}")
                        return False
            
            # Check for duplicate name + relationship combination
            new_name = member_data.get('name', '').strip().lower()
            new_relationship = member_data.get('relationship', '').strip().lower()
            
            for member in existing_members:
                existing_name = member.get('name', '').strip().lower()
                existing_relationship = member.get('relationship', '').strip().lower()
                
                if (existing_name == new_name and 
                    existing_relationship == new_relationship and
                    member.get('member_id') != exclude_member_id):
                    logger.warning(f"Duplicate name+relationship found: {new_name} ({new_relationship})")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating household member uniqueness: {str(e)}")
            # In case of error, assume not unique for safety
            return False
    
    def bulk_update_household_members(self, uid: str, members_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform bulk operations on household members.
        
        Args:
            uid: User ID for the residence
            members_data: List of member data with operation type
            
        Returns:
            Dictionary with bulk operation results
        """
        try:
            logger.info(f"Performing bulk household member operations for user {uid}")
            
            results = {
                'successful': [],
                'failed': [],
                'errors': [],
                'total_processed': len(members_data)
            }
            
            for i, member_operation in enumerate(members_data):
                try:
                    operation = member_operation.get('operation')
                    member_data = member_operation.get('data', {})
                    member_id = member_operation.get('member_id')
                    
                    if not operation:
                        raise ValueError("Operation type is required")
                    
                    result = self.manage_household_members(uid, operation, member_data, member_id)
                    results['successful'].append({
                        'index': i,
                        'operation': operation,
                        'result': result
                    })
                    
                except Exception as e:
                    results['failed'].append({
                        'index': i,
                        'operation': member_operation.get('operation'),
                        'error': str(e)
                    })
                    results['errors'].append(f"Operation {i}: {str(e)}")
            
            logger.info(f"Bulk household member operations completed: {len(results['successful'])} successful, "
                       f"{len(results['failed'])} failed")
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk household member operations: {str(e)}")
            raise Exception(f"Failed to perform bulk household member operations: {str(e)}")


# Utility functions for UserManager

def create_user_manager(db: firestore.Client) -> UserManager:
    """
    Create and return a UserManager instance.
    
    Args:
        db: Firestore database client
        
    Returns:
        UserManager instance
    """
    return UserManager(db)


def format_user_for_display(user: UserProfile) -> Dict[str, str]:
    """
    Format user data for display in UI components.
    
    Args:
        user: UserProfile object
        
    Returns:
        Dictionary with formatted display values
    """
    return {
        'uid': user.uid,
        'name': user.name,
        'email': user.email,
        'citizen_id': user.citizen_id,
        'phone': user.phone,
        'created_at': _safe_strftime(user.created_at),
        'updated_at': _safe_strftime(user.updated_at),
        'has_avatar': 'Yes' if user.avatar_url else 'No',
        'qr_configured': 'Yes' if any([user.qr_home, user.qr_card, user.qr_id_detail, user.qr_residence]) else 'No'
    }


def _safe_strftime(value) -> str:
    """Format datetime-like values safely."""
    if value is None:
        return ''
    from datetime import datetime
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    # Try parsing ISO/string timestamps
    try:
        return datetime.fromisoformat(str(value)).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return str(value)


def validate_search_parameters(search_term: Optional[str] = None,
                             date_filter: Optional[Dict[str, datetime]] = None,
                             limit: int = 100, offset: int = 0) -> Dict[str, str]:
    """
    Validate search parameters for get_all_users method.
    
    Args:
        search_term: Search term to validate
        date_filter: Date filter to validate
        limit: Limit to validate
        offset: Offset to validate
        
    Returns:
        Dictionary with validation errors (empty if valid)
    """
    errors = {}
    
    if search_term is not None and len(search_term.strip()) < 2:
        errors['search_term'] = 'Search term must be at least 2 characters long'
    
    if date_filter:
        if 'start_date' in date_filter and 'end_date' in date_filter:
            if date_filter['start_date'] > date_filter['end_date']:
                errors['date_filter'] = 'Start date must be before end date'
    
    if limit <= 0 or limit > 1000:
        errors['limit'] = 'Limit must be between 1 and 1000'
    
    if offset < 0:
        errors['offset'] = 'Offset must be non-negative'
    
    return errors