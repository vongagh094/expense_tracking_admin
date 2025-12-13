"""
Data models for the Firebase Admin Dashboard.
Aligns with mobile app Firestore schema.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

DEFAULT_PASSCODE = "789789"


@dataclass
class UserProfile:
    """User profile - matches Firestore users/{uid}"""
    
    uid: str
    full_name: str = ""
    email: str = ""
    phone_number: str = ""
    citizen_id: str = ""
    passcode: str = DEFAULT_PASSCODE
    
    # Core Identity Fields
    identity_level: int = 2
    date_of_birth: str = "" # DD/MM/YYYY
    gender: str = "Nam"
    nationality: str = "Việt Nam"
    
    # Address Fields
    permanent_address: str = ""
    current_address: str = ""
    temporary_address: str = ""
    address: Optional[str] = None # Legacy/Generic support
    
    # Assets
    avatar_asset: str = ""
    badge_asset: str = ""
    
    # Legacy/Internal
    avatar_url: Optional[str] = None # Deprecated in favor of avatar_asset? Keep for compat.
    
    # QR payloads
    qr_home: str = ""
    qr_card: str = ""
    qr_id_detail: str = ""
    qr_residence: str = ""
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Firestore document."""
        data = {
            'uid': self.uid,
            'full_name': self.full_name,
            'email': self.email,
            'phone_number': self.phone_number,
            'citizen_id': self.citizen_id,
            'passcode': self.passcode or DEFAULT_PASSCODE,
            'identity_level': self.identity_level,
            'date_of_birth': self.date_of_birth,
            'gender': self.gender,
            'nationality': self.nationality,
            'permanent_address': self.permanent_address,
            'current_address': self.current_address,
            'temporary_address': self.temporary_address,
            'avatar_asset': self.avatar_asset,
            'badge_asset': self.badge_asset,
            'qr_home': self.qr_home,
            'qr_card': self.qr_card,
            'qr_id_detail': self.qr_id_detail,
            'qr_residence': self.qr_residence,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }
        
        # Include legacy/optional if set
        if self.address: data['address'] = self.address
        if self.avatar_url: data['avatar_url'] = self.avatar_url
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Create from Firestore document."""
        # Handle date_of_birth legacy mapping
        dob = data.get('date_of_birth', data.get('dob', ''))
        if isinstance(dob, datetime):
            dob = dob.strftime('%d/%m/%Y')
            
        return cls(
            uid=data.get('uid', ''),
            full_name=data.get('full_name', data.get('name', '')),
            email=data.get('email', ''),
            phone_number=data.get('phone_number', data.get('phone', '')),
            citizen_id=data.get('citizen_id', ''),
            passcode=data.get('passcode', DEFAULT_PASSCODE),
            
            identity_level=data.get('identity_level', 2),
            date_of_birth=dob,
            gender=data.get('gender', 'Nam'),
            nationality=data.get('nationality', 'Việt Nam'),
            
            permanent_address=data.get('permanent_address', ''),
            current_address=data.get('current_address', ''),
            temporary_address=data.get('temporary_address', ''),
            address=data.get('address'),
            
            avatar_asset=data.get('avatar_asset', ''),
            badge_asset=data.get('badge_asset', ''),
            avatar_url=data.get('avatar_url'),
            
            qr_home=data.get('qr_home', ''),
            qr_card=data.get('qr_card', ''),
            qr_id_detail=data.get('qr_id_detail', ''),
            qr_residence=data.get('qr_residence', ''),
            
            created_at=data.get('created_at', datetime.utcnow()),
            updated_at=data.get('updated_at', datetime.utcnow()),
        )
    
    @property
    def name(self) -> str:
        return self.full_name
        
    @property
    def dob(self) -> str:
        return self.date_of_birth
    
    @property
    def phone(self) -> str:
        return self.phone_number


@dataclass
class CitizenCard:
    """Citizen card - matches Firestore citizen_cards/{uid}"""
    
    uid: str
    citizen_id: str = ""
    full_name: str = ""
    date_of_birth: str = "" # DD/MM/YYYY
    gender: str = "Nam"
    nationality: str = "Việt Nam"
    
    # Location info
    birthplace: str = "" # Place of Birth
    birth_registration_place: str = ""
    hometown: str = ""
    permanent_address: str = ""
    permanent_address_2: str = "" # Optional line 2
    temporary_address: str = ""
    current_address: str = ""
    
    # Additional info
    ethnicity: str = ""
    religion: str = ""
    identifying_marks: str = ""
    blood_type: str = ""
    profession: str = ""
    other_info: str = ""
    
    # Issue Details
    issue_date: str = "" # DD/MM/YYYY
    issue_place: str = ""
    
    # Meta
    qr_code_data: str = ""
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_updated_at: str = "" # String timestamp for display/sync if needed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Firestore document."""
        data = {
            'uid': self.uid,
            'citizen_id': self.citizen_id,
            'full_name': self.full_name,
            'date_of_birth': self.date_of_birth,
            'gender': self.gender,
            'nationality': self.nationality,
            'birthplace': self.birthplace,
            'birth_registration_place': self.birth_registration_place,
            'hometown': self.hometown,
            'permanent_address': self.permanent_address,
            'permanent_address_2': self.permanent_address_2,
            'temporary_address': self.temporary_address,
            'current_address': self.current_address,
            'ethnicity': self.ethnicity,
            'religion': self.religion,
            'identifying_marks': self.identifying_marks,
            'blood_type': self.blood_type,
            'profession': self.profession,
            'other_info': self.other_info,
            'issue_date': self.issue_date,
            'issue_place': self.issue_place,
            'qr_code_data': self.qr_code_data,
            'updated_at': self.updated_at,
            'last_updated_at': self.last_updated_at or self.updated_at.strftime("%d/%m/%Y")
        }
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CitizenCard':
        """Create from Firestore document."""
        
        # Handle date conversions if legacy data (datetime -> str)
        dob = data.get('date_of_birth', '')
        if isinstance(dob, datetime): dob = dob.strftime('%d/%m/%Y')
        
        issue = data.get('issue_date', '')
        if isinstance(issue, datetime): issue = issue.strftime('%d/%m/%Y')
        
        return cls(
            uid=data.get('uid', ''),
            citizen_id=data.get('citizen_id', ''),
            full_name=data.get('full_name', ''),
            date_of_birth=dob,
            gender=data.get('gender', 'Nam'),
            nationality=data.get('nationality', 'Việt Nam'),
            birthplace=data.get('birthplace', data.get('place_of_birth', '')),
            birth_registration_place=data.get('birth_registration_place', ''),
            hometown=data.get('hometown', ''),
            permanent_address=data.get('permanent_address', ''),
            permanent_address_2=data.get('permanent_address_2', ''),
            temporary_address=data.get('temporary_address', ''),
            current_address=data.get('current_address', ''),
            ethnicity=data.get('ethnicity', ''),
            religion=data.get('religion', ''),
            identifying_marks=data.get('identifying_marks', data.get('personal_identification', '')),
            blood_type=data.get('blood_type', ''),
            profession=data.get('profession', ''),
            other_info=data.get('other_info', ''),
            issue_date=issue,
            issue_place=data.get('issue_place', data.get('issuing_authority', '')),
            qr_code_data=data.get('qr_code_data', data.get('qr_payload', '')),
            updated_at=data.get('updated_at', datetime.utcnow()),
            last_updated_at=data.get('last_updated_at', datetime.utcnow().strftime("%d/%m/%Y"))
        )


@dataclass
class HouseholdMember:
    """Household member - matches residence/{uid}/household_members/{memberId}"""
    
    member_id: str = ""
    full_name: str = ""
    id_number: str = ""  # Changed from Optional to str default "" to match schema requirement usually
    birth_date: str = ""
    gender: str = ""
    relation_to_head: str = ""
    citizen_status: Optional[str] = None
    
    def __post_init__(self):
        if not self.member_id:
            self.member_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Firestore document format per schema."""
        # Schema: full_name, id_number, birth_date, gender, relation_to_head, citizen_status
        data = {
            'full_name': self.full_name,
            'id_number': self.id_number,
            'birth_date': self.birth_date,
            'gender': self.gender,
            'relation_to_head': self.relation_to_head,
        }
        if self.citizen_status:
            data['citizen_status'] = self.citizen_status
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HouseholdMember':
        # Handle both old and new schema keys
        return cls(
            member_id=data.get('member_id', str(uuid.uuid4())), # Not in schema body but needed for app logic
            full_name=data.get('full_name', data.get('name', '')),
            id_number=data.get('id_number', data.get('citizen_id', '')),
            birth_date=data.get('birth_date', data.get('dob', '')),
            gender=data.get('gender', ''),
            relation_to_head=data.get('relation_to_head', data.get('relationship', '')),
            citizen_status=data.get('citizen_status'),
        )
    
    # Backward compat
    @property
    def name(self) -> str:
        return self.full_name
    
    @property
    def relationship(self) -> str:
        return self.relation_to_head
    
    @property
    def citizen_id(self) -> str:
        return self.id_number


@dataclass
class Residence:
    """Residence - matches Firestore residence/{uid}"""
    
    uid: str
    full_name: str = ""
    id_number: str = ""  # Schema: id_number
    birth_date: str = ""
    gender: str = ""
    
    # Address info
    permanent_address: str = ""
    current_address: str = ""
    temporary_address: Optional[str] = None
    temporary_start: Optional[str] = None
    temporary_end: Optional[str] = None
    
    # Details
    ethnicity: Optional[str] = None
    religion: Optional[str] = None
    nationality: Optional[str] = None
    hometown: Optional[str] = None
    citizen_status: Optional[str] = None
    
    # Household Head Info
    household_head_name: str = ""
    household_head_id: str = ""
    relation_to_head: str = ""
    
    # Old/Internal fields
    qr_payload: Optional[str] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)
    household_members: List[HouseholdMember] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Firestore document matching the Resident Information Data Guide."""
        # Main fields
        data = {
            'full_name': self.full_name,
            'id_number': self.id_number,
            'birth_date': self.birth_date,
            'gender': self.gender,
            'permanent_address': self.permanent_address,
            'current_address': self.current_address,
            'household_head_name': self.household_head_name,
            'household_head_id': self.household_head_id,
            'relation_to_head': self.relation_to_head,
            'updated_at': self.updated_at,
        }
        
        # Optional fields
        for key in ['ethnicity', 'religion', 'nationality', 'hometown', 'citizen_status',
                   'temporary_address', 'temporary_start', 'temporary_end', 'qr_payload']:
            val = getattr(self, key)
            if val:
                data[key] = val
                
        return data
    
        if members is None and 'household_members' in data:
            # Try to parse members from data if provided as list of dicts
            raw_members = data.get('household_members', [])
            members = []
            for m in raw_members:
                if isinstance(m, dict):
                    members.append(HouseholdMember.from_dict(m))
                elif isinstance(m, HouseholdMember):
                    members.append(m)
                    
        return cls(
            uid=data.get('uid', ''), # Internal, often document ID
            full_name=data.get('full_name', ''),
            id_number=data.get('id_number', data.get('citizen_id', '')),
            birth_date=data.get('birth_date', ''),
            gender=data.get('gender', ''),
            
            permanent_address=data.get('permanent_address', ''),
            current_address=data.get('current_address', ''),
            temporary_address=data.get('temporary_address'),
            temporary_start=data.get('temporary_start'),
            temporary_end=data.get('temporary_end'),
            
            ethnicity=data.get('ethnicity'),
            religion=data.get('religion'),
            nationality=data.get('nationality'),
            hometown=data.get('hometown'),
            citizen_status=data.get('citizen_status'),
            
            household_head_name=data.get('household_head_name', data.get('head_of_household', '')),
            household_head_id=data.get('household_head_id', ''),
            relation_to_head=data.get('relation_to_head', data.get('relationship_to_head', '')),
            
            qr_payload=data.get('qr_payload'),
            updated_at=data.get('updated_at', datetime.utcnow()),
            household_members=members or [],
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Residence':
        """Create from Firestore document."""
        # Handle household members if list of dicts
        members = []
        raw_members = data.get('household_members', [])
        for m in raw_members:
            if isinstance(m, dict):
                members.append(HouseholdMember.from_dict(m))
            elif isinstance(m, HouseholdMember):
                members.append(m)

        return cls(
            uid=data.get('uid', ''),
            full_name=data.get('full_name', ''),
            id_number=data.get('id_number', data.get('citizen_id', '')),
            birth_date=data.get('birth_date', ''),
            gender=data.get('gender', ''),
            
            permanent_address=data.get('permanent_address', ''),
            current_address=data.get('current_address', ''),
            temporary_address=data.get('temporary_address'),
            temporary_start=data.get('temporary_start'),
            temporary_end=data.get('temporary_end'),
            
            ethnicity=data.get('ethnicity'),
            religion=data.get('religion'),
            nationality=data.get('nationality'),
            hometown=data.get('hometown'),
            citizen_status=data.get('citizen_status'),
            
            household_head_name=data.get('household_head_name', data.get('head_of_household', '')),
            household_head_id=data.get('household_head_id', ''),
            relation_to_head=data.get('relation_to_head', data.get('relationship_to_head', '')),
            
            qr_payload=data.get('qr_payload'),
            updated_at=data.get('updated_at', datetime.utcnow()),
            household_members=members,
        )


# Helper factory functions (for backward compatibility)

def create_user_profile(uid: str, full_name: str = "", email: str = "", 
                       phone_number: str = "", citizen_id: str = "", 
                       passcode: str = DEFAULT_PASSCODE, **kwargs) -> UserProfile:
    """Create a new UserProfile instance."""
    return UserProfile(
        uid=uid,
        full_name=full_name,
        email=email,
        phone_number=phone_number,
        citizen_id=citizen_id,
        passcode=passcode or DEFAULT_PASSCODE,
        **kwargs
    )


def create_citizen_card(uid: str, full_name: str = "", citizen_id: str = "",
                       **kwargs) -> CitizenCard:
    """Create a new CitizenCard instance."""
    return CitizenCard(uid=uid, full_name=full_name, citizen_id=citizen_id, **kwargs)


def create_residence(uid: str, full_name: str = "", citizen_id: str = "",
                    permanent_address: str = "", current_address: str = "",
                    **kwargs) -> Residence:
    """Create a new Residence instance."""
    return Residence(
        uid=uid,
        full_name=full_name,
        citizen_id=citizen_id,
        permanent_address=permanent_address,
        current_address=current_address,
        **kwargs
    )


def create_household_member(full_name: str = "", relation_to_head: str = "",
                           member_id: str = None, **kwargs) -> HouseholdMember:
    """Create a new HouseholdMember instance."""
    return HouseholdMember(
        member_id=member_id or str(uuid.uuid4()),
        full_name=full_name,
        relation_to_head=relation_to_head,
        **kwargs
    )