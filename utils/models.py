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
    
    # Optional fields
    avatar_url: Optional[str] = None
    address: Optional[str] = None
    dob: Optional[str] = None  # Keep as string for simplicity
    gender: Optional[str] = None
    nationality: Optional[str] = None
    permanent_address: Optional[str] = None
    temporary_address: Optional[str] = None
    current_address: Optional[str] = None
    identity_level: int = 2
    
    # QR payloads - fallback to uid if empty
    qr_home: Optional[str] = None
    qr_card: Optional[str] = None
    qr_id_detail: Optional[str] = None
    qr_residence: Optional[str] = None
    
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
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }
        
        # Add optional fields if set
        for key in ['avatar_url', 'address', 'dob', 'gender', 'nationality',
                   'permanent_address', 'temporary_address', 'current_address',
                   'qr_home', 'qr_card', 'qr_id_detail', 'qr_residence']:
            val = getattr(self, key)
            if val:
                data[key] = val
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Create from Firestore document."""
        return cls(
            uid=data.get('uid', ''),
            full_name=data.get('full_name', data.get('name', '')),  # Backwards compat
            email=data.get('email', ''),
            phone_number=data.get('phone_number', data.get('phone', '')),
            citizen_id=data.get('citizen_id', ''),
            passcode=data.get('passcode', DEFAULT_PASSCODE),
            avatar_url=data.get('avatar_url'),
            address=data.get('address'),
            dob=data.get('dob') if isinstance(data.get('dob'), str) else None,
            gender=data.get('gender'),
            nationality=data.get('nationality'),
            permanent_address=data.get('permanent_address'),
            temporary_address=data.get('temporary_address'),
            current_address=data.get('current_address'),
            identity_level=data.get('identity_level', 2),
            qr_home=data.get('qr_home'),
            qr_card=data.get('qr_card'),
            qr_id_detail=data.get('qr_id_detail'),
            qr_residence=data.get('qr_residence'),
            created_at=data.get('created_at', datetime.utcnow()),
            updated_at=data.get('updated_at', datetime.utcnow()),
        )
    
    # Backward compat properties
    @property
    def name(self) -> str:
        return self.full_name
    
    @property
    def phone(self) -> str:
        return self.phone_number


@dataclass
class CitizenCard:
    """Citizen card - matches Firestore citizen_cards/{uid}"""
    
    uid: str
    full_name: str = ""
    citizen_id: str = ""
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    
    # Location info
    birthplace: Optional[str] = None
    birth_registration_place: Optional[str] = None
    hometown: Optional[str] = None
    permanent_address: Optional[str] = None
    temporary_address: Optional[str] = None
    current_address: Optional[str] = None
    
    # Additional info
    ethnicity: Optional[str] = None
    religion: Optional[str] = None
    issue_date: Optional[str] = None
    issue_place: Optional[str] = None
    identifying_marks: Optional[str] = None
    blood_type: Optional[str] = None
    profession: Optional[str] = None
    
    qr_payload: Optional[str] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Firestore document."""
        data = {'uid': self.uid, 'updated_at': self.updated_at}
        
        for key in ['full_name', 'citizen_id', 'date_of_birth', 'gender', 'nationality',
                   'birthplace', 'birth_registration_place', 'hometown', 
                   'permanent_address', 'temporary_address', 'current_address',
                   'ethnicity', 'religion', 'issue_date', 'issue_place',
                   'identifying_marks', 'blood_type', 'profession', 'qr_payload']:
            val = getattr(self, key)
            if val:
                data[key] = val
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CitizenCard':
        """Create from Firestore document."""
        return cls(
            uid=data.get('uid', ''),
            full_name=data.get('full_name', ''),
            citizen_id=data.get('citizen_id', ''),
            date_of_birth=data.get('date_of_birth'),
            gender=data.get('gender'),
            nationality=data.get('nationality'),
            birthplace=data.get('birthplace', data.get('place_of_birth')),
            birth_registration_place=data.get('birth_registration_place'),
            hometown=data.get('hometown'),
            permanent_address=data.get('permanent_address'),
            temporary_address=data.get('temporary_address'),
            current_address=data.get('current_address'),
            ethnicity=data.get('ethnicity'),
            religion=data.get('religion'),
            issue_date=data.get('issue_date'),
            issue_place=data.get('issue_place', data.get('issuing_authority')),
            identifying_marks=data.get('identifying_marks', data.get('personal_identification')),
            blood_type=data.get('blood_type'),
            profession=data.get('profession'),
            qr_payload=data.get('qr_payload'),
            updated_at=data.get('updated_at', datetime.utcnow()),
        )


@dataclass
class HouseholdMember:
    """Household member - matches residence/{uid}/household_members/{id}"""
    
    member_id: str = ""
    full_name: str = ""
    id_number: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    relation_to_head: str = ""
    citizen_status: Optional[str] = None
    
    def __post_init__(self):
        if not self.member_id:
            self.member_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            'member_id': self.member_id,
            'full_name': self.full_name,
            'relation_to_head': self.relation_to_head,
        }
        for key in ['id_number', 'birth_date', 'gender', 'citizen_status']:
            val = getattr(self, key)
            if val:
                data[key] = val
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HouseholdMember':
        return cls(
            member_id=data.get('member_id', str(uuid.uuid4())),
            full_name=data.get('full_name', data.get('name', '')),
            id_number=data.get('id_number', data.get('citizen_id')),
            birth_date=data.get('birth_date', data.get('dob')),
            gender=data.get('gender'),
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


@dataclass
class Residence:
    """Residence - matches Firestore residence/{uid}"""
    
    uid: str
    full_name: str = ""
    citizen_id: str = ""
    permanent_address: str = ""
    current_address: str = ""
    
    residence_type: Optional[str] = None
    household_id: Optional[str] = None
    head_of_household: Optional[str] = None
    relationship_to_head: Optional[str] = None
    qr_payload: Optional[str] = None
    
    updated_at: datetime = field(default_factory=datetime.utcnow)
    household_members: List[HouseholdMember] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            'uid': self.uid,
            'full_name': self.full_name,
            'citizen_id': self.citizen_id,
            'permanent_address': self.permanent_address,
            'current_address': self.current_address,
            'updated_at': self.updated_at,
        }
        for key in ['residence_type', 'household_id', 'head_of_household',
                   'relationship_to_head', 'qr_payload']:
            val = getattr(self, key)
            if val:
                data[key] = val
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], members: List[HouseholdMember] = None) -> 'Residence':
        return cls(
            uid=data.get('uid', ''),
            full_name=data.get('full_name', ''),
            citizen_id=data.get('citizen_id', ''),
            permanent_address=data.get('permanent_address', ''),
            current_address=data.get('current_address', ''),
            residence_type=data.get('residence_type'),
            household_id=data.get('household_id'),
            head_of_household=data.get('head_of_household'),
            relationship_to_head=data.get('relationship_to_head'),
            qr_payload=data.get('qr_payload'),
            updated_at=data.get('updated_at', datetime.utcnow()),
            household_members=members or [],
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