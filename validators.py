"""
Validation functions for DentalChat AI Automation
"""
import re
import phonenumbers
from email_validator import validate_email, EmailNotValidError
from typing import Tuple, Optional
from config import Config

class ValidationError(Exception):
    """Custom validation error"""
    pass

class DataValidator:
    """Data validation utility class"""
    
    @staticmethod
    def validate_pain_level(pain_level: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Validate pain level input
        Returns: (is_valid, normalized_value, error_message)
        """
        try:
            level = int(pain_level)
            if 1 <= level <= 10:
                return True, level, None
            else:
                return False, None, "Pain level must be between 1 and 10"
        except ValueError:
            return False, None, "Pain level must be a number between 1 and 10"
    
    @staticmethod
    def validate_phone_number(phone: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate and format phone number
        Returns: (is_valid, formatted_number, error_message)
        """
        try:
            # Clean the input
            phone_clean = re.sub(r'[^\d+]', '', phone)
            
            # Parse with phonenumbers library
            parsed = phonenumbers.parse(phone_clean, "US")
            
            if phonenumbers.is_valid_number(parsed):
                formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
                return True, formatted, None
            else:
                return False, None, "Invalid phone number format"
                
        except phonenumbers.NumberParseException:
            return False, None, "Could not parse phone number. Please use format: (555) 123-4567"
    
    @staticmethod
    def validate_email_address(email: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate email address
        Returns: (is_valid, normalized_email, error_message)
        """
        try:
            # Use email-validator library
            valid = validate_email(email)
            return True, valid.email, None
        except EmailNotValidError as e:
            return False, None, f"Invalid email: {str(e)}"
    
    @staticmethod
    def validate_zip_code(zip_code: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate ZIP code
        Returns: (is_valid, normalized_zip, error_message)
        """
        # Remove spaces and convert to string
        zip_clean = str(zip_code).strip().replace(' ', '')
        
        # Check for 5-digit ZIP code
        if re.match(r'^\d{5}$', zip_clean):
            return True, zip_clean, None
        
        # Check for ZIP+4 format
        if re.match(r'^\d{5}-\d{4}$', zip_clean):
            return True, zip_clean[:5], None  # Return just the 5-digit part
        
        return False, None, "ZIP code must be 5 digits (e.g., 75201)"
    
    @staticmethod
    def validate_problem_description(description: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate problem description
        Returns: (is_valid, cleaned_description, error_message)
        """
        if not description or not description.strip():
            return False, None, "Problem description cannot be empty"
        
        cleaned = description.strip()
        
        if len(cleaned) < Config.MIN_PROBLEM_LENGTH:
            return False, None, f"Problem description must be at least {Config.MIN_PROBLEM_LENGTH} characters"
        
        if len(cleaned) > Config.MAX_PROBLEM_LENGTH:
            return False, None, f"Problem description must be less than {Config.MAX_PROBLEM_LENGTH} characters"
        
        return True, cleaned, None
    
    @staticmethod
    def validate_patient_name(name: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate patient name
        Returns: (is_valid, formatted_name, error_message)
        """
        if not name or not name.strip():
            return False, None, "Name cannot be empty"
        
        cleaned = name.strip()
        
        # Check for at least first and last name
        name_parts = cleaned.split()
        if len(name_parts) < 2:
            return False, None, "Please provide both first and last name"
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[A-Za-z\s\-']+$", cleaned):
            return False, None, "Name can only contain letters, spaces, hyphens, and apostrophes"
        
        # Title case formatting
        formatted = ' '.join(word.capitalize() for word in name_parts)
        
        return True, formatted, None
    
    @staticmethod
    def extract_pain_level_from_text(text: str) -> Optional[int]:
        """
        Extract pain level from natural language text
        """
        text_lower = text.lower()
        
        # Look for explicit numbers with pain context
        pain_patterns = [
            r'pain.*?(\d{1,2})',
            r'(\d{1,2}).*?pain',
            r'(\d{1,2}).*?out.*?of.*?10',
            r'level.*?(\d{1,2})',
            r'scale.*?(\d{1,2})'
        ]
        
        for pattern in pain_patterns:
            match = re.search(pattern, text_lower)
            if match:
                level = int(match.group(1))
                if 1 <= level <= 10:
                    return level
        
        # Look for descriptive pain levels
        pain_descriptions = {
            'mild': 2,
            'slight': 2,
            'moderate': 5,
            'severe': 8,
            'extreme': 9,
            'excruciating': 10,
            'unbearable': 10,
            'terrible': 8,
            'awful': 7,
            'horrible': 8
        }
        
        for description, level in pain_descriptions.items():
            if description in text_lower:
                return level
        
        return None
    
    @staticmethod
    def detect_emergency_keywords(text: str) -> bool:
        """
        Detect emergency keywords in text
        """
        emergency_keywords = [
            'emergency', 'urgent', 'severe', 'excruciating', 'unbearable',
            'swollen', 'swelling', 'infection', 'abscess', 'bleeding',
            'knocked out', 'broken', 'fractured', 'trauma', 'accident',
            'can\'t eat', 'can\'t sleep', 'getting worse', 'spreading'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in emergency_keywords)
    
    @staticmethod
    def extract_time_frame(text: str) -> Optional[str]:
        """
        Extract when symptoms started from text
        """
        time_patterns = [
            r'(\d+)\s*(day|week|month|year)s?\s*ago',
            r'(yesterday|today|this morning|last night)',
            r'since\s+(yesterday|today|this morning|last night)',
            r'for\s+(\d+)\s*(day|week|month|year)s?',
            r'started\s+(\d+)\s*(day|week|month|year)s?\s*ago'
        ]
        
        text_lower = text.lower()
        for pattern in time_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(0)
        
        return None