"""
Data extraction module using LangChain and OpenAI
"""
import json
import re
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from models import PatientInfo
from validators import DataValidator
from config import Config

class PatientDataExtractor:
    """Extract patient information from conversations using LangChain and OpenAI"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=Config.OPENAI_API_KEY,
            model=Config.OPENAI_MODEL,
            temperature=0.1  # Low temperature for consistent extraction
        )
        
        self.extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert medical information extractor. 
            Extract structured information from dental conversations.
            
            Always return valid JSON with these fields:
            {
                "problem_description": "detailed description of dental issue",
                "pain_level": null or number 1-10,
                "emergency_status": null or boolean,
                "location": "ZIP code or city, state",
                "patient_name": "full name if provided",
                "phone": "phone number if provided", 
                "email": "email address if provided",
                "started_when": "when symptoms began",
                "symptoms": ["list", "of", "symptoms"]
            }
            
            Use null for missing information. Be precise and accurate."""),
            ("human", "Extract information from this conversation:\n\n{conversation_text}")
        ])
    
    def extract_from_message(self, message: str, current_info: PatientInfo) -> PatientInfo:
        """
        Extract information from a single message and update current info
        """
        try:
            # Create conversation context including the current message
            conversation_context = f"""
Previous information collected:
- Problem: {current_info.problem_description or 'Not provided'}
- Pain level: {current_info.pain_level or 'Not provided'}
- Name: {current_info.patient_name or 'Not provided'}
- Phone: {current_info.phone or 'Not provided'}
- Email: {current_info.email or 'Not provided'}
- Location: {current_info.location or 'Not provided'}
- Started when: {current_info.started_when or 'Not provided'}

New message: {message}
"""
            
            # Use LangChain to extract information
            chain = self.extraction_prompt | self.llm
            response = chain.invoke({"conversation_text": conversation_context})
            
            # Parse the JSON response
            extracted_data = self._parse_extraction_response(response.content)
            
            # Update current patient info with extracted data
            updated_info = self._merge_patient_info(current_info, extracted_data)
            
            # Apply additional validation and enhancement
            enhanced_info = self._enhance_extracted_info(updated_info, message)
            
            # Debug logging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Extracted from '{message[:50]}...': {extracted_data}")
            logger.info(f"Updated info complete: {enhanced_info.is_complete()}")
            logger.info(f"Missing fields: {enhanced_info.missing_fields()}")
            
            return enhanced_info
            
        except Exception as e:
            print(f"Error in extraction: {e}")
            return current_info
    
    def extract_from_conversation(self, conversation_text: str) -> PatientInfo:
        """
        Extract information from full conversation history
        """
        try:
            chain = self.extraction_prompt | self.llm
            response = chain.invoke({"conversation_text": conversation_text})
            
            extracted_data = self._parse_extraction_response(response.content)
            patient_info = PatientInfo(**extracted_data)
            
            # Apply additional enhancements
            enhanced_info = self._enhance_extracted_info(patient_info, conversation_text)
            
            return enhanced_info
            
        except Exception as e:
            print(f"Error in conversation extraction: {e}")
            return PatientInfo()
    
    def _parse_extraction_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse and clean the JSON response from OpenAI
        """
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # If no JSON found, try to parse the whole response
                return json.loads(response_text)
                
        except json.JSONDecodeError:
            print(f"Failed to parse JSON: {response_text}")
            return {}
    
    def _merge_patient_info(self, current: PatientInfo, extracted: Dict[str, Any]) -> PatientInfo:
        """
        Merge extracted data with current patient info
        """
        # Create a copy of current info
        current_dict = current.dict()
        
        # Update with extracted data (only if not null and not empty)
        for key, value in extracted.items():
            if value is not None and value != "" and value != "null":
                if key in current_dict:
                    # For lists, merge instead of replace
                    if key == "symptoms" and isinstance(value, list):
                        existing_symptoms = current_dict.get("symptoms", []) or []
                        current_dict[key] = list(set(existing_symptoms + value))
                    # Don't overwrite existing valid data with partial data
                    elif current_dict[key] is None or current_dict[key] == "":
                        current_dict[key] = value
                    # Special handling for contact info that might be in one message
                    elif key in ["patient_name", "phone", "email"] and not current_dict[key]:
                        current_dict[key] = value
        
        try:
            return PatientInfo(**current_dict)
        except Exception as e:
            print(f"Error creating PatientInfo: {e}")
            return current
    
    def _enhance_extracted_info(self, patient_info: PatientInfo, text: str) -> PatientInfo:
        """
        Apply additional enhancements to extracted information
        """
        info_dict = patient_info.dict()
        
        # Extract pain level from text if not already set
        if not info_dict.get("pain_level"):
            pain_level = DataValidator.extract_pain_level_from_text(text)
            if pain_level:
                info_dict["pain_level"] = pain_level
        
        # Detect emergency status if not set
        if info_dict.get("emergency_status") is None:
            is_emergency = (
                DataValidator.detect_emergency_keywords(text) or
                (info_dict.get("pain_level", 0) >= Config.PAIN_EMERGENCY_THRESHOLD)
            )
            info_dict["emergency_status"] = is_emergency
        
        # Extract time frame if not set
        if not info_dict.get("started_when"):
            time_frame = DataValidator.extract_time_frame(text)
            if time_frame:
                info_dict["started_when"] = time_frame
        
        # Enhanced contact info extraction for consolidated messages
        if not info_dict.get("phone"):
            from utils import TextProcessor
            phone = TextProcessor.extract_phone(text)
            if phone:
                info_dict["phone"] = phone
        
        if not info_dict.get("email"):
            from utils import TextProcessor
            email = TextProcessor.extract_email(text)
            if email:
                info_dict["email"] = email
        
        # Extract name from contact info format like "John Smith, email, phone"
        if not info_dict.get("patient_name"):
            # Look for name patterns at the beginning of contact info
            import re
            name_pattern = r'^([A-Za-z\s]+)(?=,|\s*[a-zA-Z0-9._%+-]+@)'
            match = re.search(name_pattern, text.strip())
            if match:
                potential_name = match.group(1).strip()
                if len(potential_name.split()) >= 2:  # At least first and last name
                    info_dict["patient_name"] = potential_name
        
        # Validate and format phone number
        if info_dict.get("phone"):
            is_valid, formatted, error = DataValidator.validate_phone_number(info_dict["phone"])
            if is_valid:
                info_dict["phone"] = formatted
            else:
                # Keep original if validation fails, might be a different format
                pass
        
        # Validate and format email
        if info_dict.get("email"):
            is_valid, formatted, error = DataValidator.validate_email_address(info_dict["email"])
            if is_valid:
                info_dict["email"] = formatted
            else:
                # Keep original if validation fails
                pass
        
        # Validate ZIP code
        if info_dict.get("location"):
            is_valid, formatted, error = DataValidator.validate_zip_code(info_dict["location"])
            if is_valid:
                info_dict["location"] = formatted
        
        try:
            return PatientInfo(**info_dict)
        except Exception as e:
            print(f"Error in enhancement: {e}")
            return patient_info

class SmartQuestionGenerator:
    """Generate smart follow-up questions based on missing information"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=Config.OPENAI_API_KEY,
            model=Config.OPENAI_MODEL,
            temperature=0.7  # Higher temperature for more natural questions
        )
    
    def generate_follow_up_question(self, patient_info: PatientInfo, conversation_history: str) -> str:
        """
        Generate appropriate follow-up question based on missing information
        """
        missing_fields = patient_info.missing_fields()
        
        if not missing_fields:
            return "I have all the information I need. Let me create your post now."
        
        # Create context for question generation
        context = {
            "missing_fields": missing_fields,
            "current_info": patient_info.dict(),
            "conversation_history": conversation_history[-500:]  # Last 500 chars
        }
        
        prompt = f"""
        Based on the conversation history and missing information, generate ONE natural, 
        empathetic follow-up question to gather the next most important piece of information.
        
        Missing information: {', '.join(missing_fields)}
        
        Current conversation context:
        {conversation_history[-300:]}
        
        Guidelines:
        - Ask for the most critical missing information first
        - Be empathetic and professional
        - Keep questions simple and clear
        - If asking about pain, acknowledge their discomfort
        - Only ask ONE question at a time
        
        Generate just the question, no other text:
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            print(f"Error generating question: {e}")
            return self._get_default_question(missing_fields[0])
    
    def _get_default_question(self, missing_field: str) -> str:
        """
        Get default question for missing field
        """
        default_questions = {
            "dental problem description": "Could you describe what's happening with your teeth or mouth?",
            "pain level (1-10)": "On a scale of 1-10, how would you rate your pain level?",
            "ZIP code or location": "What's your ZIP code so I can find dentists in your area?",
            "your name": "What's your name so dentists can reach out to you?",
            "phone number": "What's the best phone number to reach you?",
            "email address": "What's your email address for appointment confirmations?"
        }
        
        return default_questions.get(missing_field, "Could you provide more information about your dental concern?")