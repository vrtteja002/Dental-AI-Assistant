"""
Data models for DentalChat AI Automation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import re

class PatientInfo(BaseModel):
    """Patient information model"""
    problem_description: Optional[str] = None
    pain_level: Optional[int] = Field(None, ge=1, le=10)
    emergency_status: Optional[bool] = None
    location: Optional[str] = None
    patient_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    started_when: Optional[str] = None
    symptoms: Optional[List[str]] = []
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is None:
            return v
        phone_str = str(v)
        digits_only = re.sub(r'[^\d]', '', phone_str)
        
        if len(digits_only) == 10:
            return f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
        elif len(digits_only) == 11 and digits_only[0] == '1':
            return f"({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
        else:
            return phone_str
    
    @validator('email')
    def validate_email(cls, v):
        if v is None:
            return v
        email_str = str(v)
        if '@' in email_str and '.' in email_str.split('@')[-1]:
            return email_str.lower()
        else:
            return email_str
    
    @validator('location')
    def validate_location(cls, v):
        if v is None:
            return v
        location_str = str(v).strip()
        
        # Accept any location string that's reasonable
        if len(location_str) >= 2:
            return location_str
        else:
            return str(v)
    
    def is_complete(self) -> bool:
        """Check if all required fields are present"""
        required_fields = ['problem_description', 'patient_name', 'location']
        has_contact = self.phone is not None or self.email is not None
        
        basic_complete = all(getattr(self, field) is not None for field in required_fields)
        return basic_complete and has_contact
    
    def missing_fields(self) -> List[str]:
        """Get list of missing required fields"""
        missing = []
        
        if not self.problem_description:
            missing.append('dental problem description')
        if not self.patient_name:
            missing.append('your name')
        if not self.location:
            missing.append('ZIP code or location')
        if not self.phone and not self.email:
            missing.append('phone number or email address')
        
        return missing

class ConversationTurn(BaseModel):
    """Single conversation turn"""
    timestamp: datetime = Field(default_factory=datetime.now)
    role: str  # 'user' or 'assistant'
    message: str
    extracted_info: Optional[dict] = None

class ConversationHistory(BaseModel):
    """Complete conversation history"""
    session_id: str
    turns: List[ConversationTurn] = []
    patient_info: PatientInfo = Field(default_factory=PatientInfo)
    is_complete: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    
    def add_turn(self, role: str, message: str, extracted_info: dict = None):
        """Add a conversation turn"""
        turn = ConversationTurn(
            role=role, 
            message=message, 
            extracted_info=extracted_info
        )
        self.turns.append(turn)
    
    def get_conversation_text(self) -> str:
        """Get full conversation as text"""
        text = ""
        for turn in self.turns:
            text += f"{turn.role.title()}: {turn.message}\n"
        return text

class DentalChatPost(BaseModel):
    """DentalChat post submission model"""
    title: str
    problem_description: str
    pain_level: int = Field(ge=1, le=10)
    emergency: bool
    location: str
    patient_name: str
    phone: str
    email: str
    started_when: Optional[str] = None
    symptoms: Optional[List[str]] = []
    
    @classmethod
    def from_patient_info(cls, patient_info: PatientInfo):
        """Create post from patient info"""
        # Generate title from problem description
        title = patient_info.problem_description[:50] + "..." if len(patient_info.problem_description) > 50 else patient_info.problem_description
        
        return cls(
            title=title,
            problem_description=patient_info.problem_description,
            pain_level=patient_info.pain_level or 5,  # Default to moderate if not provided
            emergency=patient_info.emergency_status or (patient_info.pain_level or 0) >= 7,
            location=patient_info.location,
            patient_name=patient_info.patient_name,
            phone=patient_info.phone or "",
            email=patient_info.email or "",
            started_when=patient_info.started_when,
            symptoms=patient_info.symptoms or []
        )

class APIResponse(BaseModel):
    """Standard API response model"""
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None