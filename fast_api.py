# """
# FastAPI application for DentalChat AI Automation
# Alternative web interface for the chatbot
# """
# from fastapi import FastAPI, HTTPException, BackgroundTasks
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import HTMLResponse, JSONResponse
# from fastapi.staticfiles import StaticFiles
# from pydantic import BaseModel
# from typing import Dict, List, Optional
# import uvicorn
# import logging
# from datetime import datetime

# from chat_agent import ConversationManager
# from models import PatientInfo, APIResponse
# from utils import performance_monitor, DataValidator
# from config import Config

# # Setup logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Initialize FastAPI app
# app = FastAPI(
#     title="DentalChat AI Automation API",
#     description="Automated patient intake and post creation for dental offices",
#     version="1.0.0"
# )

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Configure appropriately for production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Initialize conversation manager
# conversation_manager = ConversationManager()

# # Pydantic models for API
# class MessageRequest(BaseModel):
#     message: str
#     session_id: Optional[str] = None

# class MessageResponse(BaseModel):
#     response: str
#     session_id: str
#     is_complete: bool
#     patient_info: Optional[Dict] = None

# class SessionResponse(BaseModel):
#     session_id: str
#     message: str

# class HealthResponse(BaseModel):
#     status: str
#     timestamp: str
#     version: str

# @app.get("/", response_class=HTMLResponse)
# async def read_root():
#     """Serve the main chat interface"""
#     return """
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <title>DentalChat AI Assistant</title>
#         <meta charset="UTF-8">
#         <meta name="viewport" content="width=device-width, initial-scale=1.0">
#         <style>
#             body {
#                 font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
#                 max-width: 800px;
#                 margin: 0 auto;
#                 padding: 20px;
#                 background-color: #f5f5f5;
#             }
#             .container {
#                 background: white;
#                 border-radius: 10px;
#                 padding: 30px;
#                 box-shadow: 0 2px 10px rgba(0,0,0,0.1);
#             }
#             .header {
#                 text-align: center;
#                 color: #2a5298;
#                 margin-bottom: 30px;
#             }
#             .chat-container {
#                 height: 400px;
#                 overflow-y: auto;
#                 border: 1px solid #ddd;
#                 padding: 15px;
#                 margin-bottom: 20px;
#                 border-radius: 5px;
#                 background-color: #fafafa;
#             }
#             .message {
#                 margin: 10px 0;
#                 padding: 10px;
#                 border-radius: 10px;
#             }
#             .user-message {
#                 background-color: #e3f2fd;
#                 text-align: right;
#                 margin-left: 20%;
#             }
#             .assistant-message {
#                 background-color: #f1f8e9;
#                 margin-right: 20%;
#             }
#             .input-container {
#                 display: flex;
#                 gap: 10px;
#             }
#             #messageInput {
#                 flex: 1;
#                 padding: 12px;
#                 border: 1px solid #ddd;
#                 border-radius: 5px;
#                 font-size: 16px;
#             }
#             #sendButton {
#                 padding: 12px 24px;
#                 background-color: #2a5298;
#                 color: white;
#                 border: none;
#                 border-radius: 5px;
#                 cursor: pointer;
#                 font-size: 16px;
#             }
#             #sendButton:hover {
#                 background-color: #1e3c72;
#             }
#             #sendButton:disabled {
#                 background-color: #ccc;
#                 cursor: not-allowed;
#             }
#             .loading {
#                 color: #666;
#                 font-style: italic;
#             }
#             .complete-message {
#                 background-color: #d4edda;
#                 color: #155724;
#                 padding: 15px;
#                 border-radius: 5px;
#                 margin: 10px 0;
#                 text-align: center;
#             }
#         </style>
#     </head>
#     <body>
#         <div class="container">
#             <div class="header">
#                 <h1>🦷 DentalChat AI Assistant</h1>
#                 <p>Automated patient intake for dental offices</p>
#             </div>
            
#             <div id="chatContainer" class="chat-container">
#                 <div class="message assistant-message">
#                     <strong>Dr. Assistant:</strong> Welcome! Click "Start New Conversation" to begin.
#                 </div>
#             </div>
            
#             <div class="input-container">
#                 <input type="text" id="messageInput" placeholder="Type your message here..." disabled>
#                 <button id="sendButton" onclick="sendMessage()" disabled>Send</button>
#                 <button id="newChatButton" onclick="startNewChat()">New Chat</button>
#             </div>
#         </div>

#         <script>
#             let sessionId = null;
#             let isComplete = false;

#             async function startNewChat() {
#                 try {
#                     const response = await fetch('/api/new-session', {
#                         method: 'POST'
#                     });
#                     const data = await response.json();
                    
#                     sessionId = data.session_id;
#                     isComplete = false;
                    
#                     // Clear chat and add welcome message
#                     const chatContainer = document.getElementById('chatContainer');
#                     chatContainer.innerHTML = '';
                    
#                     addMessage('assistant', data.message);
                    
#                     // Enable input
#                     document.getElementById('messageInput').disabled = false;
#                     document.getElementById('sendButton').disabled = false;
#                     document.getElementById('messageInput').focus();
                    
#                 } catch (error) {
#                     console.error('Error starting new chat:', error);
#                     alert('Error starting new conversation. Please try again.');
#                 }
#             }

#             async function sendMessage() {
#                 const messageInput = document.getElementById('messageInput');
#                 const message = messageInput.value.trim();
                
#                 if (!message || !sessionId || isComplete) return;
                
#                 // Add user message to chat
#                 addMessage('user', message);
#                 messageInput.value = '';
                
#                 // Show loading
#                 const loadingDiv = addMessage('assistant', 'Dr. Assistant is typing...', 'loading');
                
#                 // Disable input while processing
#                 document.getElementById('sendButton').disabled = true;
#                 messageInput.disabled = true;
                
#                 try {
#                     const response = await fetch('/api/chat', {
#                         method: 'POST',
#                         headers: {
#                             'Content-Type': 'application/json'
#                         },
#                         body: JSON.stringify({
#                             message: message,
#                             session_id: sessionId
#                         })
#                     });
                    
#                     const data = await response.json();
                    
#                     // Remove loading message
#                     loadingDiv.remove();
                    
#                     // Add assistant response
#                     addMessage('assistant', data.response);
                    
#                     // Check if conversation is complete
#                     if (data.is_complete) {
#                         isComplete = true;
#                         document.getElementById('messageInput').disabled = true;
#                         document.getElementById('sendButton').disabled = true;
                        
#                         // Add completion message
#                         const completeDiv = document.createElement('div');
#                         completeDiv.className = 'complete-message';
#                         completeDiv.innerHTML = '✅ <strong>Conversation Complete!</strong> Your dental post has been created successfully.';
#                         document.getElementById('chatContainer').appendChild(completeDiv);
#                     } else {
#                         // Re-enable input
#                         messageInput.disabled = false;
#                         document.getElementById('sendButton').disabled = false;
#                         messageInput.focus();
#                     }
                    
#                 } catch (error) {
#                     console.error('Error sending message:', error);
#                     loadingDiv.remove();
#                     addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
                    
#                     // Re-enable input
#                     messageInput.disabled = false;
#                     document.getElementById('sendButton').disabled = false;
#                 }
#             }

#             function addMessage(role, content, className = '') {
#                 const chatContainer = document.getElementById('chatContainer');
#                 const messageDiv = document.createElement('div');
#                 messageDiv.className = `message ${role}-message ${className}`;
                
#                 const roleLabel = role === 'user' ? 'You' : 'Dr. Assistant';
#                 messageDiv.innerHTML = `<strong>${roleLabel}:</strong> ${content}`;
                
#                 chatContainer.appendChild(messageDiv);
#                 chatContainer.scrollTop = chatContainer.scrollHeight;
                
#                 return messageDiv;
#             }

#             // Handle Enter key
#             document.getElementById('messageInput').addEventListener('keypress', function(e) {
#                 if (e.key === 'Enter') {
#                     sendMessage();
#                 }
#             });
#         </script>
#     </body>
#     </html>
#     """

# @app.get("/health", response_model=HealthResponse)
# async def health_check():
#     """Health check endpoint"""
#     return HealthResponse(
#         status="healthy",
#         timestamp=datetime.now().isoformat(),
#         version="1.0.0"
#     )

# @app.post("/api/new-session", response_model=SessionResponse)
# async def create_new_session():
#     """Create a new conversation session"""
#     try:
#         session_id, welcome_msg = conversation_manager.create_session()
        
#         performance_monitor.increment_metric('conversations_started')
        
#         return SessionResponse(
#             session_id=session_id,
#             message=welcome_msg
#         )
        
#     except Exception as e:
#         logger.error(f"Error creating session: {e}")
#         raise HTTPException(status_code=500, detail="Failed to create session")

# @app.post("/api/chat", response_model=MessageResponse)
# async def chat_message(request: MessageRequest):
#     """Send a message to the chatbot"""
#     try:
#         # Validate input
#         if not request.message.strip():
#             raise HTTPException(status_code=400, detail="Message cannot be empty")
        
#         if not request.session_id:
#             raise HTTPException(status_code=400, detail="Session ID is required")
        
#         # Sanitize input
#         sanitized_message = DataValidator.sanitize_input(request.message)
        
#         # Send message to conversation manager
#         response, is_complete = conversation_manager.send_message(
#             request.session_id, 
#             sanitized_message
#         )
        
#         # Get session info for patient data
#         session_info = conversation_manager.get_session_info(request.session_id)
#         patient_info = session_info.get('patient_info') if session_info else None
        
#         performance_monitor.increment_metric('api_calls')
        
#         if is_complete:
#             performance_monitor.increment_metric('conversations_completed')
#             performance_monitor.increment_metric('posts_created')
        
#         return MessageResponse(
#             response=response,
#             session_id=request.session_id,
#             is_complete=is_complete,
#             patient_info=patient_info
#         )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error processing chat message: {e}")
#         performance_monitor.increment_metric('errors')
#         raise HTTPException(status_code=500, detail="Failed to process message")

# @app.get("/api/session/{session_id}")
# async def get_session_info(session_id: str):
#     """Get information about a specific session"""
#     try:
#         if not DataValidator.is_valid_session_id(session_id):
#             raise HTTPException(status_code=400, detail="Invalid session ID format")
        
#         session_info = conversation_manager.get_session_info(session_id)
        
#         if not session_info:
#             raise HTTPException(status_code=404, detail="Session not found")
        
#         return session_info
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error getting session info: {e}")
#         raise HTTPException(status_code=500, detail="Failed to get session info")

# @app.get("/api/metrics")
# async def get_metrics():
#     """Get application metrics"""
#     return {
#         "metrics": performance_monitor.get_metrics(),
#         "timestamp": datetime.now().isoformat()
#     }

# @app.post("/api/validate")
# async def validate_patient_info(patient_info: Dict):
#     """Validate patient information"""
#     try:
#         # Create PatientInfo object for validation
#         info = PatientInfo(**patient_info)
        
#         return {
#             "is_valid": True,
#             "is_complete": info.is_complete(),
#             "missing_fields": info.missing_fields(),
#             "validated_data": info.dict()
#         }
        
#     except Exception as e:
#         return {
#             "is_valid": False,
#             "error": str(e),
#             "missing_fields": []
#         }

# # Error handlers
# @app.exception_handler(404)
# async def not_found_handler(request, exc):
#     return JSONResponse(
#         status_code=404,
#         content={"error": "Endpoint not found"}
#     )

# @app.exception_handler(500)
# async def internal_error_handler(request, exc):
#     return JSONResponse(
#         status_code=500,
#         content={"error": "Internal server error"}
#     )

# def run_server():
#     """Run the FastAPI server"""
#     uvicorn.run(
#         "fastapi_app:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=True,
#         log_level="info"
#     )

# if __name__ == "__main__":
#     run_server()