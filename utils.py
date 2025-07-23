"""
Utility functions for DentalChat AI Automation
"""
import re
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

class TextProcessor:
    """Text processing utilities"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text input"""
        if not text:
            return ""
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters that might cause issues
        cleaned = re.sub(r'[^\w\s\-\.\,\!\?\(\)\'\"@]', '', cleaned)
        
        return cleaned
    
    @staticmethod
    def extract_numbers(text: str) -> List[int]:
        """Extract all numbers from text"""
        return [int(match) for match in re.findall(r'\d+', text)]
    
    @staticmethod
    def extract_email(text: str) -> Optional[str]:
        """Extract email address from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    @staticmethod
    def extract_phone(text: str) -> Optional[str]:
        """Extract phone number from text"""
        # Remove all non-digit characters first
        digits = re.sub(r'[^\d]', '', text)
        
        # Check for valid phone number patterns
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        
        return None
    
    @staticmethod
    def normalize_zip_code(text: str) -> Optional[str]:
        """Extract and normalize ZIP code"""
        # Look for 5-digit ZIP codes
        zip_pattern = r'\b\d{5}\b'
        match = re.search(zip_pattern, text)
        return match.group(0) if match else None

class SessionManager:
    """Manage conversation sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = {
            'created_at': datetime.now(timezone.utc),
            'user_id': user_id,
            'last_activity': datetime.now(timezone.utc),
            'metadata': {}
        }
        
        return session_id
    
    def update_session_activity(self, session_id: str):
        """Update last activity timestamp"""
        if session_id in self.sessions:
            self.sessions[session_id]['last_activity'] = datetime.now(timezone.utc)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        return self.sessions.get(session_id)
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """Remove expired sessions"""
        cutoff_time = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
        
        expired_sessions = [
            session_id for session_id, session_data in self.sessions.items()
            if session_data['last_activity'].timestamp() < cutoff_time
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

class ResponseFormatter:
    """Format responses for different output types"""
    
    @staticmethod
    def format_patient_summary(patient_info: Dict[str, Any]) -> str:
        """Format patient information summary"""
        lines = ["**Patient Information Summary:**"]
        
        if patient_info.get('patient_name'):
            lines.append(f"• **Name**: {patient_info['patient_name']}")
        
        if patient_info.get('problem_description'):
            lines.append(f"• **Issue**: {patient_info['problem_description']}")
        
        if patient_info.get('pain_level'):
            pain_emoji = "🔴" if patient_info['pain_level'] >= 7 else "🟡" if patient_info['pain_level'] >= 4 else "🟢"
            lines.append(f"• **Pain Level**: {patient_info['pain_level']}/10 {pain_emoji}")
        
        if patient_info.get('location'):
            lines.append(f"• **Location**: {patient_info['location']}")
        
        if patient_info.get('phone'):
            lines.append(f"• **Phone**: {patient_info['phone']}")
        
        if patient_info.get('email'):
            lines.append(f"• **Email**: {patient_info['email']}")
        
        if patient_info.get('started_when'):
            lines.append(f"• **Started**: {patient_info['started_when']}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_error_message(error_type: str, details: str = "") -> str:
        """Format error messages consistently"""
        error_messages = {
            'validation': "I noticed there might be an issue with the information provided.",
            'api_error': "I'm having trouble connecting to our system right now.",
            'incomplete_data': "I need a bit more information to help you.",
            'network_error': "There seems to be a connection issue.",
            'unknown': "Something unexpected happened."
        }
        
        base_message = error_messages.get(error_type, error_messages['unknown'])
        
        if details:
            return f"{base_message} {details}"
        
        return f"{base_message} Please try again or let me know if you need help."
    
    @staticmethod
    def format_success_message(post_id: str, estimated_time: str = "1-2 hours") -> str:
        """Format success message for post creation"""
        return f"""🎉 **Great! Your dental post has been created successfully!**

**Post ID**: {post_id}
**Estimated Response Time**: {estimated_time}

**What happens next:**
1. Local dentists will review your post
2. You'll receive notifications when they respond  
3. You can then choose which dentist to contact

**Important**: Keep your phone and email handy for dentist responses!

Is there anything else I can help you with?"""

class DataValidator:
    """Additional validation utilities"""
    
    @staticmethod
    def is_valid_session_id(session_id: str) -> bool:
        """Validate session ID format"""
        try:
            uuid.UUID(session_id)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def sanitize_input(user_input: str, max_length: int = 1000) -> str:
        """Sanitize user input"""
        if not user_input:
            return ""
        
        # Limit length
        sanitized = user_input[:max_length]
        
        # Remove potentially harmful characters
        sanitized = re.sub(r'[<>{}\\]', '', sanitized)
        
        # Clean whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized.strip())
        
        return sanitized
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """Check for missing required fields"""
        missing = []
        for field in required_fields:
            if field not in data or not data[field]:
                missing.append(field)
        return missing

class LoggingUtils:
    """Logging utilities"""
    
    @staticmethod
    def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
        """Setup logging configuration"""
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        handlers = [logging.StreamHandler()]
        if log_file:
            handlers.append(logging.FileHandler(log_file))
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=handlers
        )
    
    @staticmethod
    def log_conversation_turn(session_id: str, role: str, message: str):
        """Log conversation turn for monitoring"""
        logger.info(f"Session {session_id[:8]} - {role}: {message[:100]}...")
    
    @staticmethod
    def log_api_call(endpoint: str, success: bool, response_time: float):
        """Log API call metrics"""
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"API {endpoint} - {status} - {response_time:.2f}s")

class PerformanceMonitor:
    """Monitor application performance"""
    
    def __init__(self):
        self.metrics = {
            'conversations_started': 0,
            'conversations_completed': 0,
            'posts_created': 0,
            'api_calls': 0,
            'errors': 0
        }
    
    def increment_metric(self, metric_name: str):
        """Increment a performance metric"""
        if metric_name in self.metrics:
            self.metrics[metric_name] += 1
    
    def get_metrics(self) -> Dict[str, int]:
        """Get current metrics"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """Reset all metrics"""
        for key in self.metrics:
            self.metrics[key] = 0

# Global instances
session_manager = SessionManager()
performance_monitor = PerformanceMonitor()