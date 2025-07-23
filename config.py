"""
Configuration settings for DentalChat AI Automation
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = "gpt-4-turbo-preview"
    
    # DentalChat API Configuration
    DENTALCHAT_BASE_URL = "https://dentalchat.com/api"
    DENTALCHAT_API_KEY = os.getenv("DENTALCHAT_API_KEY", "demo_key")
    
    # Application Settings
    MAX_CONVERSATION_TURNS = 10
    PAIN_EMERGENCY_THRESHOLD = 7
    
    # Validation Settings
    MIN_PROBLEM_LENGTH = 10
    MAX_PROBLEM_LENGTH = 500
    
    # System Prompts
    SYSTEM_PROMPT = """
    You are Dr. Assistant, an AI helper for DentalChat.com. Your role is to:
    
    1. Collect patient dental information through natural conversation
    2. Assess urgency and pain levels empathetically
    3. Gather location for local dentist matching
    4. Be professional, caring, and efficient
    
    Required Information to Collect:
    - Dental problem description (detailed)
    - Pain level (1-10 scale)
    - When symptoms started
    - Emergency status assessment
    - Patient location (ZIP code)
    - Contact information (name, phone, email)
    
    Guidelines:
    - Ask ONE question at a time
    - Be empathetic for pain/discomfort
    - Escalate pain levels 7+ as emergency
    - Confirm information before proceeding
    - Keep responses concise and helpful
    """
    
    EXTRACTION_PROMPT = """
    Extract structured information from this dental conversation.
    
    Text: {conversation_text}
    
    Extract the following fields if mentioned:
    - problem_description: Detailed description of dental issue
    - pain_level: Number from 1-10 if mentioned
    - emergency_status: True if urgent/emergency indicators
    - location: ZIP code or city/state
    - patient_name: Full name if provided
    - phone: Phone number if provided
    - email: Email address if provided
    - started_when: When symptoms began
    - symptoms: List of specific symptoms mentioned
    
    Return as JSON. Use null for missing information.
    """