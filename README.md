# DentalChat AI Automation

🦷 **AI-powered chatbot that automates dental patient intake and creates posts on DentalChat platform**

## What It Does

This system replaces manual form filling with a natural conversation. Patients chat with an AI assistant that:
- Collects dental problem details through conversation
- Extracts patient information (name, contact, location, pain level)
- Automatically creates and submits posts to DentalChat
- Connects patients with local dentists

## Features

- **Natural Language Processing** - Conversational intake instead of forms
- **Smart Information Extraction** - AI extracts structured data from chat
- **Emergency Detection** - Identifies urgent cases based on symptoms/pain
- **Auto-Post Creation** - Direct integration with DentalChat API
- **Contact Validation** - Phone/email format checking

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
Create `.env` file:
```
OPENAI_API_KEY=your_openai_api_key_here
DENTALCHAT_API_KEY=your_dentalchat_api_key_here
```

### 3. Run Application
```bash
streamlit run main.py
```

Open http://localhost:8501 in your browser.

## How It Works

1. **Patient starts conversation** - "I have tooth pain"
2. **AI asks follow-up questions** - Pain level, location, contact info
3. **Information extracted automatically** - No manual form filling
4. **Post created and submitted** - Directly to DentalChat platform
5. **Local dentists notified** - Patient gets responses from nearby dentists

## Project Structure

```
├── main.py              # Streamlit web interface
├── chat_agent.py        # LangChain conversation manager
├── data_extractor.py    # AI information extraction
├── dentalchat_api.py    # DentalChat API integration
├── models.py            # Data models and validation
├── config.py            # Configuration settings
├── requirements.txt     # Dependencies
└── .env                 # Environment variables
```

## Example Conversation

```
Dr. Assistant: What's going on with your teeth today?
Patient: I have severe tooth pain
Dr. Assistant: On a scale of 1-10, how bad is the pain?
Patient: About an 8
Dr. Assistant: When did it start?
Patient: 2 days ago
Dr. Assistant: What's your ZIP code?
Patient: 75201
Dr. Assistant: Your name and phone number?
Patient: John Smith, 555-123-4567
Dr. Assistant: ✅ Post created! Local dentists will contact you soon.
```

## Configuration

- **Mock Mode**: Uses fake API responses (default for demo)
- **Production Mode**: Connects to real DentalChat API
- **Emergency Threshold**: Pain level 7+ marked as emergency
- **Required Fields**: Problem, name, location, contact info

## Technology Stack

- **Frontend**: Streamlit
- **AI**: OpenAI GPT-4 + LangChain
- **API**: FastAPI (optional)
- **Validation**: Pydantic
- **Data**: In-memory storage

## Demo

The system includes mock API responses for testing without real DentalChat integration. Perfect for demonstrations and development.

## License

MIT License
