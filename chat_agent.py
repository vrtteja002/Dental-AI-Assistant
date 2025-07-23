"""
LangChain-powered chat agent for DentalChat automation
"""
import uuid
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferWindowMemory

from models import ConversationHistory, ConversationTurn, PatientInfo
from data_extractor import PatientDataExtractor, SmartQuestionGenerator
from dentalchat_api import get_api_client
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DentalChatAgent:
    """
    Main conversational agent for dental patient intake
    """
    
    def __init__(self, use_mock_api: bool = True):
        # Initialize LangChain components
        self.llm = ChatOpenAI(
            api_key=Config.OPENAI_API_KEY,
            model=Config.OPENAI_MODEL,
            temperature=0.7
        )
        
        # Initialize memory for conversation context
        self.memory = ConversationBufferWindowMemory(
            k=10,  # Keep last 10 exchanges
            return_messages=True,
            memory_key="chat_history"
        )
        
        # Initialize specialized components
        self.data_extractor = PatientDataExtractor()
        self.question_generator = SmartQuestionGenerator()
        self.api_client = get_api_client(use_mock=use_mock_api)
        
        # Active conversations storage
        self.conversations: Dict[str, ConversationHistory] = {}
        
        # Create the main chat prompt
        self.chat_prompt = ChatPromptTemplate.from_messages([
            ("system", Config.SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        # Create the conversation chain
        self.chain = self.chat_prompt | self.llm
        
        logger.info("DentalChatAgent initialized successfully")
    
    def start_conversation(self) -> Tuple[str, str]:
        """
        Start a new conversation and return session ID and welcome message
        """
        session_id = str(uuid.uuid4())
        self.conversations[session_id] = ConversationHistory(session_id=session_id)
        
        # Add welcome message
        welcome_msg = """Hi! I'm Dr. Assistant, and I'm here to help you connect with local dentists. 

I'll ask you a few questions about your dental concern and then automatically create a post to get you help from qualified dentists in your area.

What's going on with your teeth or mouth today?"""
        
        self.conversations[session_id].add_turn("assistant", welcome_msg)
        
        logger.info(f"Started new conversation: {session_id}")
        return session_id, welcome_msg
    
    def process_message(self, session_id: str, user_message: str) -> Tuple[str, bool]:
        """
        Process user message and return response
        
        Args:
            session_id: Unique session identifier
            user_message: User's input message
            
        Returns:
            Tuple of (response_message, is_complete)
        """
        # Debug logging
        logger.info(f"Processing message for session {session_id[:8]}: {user_message[:50]}...")
        logger.info(f"Active conversations: {list(self.conversations.keys())}")
        
        if session_id not in self.conversations:
            logger.error(f"Session {session_id} not found in conversations")
            return "I'm sorry, but your session has expired. Please start a new conversation by clicking 'Start New Conversation'.", False
        
        conversation = self.conversations[session_id]
        
        try:
            # Add user message to conversation
            conversation.add_turn("user", user_message)
            
            # Extract information from the message
            old_info = conversation.patient_info
            conversation.patient_info = self.data_extractor.extract_from_message(
                user_message, conversation.patient_info
            )
            
            # Debug: Log what was extracted
            logger.info(f"Patient info completeness: {conversation.patient_info.is_complete()}")
            if not conversation.patient_info.is_complete():
                logger.info(f"Missing fields: {conversation.patient_info.missing_fields()}")
            
            # Check for completion signals
            completion_signals = [
                "that's all", "thats all", "that's it", "thank you", 
                "thanks", "nothing else", "no more questions",
                "all set", "ready to proceed", "create the post"
            ]
            
            user_message_lower = user_message.lower().strip()
            is_completion_signal = any(signal in user_message_lower for signal in completion_signals)
            
            # Check if we have all required information OR user signals completion
            if conversation.patient_info.is_complete() or (is_completion_signal and self._has_minimum_info(conversation.patient_info)):
                # Create the post and finish conversation
                response = self._create_post_and_finish(conversation)
                conversation.is_complete = True
                logger.info(f"Conversation {session_id[:8]} completed successfully")
                return response, True
            else:
                # Generate appropriate follow-up question
                response = self._generate_follow_up_response(conversation, user_message)
                conversation.add_turn("assistant", response)
                return response, False
                
        except Exception as e:
            logger.error(f"Error processing message for session {session_id}: {e}")
            error_response = "I apologize, but I'm having trouble processing your message. Could you please try rephrasing your concern?"
            conversation.add_turn("assistant", error_response)
            return error_response, False
    
    def _has_minimum_info(self, patient_info: PatientInfo) -> bool:
        """
        Check if we have minimum information to create a post
        """
        return (
            patient_info.problem_description and
            patient_info.patient_name and
            (patient_info.phone or patient_info.email) and
            patient_info.location
        )
    
    def _generate_follow_up_response(self, conversation: ConversationHistory, user_message: str) -> str:
        """
        Generate contextual follow-up response
        """
        try:
            # Get conversation context for the LLM
            context = self._build_conversation_context(conversation)
            
            # Use LangChain to generate empathetic response with follow-up question
            response = self.chain.invoke({
                "input": user_message,
                "chat_history": context["messages"]
            })
            
            # If the LLM response doesn't ask a specific question, add one
            response_text = response.content.strip()
            
            if not self._contains_question(response_text):
                follow_up = self.question_generator.generate_follow_up_question(
                    conversation.patient_info,
                    conversation.get_conversation_text()
                )
                response_text += f"\n\n{follow_up}"
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating follow-up: {e}")
            # Fallback to simple question generator
            return self.question_generator.generate_follow_up_question(
                conversation.patient_info,
                conversation.get_conversation_text()
            )
    
    def _create_post_and_finish(self, conversation: ConversationHistory) -> str:
        """
        Create DentalChat post and return completion message
        """
        try:
            # Create the post via API
            api_response = self.api_client.create_patient_post(conversation.patient_info)
            
            if api_response.success:
                # Get nearby dentists info
                dentist_response = self.api_client.get_nearby_dentists(
                    conversation.patient_info.location,
                    conversation.patient_info.emergency_status
                )
                
                # Build success message
                success_msg = f"""Perfect! I've created your dental post successfully. Here's what happens next:

✅ **Your post is now live** and local dentists can see it
📍 **Location**: {conversation.patient_info.location}
⚡ **Priority**: {'Emergency' if conversation.patient_info.emergency_status else 'Standard'}
📞 **Contact**: {conversation.patient_info.phone}

"""
                
                if dentist_response.success:
                    dentist_count = len(dentist_response.data.get('dentists', []))
                    success_msg += f"🔍 **{dentist_count} dentists** found in your area\n"
                
                success_msg += f"""
📧 **What's Next**:
• You'll receive email notifications when dentists respond
• Typical response time: {api_response.data.get('estimated_response_time', '1-2 hours')}
• Check your email and phone for updates

**Post ID**: {api_response.data.get('post_id', 'N/A')}

Is there anything else I can help you with regarding your dental concern?"""
                
                return success_msg
                
            else:
                # Handle API error
                error_msg = f"""I apologize, but I encountered an issue creating your post: {api_response.message}

Don't worry! I still have all your information:
• **Problem**: {conversation.patient_info.problem_description}
• **Pain Level**: {conversation.patient_info.pain_level}/10
• **Contact**: {conversation.patient_info.patient_name} - {conversation.patient_info.phone}

Would you like me to try creating the post again, or would you prefer to contact DentalChat support directly?"""
                
                return error_msg
                
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            return "I apologize, but I'm having trouble creating your post right now. Please try again in a moment or contact support if the issue persists."
    
    def _build_conversation_context(self, conversation: ConversationHistory) -> Dict:
        """
        Build context for LangChain conversation
        """
        messages = []
        
        # Add recent conversation turns
        for turn in conversation.turns[-6:]:  # Last 6 turns
            if turn.role == "user":
                messages.append(HumanMessage(content=turn.message))
            else:
                messages.append(AIMessage(content=turn.message))
        
        # Add current patient info context
        info_context = self._format_patient_info_context(conversation.patient_info)
        
        return {
            "messages": messages,
            "patient_info": info_context,
            "missing_fields": conversation.patient_info.missing_fields()
        }
    
    def _format_patient_info_context(self, patient_info: PatientInfo) -> str:
        """
        Format patient info for context
        """
        info_lines = []
        
        if patient_info.problem_description:
            info_lines.append(f"Problem: {patient_info.problem_description}")
        if patient_info.pain_level:
            info_lines.append(f"Pain Level: {patient_info.pain_level}/10")
        if patient_info.patient_name:
            info_lines.append(f"Name: {patient_info.patient_name}")
        if patient_info.location:
            info_lines.append(f"Location: {patient_info.location}")
        if patient_info.phone:
            info_lines.append(f"Phone: {patient_info.phone}")
        if patient_info.email:
            info_lines.append(f"Email: {patient_info.email}")
        
        return "\n".join(info_lines) if info_lines else "No information collected yet"
    
    def _contains_question(self, text: str) -> bool:
        """
        Check if text contains a question
        """
        return '?' in text or any(text.strip().lower().startswith(q) for q in [
            'what', 'when', 'where', 'who', 'why', 'how', 'could you', 'can you',
            'would you', 'do you', 'are you', 'is there', 'have you'
        ])
    
    def get_conversation_summary(self, session_id: str) -> Optional[Dict]:
        """
        Get summary of conversation and extracted information
        """
        if session_id not in self.conversations:
            return None
        
        conversation = self.conversations[session_id]
        
        return {
            "session_id": session_id,
            "created_at": conversation.created_at.isoformat(),
            "is_complete": conversation.is_complete,
            "total_turns": len(conversation.turns),
            "patient_info": conversation.patient_info.dict(),
            "missing_fields": conversation.patient_info.missing_fields(),
            "conversation_text": conversation.get_conversation_text()
        }
    
    def cleanup_conversation(self, session_id: str):
        """
        Clean up completed conversation
        """
        if session_id in self.conversations:
            del self.conversations[session_id]
            logger.info(f"Cleaned up conversation: {session_id}")

class ConversationManager:
    """
    Manages multiple conversation sessions
    """
    
    def __init__(self):
        self.agent = DentalChatAgent()
        self.active_sessions = set()
    
    def create_session(self) -> Tuple[str, str]:
        """Create new conversation session"""
        session_id, welcome_msg = self.agent.start_conversation()
        self.active_sessions.add(session_id)
        
        logger.info(f"Created session {session_id[:8]}, total active: {len(self.active_sessions)}")
        
        return session_id, welcome_msg
    
    def send_message(self, session_id: str, message: str) -> Tuple[str, bool]:
        """Send message to specific session"""
        # Check if session exists in active sessions
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id[:8]} not in active sessions: {list(self.active_sessions)}")
            
            # Try to recover if session exists in agent but not in active_sessions
            if session_id in self.agent.conversations:
                logger.info(f"Recovering session {session_id[:8]} - adding back to active sessions")
                self.active_sessions.add(session_id)
            else:
                return "I'm sorry, but your session has expired. Please start a new conversation by clicking 'Start New Conversation'.", False
        
        response, is_complete = self.agent.process_message(session_id, message)
        
        if is_complete:
            self.active_sessions.discard(session_id)
            logger.info(f"Completed session {session_id[:8]}")
        
        return response, is_complete
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get information about a session"""
        return self.agent.get_conversation_summary(session_id)
    
    def debug_sessions(self) -> Dict:
        """Get debug information about active sessions"""
        return {
            "active_sessions": list(self.active_sessions),
            "agent_conversations": list(self.agent.conversations.keys()),
            "total_active": len(self.active_sessions),
            "total_conversations": len(self.agent.conversations)
        }
    
    def ensure_session_active(self, session_id: str) -> bool:
        """Ensure session is active and accessible"""
        if session_id in self.active_sessions:
            return True
        
        # If session exists in agent but not in active sessions, recover it
        if session_id in self.agent.conversations:
            logger.info(f"Recovering session {session_id[:8]}")
            self.active_sessions.add(session_id)
            return True
        
        return False