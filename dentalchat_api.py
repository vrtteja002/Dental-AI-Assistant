"""
DentalChat API integration module
"""
import requests
import json
from typing import Dict, Any, Optional, List
from models import DentalChatPost, PatientInfo, APIResponse
from config import Config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DentalChatAPI:
    """Handle API interactions with DentalChat platform"""
    
    def __init__(self):
        self.base_url = Config.DENTALCHAT_BASE_URL
        self.api_key = Config.DENTALCHAT_API_KEY
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': 'DentalChat-AI-Bot/1.0'
        })
    
    def create_patient_post(self, patient_info: PatientInfo) -> APIResponse:
        """
        Create a patient post on DentalChat platform
        
        Args:
            patient_info: Complete patient information
            
        Returns:
            APIResponse with success status and post details
        """
        try:
            # Validate patient info is complete
            if not patient_info.is_complete():
                missing = patient_info.missing_fields()
                return APIResponse(
                    success=False,
                    message=f"Missing required fields: {', '.join(missing)}",
                    error="INCOMPLETE_DATA"
                )
            
            # Create DentalChat post object
            post_data = DentalChatPost.from_patient_info(patient_info)
            
            # Prepare API payload
            payload = self._prepare_post_payload(post_data)
            
            # Make API request
            response = self.session.post(
                f"{self.base_url}/patient/create-post",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200 or response.status_code == 201:
                response_data = response.json()
                return APIResponse(
                    success=True,
                    message="Post created successfully",
                    data={
                        "post_id": response_data.get("post_id"),
                        "url": response_data.get("post_url"),
                        "estimated_response_time": response_data.get("estimated_response_time", "1-2 hours")
                    }
                )
            else:
                error_msg = self._parse_error_response(response)
                return APIResponse(
                    success=False,
                    message="Failed to create post",
                    error=error_msg
                )
                
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return APIResponse(
                success=False,
                message="Network error occurred",
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return APIResponse(
                success=False,
                message="An unexpected error occurred",
                error=str(e)
            )
    
    def get_nearby_dentists(self, zip_code: str, emergency: bool = False) -> APIResponse:
        """
        Get list of nearby dentists
        
        Args:
            zip_code: Patient's ZIP code
            emergency: Whether this is an emergency case
            
        Returns:
            APIResponse with dentist list
        """
        try:
            params = {
                'zip_code': zip_code,
                'emergency': emergency,
                'radius': 25,  # 25 mile radius
                'limit': 10
            }
            
            response = self.session.get(
                f"{self.base_url}/dentists/search",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                dentists = response.json().get('dentists', [])
                return APIResponse(
                    success=True,
                    message=f"Found {len(dentists)} dentists nearby",
                    data={"dentists": dentists}
                )
            else:
                return APIResponse(
                    success=False,
                    message="Failed to find nearby dentists",
                    error=self._parse_error_response(response)
                )
                
        except Exception as e:
            logger.error(f"Error finding dentists: {e}")
            return APIResponse(
                success=False,
                message="Error finding nearby dentists",
                error=str(e)
            )
    
    def get_post_status(self, post_id: str) -> APIResponse:
        """
        Get status of a patient post
        
        Args:
            post_id: ID of the post to check
            
        Returns:
            APIResponse with post status
        """
        try:
            response = self.session.get(
                f"{self.base_url}/patient/post/{post_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                post_data = response.json()
                return APIResponse(
                    success=True,
                    message="Post status retrieved",
                    data=post_data
                )
            else:
                return APIResponse(
                    success=False,
                    message="Failed to get post status",
                    error=self._parse_error_response(response)
                )
                
        except Exception as e:
            logger.error(f"Error getting post status: {e}")
            return APIResponse(
                success=False,
                message="Error retrieving post status",
                error=str(e)
            )
    
    def _prepare_post_payload(self, post_data: DentalChatPost) -> Dict[str, Any]:
        """
        Prepare the API payload for post creation
        """
        return {
            "title": post_data.title,
            "description": post_data.problem_description,
            "pain_level": post_data.pain_level,
            "emergency": post_data.emergency,
            "location": post_data.location,
            "patient": {
                "name": post_data.patient_name,
                "phone": post_data.phone,
                "email": post_data.email
            },
            "symptoms": {
                "started_when": post_data.started_when,
                "symptoms_list": post_data.symptoms
            },
            "metadata": {
                "source": "AI_CHATBOT",
                "version": "1.0",
                "automated": True
            }
        }
    
    def _parse_error_response(self, response: requests.Response) -> str:
        """
        Parse error response from API
        """
        try:
            error_data = response.json()
            return error_data.get('error', f'HTTP {response.status_code}')
        except:
            return f'HTTP {response.status_code}: {response.text[:100]}'

class MockDentalChatAPI(DentalChatAPI):
    """
    Mock API for testing and demo purposes
    """
    
    def __init__(self):
        super().__init__()
        self.mock_responses = True
        logger.info("Using Mock DentalChat API for demo")
    
    def create_patient_post(self, patient_info: PatientInfo) -> APIResponse:
        """
        Mock post creation for demo
        """
        if not patient_info.is_complete():
            missing = patient_info.missing_fields()
            return APIResponse(
                success=False,
                message=f"Missing required fields: {', '.join(missing)}",
                error="INCOMPLETE_DATA"
            )
        
        # Simulate successful post creation
        import uuid
        post_id = str(uuid.uuid4())[:8]
        
        return APIResponse(
            success=True,
            message="Post created successfully (DEMO MODE)",
            data={
                "post_id": post_id,
                "url": f"https://dentalchat.com/post/{post_id}",
                "estimated_response_time": "1-2 hours",
                "nearby_dentists": 5,
                "demo_mode": True
            }
        )
    
    def get_nearby_dentists(self, zip_code: str, emergency: bool = False) -> APIResponse:
        """
        Mock dentist search
        """
        mock_dentists = [
            {
                "name": "Dr. Sarah Johnson",
                "practice": "Dallas Dental Care",
                "distance": "2.3 miles",
                "rating": 4.8,
                "emergency_hours": emergency
            },
            {
                "name": "Dr. Michael Chen",
                "practice": "Modern Dentistry",
                "distance": "3.1 miles", 
                "rating": 4.7,
                "emergency_hours": emergency
            },
            {
                "name": "Dr. Emily Rodriguez",
                "practice": "Family Dental Center",
                "distance": "4.2 miles",
                "rating": 4.9,
                "emergency_hours": emergency
            }
        ]
        
        return APIResponse(
            success=True,
            message=f"Found {len(mock_dentists)} dentists nearby (DEMO MODE)",
            data={"dentists": mock_dentists}
        )
    
    def get_post_status(self, post_id: str) -> APIResponse:
        """
        Mock post status
        """
        return APIResponse(
            success=True,
            message="Post status retrieved (DEMO MODE)",
            data={
                "post_id": post_id,
                "status": "active",
                "responses": 2,
                "views": 15,
                "created_at": "2024-01-15T10:30:00Z"
            }
        )

def get_api_client(use_mock: bool = True) -> DentalChatAPI:
    """
    Factory function to get appropriate API client
    
    Args:
        use_mock: Whether to use mock API for demo/testing
        
    Returns:
        DentalChatAPI instance
    """
    if use_mock or Config.DENTALCHAT_API_KEY == "demo_key":
        return MockDentalChatAPI()
    else:
        return DentalChatAPI()
