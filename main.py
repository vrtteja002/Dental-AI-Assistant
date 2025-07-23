"""
Main application for DentalChat AI Automation - Simple Version
"""
import os
import sys
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat_agent import ConversationManager
from models import PatientInfo
from utils import LoggingUtils, performance_monitor
from config import Config

# Setup logging
LoggingUtils.setup_logging(level="INFO")

class DentalChatApp:
    """Simple DentalChat application"""
    
    def __init__(self):
        # Use session state to persist conversation manager
        if 'conversation_manager' not in st.session_state:
            st.session_state.conversation_manager = ConversationManager()
        self.conversation_manager = st.session_state.conversation_manager
        self.setup_page()
    
    def setup_page(self):
        """Basic page setup"""
        st.set_page_config(
            page_title="DentalChat AI Assistant",
            page_icon="🦷",
            layout="centered"
        )
    
    def run(self):
        """Run the application"""
        # Simple header
        st.title("🦷 DentalChat AI Assistant")
        st.write("Automated patient intake for dental offices")
        
        # Initialize session state
        if 'session_id' not in st.session_state:
            st.session_state.session_id = None
            st.session_state.messages = []
            st.session_state.conversation_complete = False
        
        # Start conversation button
        if not st.session_state.session_id:
            st.markdown("### Welcome! 👋")
            st.write("I'll help you create a dental consultation post through a simple conversation.")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚀 Start New Conversation", use_container_width=True):
                    self.start_conversation()
        else:
            # Display conversation
            self.show_conversation()
            
            # Input or completion message
            if not st.session_state.conversation_complete:
                self.handle_input()
            else:
                st.success("✅ Conversation completed! Your dental post has been created.")
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("🔄 Start Another Conversation", use_container_width=True):
                        self.start_conversation()
        
        # Simple sidebar
        with st.sidebar:
            st.header("Stats")
            metrics = performance_monitor.get_metrics()
            st.write(f"Conversations: {metrics['conversations_started']}")
            st.write(f"Completed: {metrics['conversations_completed']}")
            
            if st.button("Reset"):
                st.session_state.clear()
                st.rerun()
    
    def start_conversation(self):
        """Start new conversation"""
        try:
            with st.spinner('Starting conversation...'):
                session_id, welcome_msg = self.conversation_manager.create_session()
                st.session_state.session_id = session_id
                st.session_state.messages = [{"role": "assistant", "content": welcome_msg}]
                st.session_state.conversation_complete = False
                performance_monitor.increment_metric('conversations_started')
            
            st.success("✅ Conversation started!")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error starting conversation: {str(e)}")
    
    def show_conversation(self):
        """Display conversation messages"""
        st.subheader("💬 Conversation")
        
        if not st.session_state.messages:
            st.info("👋 No messages yet. Start the conversation!")
            return
            
        # Display messages
        for message in st.session_state.messages:
            if message["role"] == "user":
                # User message
                st.write("")  # spacing
                col1, col2 = st.columns([1, 3])
                with col2:
                    st.info(f"**You:** {message['content']}")
            else:
                # Assistant message
                st.write("")  # spacing
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.success(f"**🦷 Dr. Assistant:** {message['content']}")
    
    def handle_input(self):
        """Handle user input"""
        st.markdown("---")
        
        with st.form(key="chat_form", clear_on_submit=True):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                user_input = st.text_input(
                    "Your message:", 
                    placeholder="Tell me about your dental concern...",
                    label_visibility="collapsed"
                )
            
            with col2:
                submitted = st.form_submit_button("Send", use_container_width=True)
        
        if submitted and user_input.strip():
            if not st.session_state.get('session_id'):
                st.error("No active session. Please start a new conversation.")
                return
            
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            try:
                # Get AI response
                with st.spinner('Thinking...'):
                    response, is_complete = self.conversation_manager.send_message(
                        st.session_state.session_id, 
                        user_input
                    )
                
                # Add assistant response
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Check if complete
                if is_complete:
                    st.session_state.conversation_complete = True
                    performance_monitor.increment_metric('conversations_completed')
                    performance_monitor.increment_metric('posts_created')
                
                performance_monitor.increment_metric('api_calls')
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                performance_monitor.increment_metric('errors')

def main():
    """Main entry point"""
    try:
        # Check for API key
        if not Config.OPENAI_API_KEY:
            st.error("❌ OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
            st.stop()
        
        # Run app
        app = DentalChatApp()
        app.run()
        
    except Exception as e:
        st.error(f"Application error: {str(e)}")

if __name__ == "__main__":
    main()