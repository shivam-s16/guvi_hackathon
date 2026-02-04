# 🍯 Agentic Honey-Pot API

An AI-powered honeypot system for scam detection and intelligence extraction. This system detects fraudulent messages, engages scammers autonomously using **FREE AI APIs**, and extracts actionable intelligence.

## 🎯 Features

- **Scam Detection Engine**: Multi-layered detection using keyword analysis, regex patterns, and behavioral indicators
- **AI Agent**: Autonomous engagement with believable human-like personas
- **FREE AI Support**: Works with Gemini, Groq, and Cohere (all FREE tiers!)
- **Intelligence Extraction**: Extracts bank accounts, UPI IDs, phone numbers, phishing links
- **Session Management**: Handles multi-turn conversations with state persistence
- **GUVI Integration**: Automatic callback to evaluation endpoint

## 📁 Project Structure

```
HACKATHON/
├── hack/                      # Virtual environment
├── app/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── models.py              # Pydantic request/response models
│   ├── main.py                # FastAPI application
│   ├── scam_detector.py       # Scam detection engine
│   ├── intelligence_extractor.py  # Intelligence extraction
│   ├── agent.py               # AI agent for engagement
│   ├── session_manager.py     # Session state management
│   └── guvi_callback.py       # GUVI evaluation callback
├── tests/
│   └── test_api.py            # API test script
├── .env                       # Environment variables
├── requirements.txt           # Python dependencies
├── run.py                     # Server run script
└── README.md                  # This file
```

## 🚀 Quick Start

### 1. Activate Virtual Environment

```bash
# Windows
.\hack\Scripts\activate

# Linux/Mac
source hack/bin/activate
```

### 2. Configure FREE AI API Keys

Edit `.env` file and add at least ONE of these FREE API keys:

```env
# Google Gemini (FREE) - https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your-gemini-key

# Groq (FREE & FAST!) - https://console.groq.com/keys
GROQ_API_KEY=your-groq-key

# Cohere (FREE) - https://dashboard.cohere.com/api-keys
COHERE_API_KEY=your-cohere-key
```

### 3. Run the Server

```bash
python run.py
```

Or:
```bash
.\hack\Scripts\python.exe run.py
```

### 4. Access the API

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🆓 FREE AI Providers

| Provider | Model | Speed | Get Key |
|----------|-------|-------|---------|
| **Gemini** | gemini-1.5-flash | Fast | [Google AI Studio](https://makersuite.google.com/app/apikey) |
| **Groq** | llama-3.1-8b-instant | ⚡ Super Fast | [Groq Console](https://console.groq.com/keys) |
| **Cohere** | command-r | Good | [Cohere Dashboard](https://dashboard.cohere.com/api-keys) |

**Note**: The system will try providers in order (Gemini → Groq → Cohere → Fallback). If no API keys are configured, it uses intelligent template-based responses.

## 📡 API Endpoints

### 🎯 Primary Endpoint: `/api/message` (GUVI Evaluation)

**This is the main endpoint for GUVI evaluation** - returns simple format.

```http
POST /api/message
Content-Type: application/json
x-api-key: YOUR_SECRET_API_KEY
```

**Request Body:**
```json
{
  "sessionId": "wertyu-dfghj-ertyui",
  "message": {
    "sender": "scammer",
    "text": "Your bank account will be blocked today. Verify immediately.",
    "timestamp": "2026-01-21T10:15:30Z"
  },
  "conversationHistory": [],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

**Response (Simple Format):**
```json
{
  "status": "success",
  "reply": "Why is my account being suspended?"
}
```

**Multi-Language Support:** Set `metadata.language` to `"Hindi"` or `"Tamil"` for responses in that language:

```json
{
  "status": "success",
  "reply": "क्या? मेरा अकाउंट ब्लॉक हो जाएगा? लेकिन क्यों सर?"
}
```

---

### 📊 Detailed Endpoint: `/api/honeypot`

Returns detailed response with intelligence.

```http
POST /api/honeypot
Content-Type: application/json
x-api-key: YOUR_SECRET_API_KEY
```

**Request Body (First Message):**
```json
{
  "sessionId": "unique-session-id",
  "message": {
    "sender": "scammer",
    "text": "Your bank account will be blocked today. Verify immediately.",
    "timestamp": "2026-01-21T10:15:30Z"
  },
  "conversationHistory": [],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

**Response (Detailed):**
```json
{
  "status": "success",
  "scamDetected": true,
  "agentResponse": "What? My account will be blocked? But why sir?",
  "engagementMetrics": {
    "engagementDurationSeconds": 5,
    "totalMessagesExchanged": 2
  },
  "extractedIntelligence": {
    "bankAccounts": [],
    "upiIds": [],
    "phishingLinks": [],
    "phoneNumbers": [],
    "suspiciousKeywords": ["blocked", "verify", "immediately"]
  },
  "agentNotes": "AI Provider: gemini. Persona: Rajesh Kumar, 58yo retired teacher",
  "sessionActive": true
}
```

### Follow-up Message (Multi-turn)

```json
{
  "sessionId": "same-session-id",
  "message": {
    "sender": "scammer",
    "text": "Share your UPI ID scammer@ybl for verification. Call 9876543210.",
    "timestamp": "2026-01-21T10:17:10Z"
  },
  "conversationHistory": [
    {
      "sender": "scammer",
      "text": "Your bank account will be blocked today.",
      "timestamp": "2026-01-21T10:15:30Z"
    },
    {
      "sender": "user",
      "text": "What? My account will be blocked? But why sir?",
      "timestamp": "2026-01-21T10:16:10Z"
    }
  ],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

### Other Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/session/{id}` | GET | Get session info |
| `/api/session/{id}/complete` | POST | Complete session & trigger GUVI callback |
| `/api/stats` | GET | Get honeypot statistics |
| `/health` | GET | Health check |

## 🤖 AI Agent Behavior

The AI agent:

1. **Maintains a Persona**: Generates a believable victim persona (elderly person, less tech-savvy)
2. **Shows Confusion**: Responds with worry and confusion initially
3. **Asks Questions**: Probes for more information from scammers
4. **Builds Trust**: Gradually shows compliance to keep scammers engaged
5. **Stalls**: Delays while extracting maximum intelligence
6. **Provides Fake Info**: Gives fake OTPs, wrong account numbers when pressed

## 🕵️ Intelligence Extraction

Automatically extracts:

- **Bank Accounts**: Indian account number patterns
- **UPI IDs**: All major UPI handle formats (@ybl, @paytm, @oksbi, etc.)
- **Phone Numbers**: Indian mobile numbers (+91)
- **Phishing Links**: Suspicious URLs and shortened links
- **Email Addresses**: Email patterns
- **Suspicious Keywords**: Urgency, threats, financial terms

## 📋 GUVI Evaluation Callback

When a session completes, results are automatically sent to:
```
POST https://hackathon.guvi.in/api/updateHoneyPotFinalResult
```

**Payload sent:**
```json
{
  "sessionId": "abc123-session-id",
  "scamDetected": true,
  "totalMessagesExchanged": 18,
  "extractedIntelligence": {
    "bankAccounts": ["XXXX-XXXX-XXXX"],
    "upiIds": ["scammer@upi"],
    "phishingLinks": ["http://malicious-link.example"],
    "phoneNumbers": ["+91XXXXXXXXXX"],
    "suspiciousKeywords": ["urgent", "verify now", "account blocked"]
  },
  "agentNotes": "Scammer used urgency tactics and payment redirection"
}
```

## 🧪 Testing

```bash
# Activate environment first
.\hack\Scripts\activate

# Run tests
python tests/test_api.py
```

## 🛠️ Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | API authentication key | `default-secret-key-change-me` |
| `AI_PROVIDER` | Primary AI provider | `gemini` |
| `GEMINI_API_KEY` | Google Gemini API key (FREE) | - |
| `GROQ_API_KEY` | Groq API key (FREE) | - |
| `COHERE_API_KEY` | Cohere API key (FREE) | - |
| `SESSION_TIMEOUT_MINUTES` | Session timeout | `30` |
| `MAX_ENGAGEMENT_MESSAGES` | Max messages per session | `25` |

## 📝 License

MIT License - Built for GUVI Hackathon 2026
