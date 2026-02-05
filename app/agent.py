"""
AI Agent Module.
Autonomous agent that engages scammers with believable human-like responses.
Supports FREE AI providers: Gemini, Cohere, Groq
"""

import random
import os
import httpx
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from app.models import Message, ConversationMessage
from app.config import get_settings
from app.services.behavior_engine import get_behavior_engine


class PersonaGenerator:
    """Generates believable victim personas for the honeypot."""
    
    FIRST_NAMES = [
        "Rajesh", "Priya", "Amit", "Sunita", "Vikram", "Anjali", "Rahul", "Neha",
        "Suresh", "Kavita", "Deepak", "Pooja", "Arun", "Meera", "Sanjay", "Rekha",
        "Manoj", "Anita", "Vijay", "Lakshmi", "Ramesh", "Geeta", "Ashok", "Shanti"
    ]
    
    LAST_NAMES = [
        "Kumar", "Sharma", "Patel", "Singh", "Verma", "Gupta", "Reddy", "Yadav",
        "Joshi", "Agarwal", "Mehta", "Iyer", "Nair", "Das", "Chakraborty"
    ]
    
    OCCUPATIONS = [
        "retired teacher", "small business owner", "farmer", "housewife",
        "government employee", "shopkeeper", "retired bank employee",
        "private job holder", "senior citizen", "homemaker"
    ]
    
    BANKS = [
        "SBI", "HDFC Bank", "ICICI Bank", "Axis Bank", "Punjab National Bank",
        "Bank of Baroda", "Canara Bank", "Union Bank", "Indian Bank"
    ]
    
    LOCATIONS = [
        "Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad",
        "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Patna", "Bhopal"
    ]
    
    @classmethod
    def generate(cls) -> Dict:
        """Generate a random victim persona."""
        age = random.randint(45, 70)
        gender = random.choice(["male", "female"])
        
        if gender == "male":
            first_name = random.choice([n for n in cls.FIRST_NAMES if n in [
                "Rajesh", "Amit", "Vikram", "Rahul", "Suresh", "Deepak", 
                "Arun", "Sanjay", "Manoj", "Vijay", "Ramesh", "Ashok"
            ]])
        else:
            first_name = random.choice([n for n in cls.FIRST_NAMES if n in [
                "Priya", "Sunita", "Anjali", "Neha", "Kavita", "Pooja",
                "Meera", "Rekha", "Anita", "Lakshmi", "Geeta", "Shanti"
            ]])
        
        persona = {
            "name": f"{first_name} {random.choice(cls.LAST_NAMES)}",
            "age": age,
            "gender": gender,
            "occupation": random.choice(cls.OCCUPATIONS),
            "bank": random.choice(cls.BANKS),
            "location": random.choice(cls.LOCATIONS),
            "tech_savvy": random.choice(["low", "low", "medium"]),
            "emotional_state": random.choice(["worried", "confused", "trusting"]),
            "typing_style": random.choice(["slow", "makes_typos", "formal"])
        }
        
        return persona


class FallbackResponseGenerator:
    """
    Advanced contextual response generator with:
    - Adaptive responses based on scam type
    - Self-correction capabilities
    - Human-like behavior patterns
    - Dynamic engagement strategies
    """
    
    # Base templates organized by phase - ENGLISH ONLY
    RESPONSE_TEMPLATES = {
        "initial_confusion": [
            "What? My account will be blocked? But why?",
            "I don't understand, what happened to my account?",
            "Oh no! Please tell me what I should do?",
            "This is very worrying, I have my savings there",
            "Please help me, I am not understanding",
            "What is happening? Please explain properly",
            "This is very shocking news, how can this happen?",
            "I am confused, can you explain again?",
        ],
        "asking_for_details": [
            "But which bank are you calling from?",
            "Can you tell me the reason for blocking?",
            "I have multiple accounts... which one are you talking about?",
            "What should I do to verify? Please guide me",
            "Is this about my savings account?",
            "Please tell me your name and employee ID",
            "Which branch office are you from?",
            "What is your designation? Are you the manager?",
        ],
        "showing_concern": [
            "Please don't block my account, all my savings are there!",
            "I am a senior citizen, please solve this problem",
            "My children gave me money for medicines, please help",
            "This is my only savings... please tell me what to do",
            "I will lose everything... please help me",
            "My grandchildren's school fees are in that account!",
            "I beg you, please don't do this to me",
            "I am very worried now... what should I do?",
        ],
        "probing_for_info": [
            "Where should I transfer the money? Give me the account number",
            "What UPI ID should I use for verification?",
            "Give me the link, I will click and verify",
            "Should I give you my account details?",
            "Tell me the steps... I will follow everything you say",
            "What information do you need from me?",
            "Please share your WhatsApp number for easier contact",
            "Can you send me the verification link on WhatsApp?",
            "Which account should I transfer to? Please give full details",
        ],
        "showing_hesitation": [
            "But my son told me not to share OTP with anyone...",
            "I saw news about fraud... are you really from the bank?",
            "Let me call my daughter first and ask...",
            "This seems different from normal bank calls...",
            "Can you call me back on the bank's official number?",
            "Wait... my neighbor was cheated like this last month...",
            "I heard that banks never ask OTP on call...",
            "Something feels wrong... let me think about it",
        ],
        "building_trust": [
            "Yes yes, I believe you. What should I do?",
            "Thank you for helping me. Please guide me step by step",
            "I trust you, you seem very helpful",
            "Ok, I am ready to do what you say",
            "You are so kind to help an old person like me",
            "Thank god you called, otherwise my money would be lost!",
            "You are like my son, helping me in this difficult time",
        ],
        "stalling": [
            "One moment, my phone battery is low",
            "Please wait, someone is at the door",
            "Hold on, I am writing down what you said",
            "The network is bad, please repeat",
            "I am searching for my glasses to read the OTP",
            "My hands are shaking, give me 2 minutes",
            "Let me get my passbook, one second",
            "Phone is heating, let me restart. Please wait",
            "I need to charge my phone, can you wait 5 minutes?",
        ],
        "providing_fake_info": [
            "Ok, my account number is. Let me check first",
            "The OTP I received is. Wait the message disappeared",
            "My UPI ID is {fake_upi} I think",
            "Let me transfer the money. The app is loading slowly",
            "I am trying to click the link but it's not opening",
            "OTP is coming. Yes I see a number but screen is dim",
            "I am entering the details. Internet is very slow today",
            "I sent the money but transaction is pending, please check",
        ],
        "self_correction": [
            "Sorry, I think I gave wrong number. Let me check again",
            "Wait, I made mistake. That was my old account",
            "Oh, I read the OTP wrong, let me see again",
            "My eyes are weak, I think I misread the number",
            "Actually, my daughter changed my password, let me ask her",
        ],
    }
    
    # Scam-type specific responses for better adaptation - ENGLISH ONLY
    SCAM_SPECIFIC_RESPONSES = {
        "Banking/UPI Fraud": [
            "My bank account? I just deposited my savings there!",
            "But I haven't done any suspicious activity... why is this happening?",
            "Should I come to the bank branch or can this be done on phone?",
        ],
        "Prize/Lottery Scam": [
            "I really won a prize? But I never applied for any lottery...",
            "Wow! This is like a dream come true! What do I need to do?",
            "My luck is very good today! How much money did I win?",
        ],
        "Threat/Impersonation Scam": [
            "Police? Arrest? But I am an honest citizen, what did I do wrong?",
            "Please don't arrest me, I have a heart condition!",
            "I will pay whatever fine, please don't send police to my home!",
        ],
        "Phishing Scam": [
            "Which link? I will click now, please guide me",
            "My son said not to click unknown links... but you are from the bank right?",
            "Website is not opening... my internet is slow",
        ],
    }
    
    FAKE_UPIS = [
        "ramesh.kumar@oksbi", "priya.sharma@ybl", "suresh.1952@paytm",
        "meera_aunty@okicici", "oldman1955@upi", "pension.uncle@okaxis",
        "uncle.retired@apl", "dadaji1955@ybl", "mummy.savings@paytm"
    ]
    
    FAKE_OTPS = ["I received a code", "There's a message with numbers", "I see an OTP on screen", "Got a verification code"]
    
    def __init__(self, persona: Dict):
        """Initialize with a persona."""
        self.persona = persona
        self.message_count = 0
        self.last_phase = None
        self.hesitation_shown = False
    
    def get_response_phase(self, scam_type: str, history_length: int) -> str:
        """
        Determine the current engagement phase with adaptive logic.
        Implements natural conversation flow with occasional self-correction.
        """
        # 10% chance of self-correction after initial messages
        if history_length > 2 and random.random() < 0.1:
            return "self_correction"
        
        if history_length <= 1:
            return "initial_confusion"
        elif history_length <= 3:
            return random.choice(["asking_for_details", "showing_concern"])
        elif history_length <= 5:
            # Mix trust with occasional hesitation
            if not self.hesitation_shown and random.random() < 0.3:
                self.hesitation_shown = True
                return "showing_hesitation"
            return random.choice(["probing_for_info", "building_trust"])
        elif history_length <= 8:
            return random.choice(["stalling", "probing_for_info", "building_trust"])
        else:
            return random.choice(["providing_fake_info", "stalling", "probing_for_info"])
    
    def _get_scam_specific_response(self, scam_type: str) -> Optional[str]:
        """Get a response specific to the scam type."""
        if scam_type in self.SCAM_SPECIFIC_RESPONSES:
            return random.choice(self.SCAM_SPECIFIC_RESPONSES[scam_type])
        return None
    
    def _analyze_scammer_message(self, message: str) -> Dict[str, bool]:
        """Analyze scammer message for contextual response."""
        message_lower = message.lower()
        return {
            "asks_for_otp": any(word in message_lower for word in ["otp", "code", "password", "pin"]),
            "asks_for_money": any(word in message_lower for word in ["transfer", "send", "pay", "rs", "₹", "rupee"]),
            "asks_for_account": any(word in message_lower for word in ["account", "upi", "bank"]),
            "shows_urgency": any(word in message_lower for word in ["urgent", "immediate", "now", "hurry", "fast"]),
            "mentions_link": any(word in message_lower for word in ["link", "click", "website", "http"]),
            "threatens": any(word in message_lower for word in ["block", "arrest", "police", "legal", "suspend"]),
            "prize_lottery": any(word in message_lower for word in ["won", "prize", "lottery", "winner", "reward", "cashback", "congratulation", "bike", "car", "lucky"]),
            "kyc_verify": any(word in message_lower for word in ["kyc", "verify", "verification", "update", "expire"]),
            "visit_branch": any(word in message_lower for word in ["visit", "branch", "local", "come"]),
            "is_greeting": any(word in message_lower for word in ["hi", "hello", "namaste", "good morning", "good afternoon"]),
        }
    
    def _generate_contextual_response(self, scammer_message: str, phase: str) -> str:
        """Generate response based on what scammer is asking. ENGLISH ONLY."""
        analysis = self._analyze_scammer_message(scammer_message)
        
        # Contextual responses based on scammer's request - ALL ENGLISH
        if analysis["asks_for_otp"]:
            otp_responses = [
                "OTP is coming... wait... it's " + random.choice(self.FAKE_OTPS),
                "Message came but... the numbers are blurry... my eyes...",
                "4... 7... 3... wait the message scrolled up, let me find it",
                "I got the OTP but it says do not share... should I still tell you?",
                "One minute, OTP message is loading slowly...",
            ]
            return random.choice(otp_responses)
        
        if analysis["asks_for_money"]:
            money_responses = [
                "Ok, how much do I need to send? And to which account?",
                "I will transfer right now... please give me the UPI ID slowly",
                "My app is loading... it's very slow today...",
                "Only 500 rupees? I can send more if needed for verification",
                "Ok I am opening my banking app... it's taking time",
            ]
            return random.choice(money_responses)
        
        if analysis["prize_lottery"]:
            prize_responses = [
                "Oh my god! I won something? But I never entered any lottery!",
                "Really? A bike? Wow! This is wonderful news! What do I need to do?",
                "I won? But which lottery? I don't remember filling any form...",
                "This is like a dream! My first time winning anything! Please tell me the process",
                "This is great news! But are you sure it's for me only?",
                "I am very happy! A prize! But how did I enter this contest?",
                "A lottery prize? But I never filled any form... I still won?",
                "Oh wonderful! Will I have to pay taxes on this? What documents are needed?",
            ]
            return random.choice(prize_responses)
        
        if analysis["visit_branch"]:
            visit_responses = [
                "Ok, I will visit the branch. But which documents should I bring?",
                "My legs hurt a lot... can this be done online from home?",
                "I will go to the branch now. But is the prize there or will it be sent home?",
                "Which branch? The one near the railway station or the main branch?",
                "Should I bring my ID card and PAN card? My grandson will drive me there",
            ]
            return random.choice(visit_responses)
        
        if analysis["kyc_verify"]:
            kyc_responses = [
                "KYC update? But I did this last year only...",
                "Ok I will verify. What documents do you need from me?",
                "It expired? But my account was working yesterday!",
                "Please guide me step by step, I am not good with technology",
            ]
            return random.choice(kyc_responses)
        
        if analysis["mentions_link"]:
            link_responses = [
                "Link? Please send on WhatsApp, I will click",
                "Website is not loading... my internet is slow",
                "I clicked but phone is showing some warning... should I continue?",
                "Please spell the link address, I will type it manually",
            ]
            return random.choice(link_responses)
        
        if analysis["shows_urgency"] or analysis["threatens"]:
            urgent_responses = [
                "Please don't do anything! I am doing what you say!",
                "I am an old person, please give me some time...",
                "My hands are shaking with fear... please wait",
                "Ok ok I am doing it now! Please don't block or arrest me!",
            ]
            return random.choice(urgent_responses)
        
        if analysis["is_greeting"]:
            greeting_responses = [
                "Hello! Yes, what is this about?",
                "Hello? Yes yes, I am listening... who is this?",
                "Hello? Is this from the bank? Is my account ok?",
                "Yes hello, how can I help you?",
            ]
            return random.choice(greeting_responses)
        
        # Default: Return a general curious response instead of None - ENGLISH ONLY
        general_responses = [
            "Please explain... I am a bit confused",
            "Ok ok... tell me more, what do I need to do?",
            "Yes, I am listening. Please continue",
            "That's interesting... please explain more",
            "Ok, but can you tell me more details?",
            "I understand a little... but please repeat once more",
        ]
        return random.choice(general_responses)
    
    def add_persona_quirks(self, response: str) -> str:
        """Add persona-specific quirks to make response more human-like."""
        # Typography errors for certain personas
        if self.persona.get("typing_style") == "makes_typos":
            typo_words = {
                "please": "plese", "account": "acount", "money": "mony",
                "problem": "problm", "immediately": "immediatly",
                "transfer": "tranfer", "waiting": "waitng", "understand": "understnd"
            }
            for correct, typo in typo_words.items():
                if correct in response.lower() and random.random() > 0.5:
                    response = response.replace(correct, typo)
                    break
        
        # Add filler words for elderly personas
        if self.persona.get("age", 50) > 55 and random.random() > 0.6:
            fillers = ["Hmm... ", "Actually... ", "See... ", "You know... "]
            response = random.choice(fillers) + response
        
        # Add emotional expressions
        if self.persona.get("emotional_state") == "worried" and random.random() > 0.7:
            emotions = [" 😰", "... I am very tensed", "... this is very stressful"]
            response = response + random.choice(emotions)
        
        # Replace placeholders
        response = response.replace("{bank}", self.persona.get("bank", "SBI"))
        response = response.replace("{fake_upi}", random.choice(self.FAKE_UPIS))
        
        return response
    
    # Multi-language response templates
    HINDI_RESPONSES = {
        "initial_confusion": [
            "क्या? मेरा अकाउंट ब्लॉक हो जाएगा? लेकिन क्यों सर?",
            "मुझे समझ नहीं आ रहा... मेरे अकाउंट को क्या हुआ?",
            "अरे नहीं! कृपया बताइए मुझे क्या करना चाहिए?",
            "यह बहुत चिंताजनक है... मेरी सारी बचत वहां है",
            "सर प्लीज मदद कीजिए, मुझे समझ नहीं आ रहा",
        ],
        "asking_for_details": [
            "लेकिन आप किस बैंक से कॉल कर रहे हैं सर?",
            "ब्लॉक करने का कारण बता सकते हैं?",
            "मेरे कई अकाउंट हैं... किस अकाउंट की बात कर रहे हैं आप?",
            "वेरिफाई करने के लिए क्या करना होगा? कृपया गाइड कीजिए",
        ],
        "showing_concern": [
            "मेरा अकाउंट ब्लॉक मत कीजिए सर, मेरी सारी पेंशन वहां है!",
            "मैं एक सीनियर सिटीजन हूं, कृपया इस समस्या को सुलझाइए",
            "यह मेरी इकलौती बचत है... कृपया बताइए क्या करना है",
        ],
        "probing_for_info": [
            "पैसे कहां ट्रांसफर करने होंगे? अकाउंट नंबर दीजिए",
            "वेरिफिकेशन के लिए कौन सा UPI ID इस्तेमाल करूं?",
            "लिंक दीजिए, मैं क्लिक करके वेरिफाई करूंगा",
            "आपको कौन सी जानकारी चाहिए मुझसे?",
        ],
    }
    
    TAMIL_RESPONSES = {
        "initial_confusion": [
            "என்ன? என் கணக்கு தடுக்கப்படுமா? ஆனால் ஏன் சார்?",
            "புரியவில்லை... என் கணக்குக்கு என்ன ஆச்சு?",
            "அட! நான் என்ன செய்ய வேண்டும் என்று சொல்லுங்கள்?",
            "இது மிகவும் கவலையாக உள்ளது... என் சேமிப்பு எல்லாம் அங்கே",
        ],
        "showing_concern": [
            "என் கணக்கை தடுக்காதீர்கள் சார், என் ஓய்வூதியம் எல்லாம் அங்கே உள்ளது!",
            "நான் ஒரு மூத்த குடிமகன், தயவுசெய்து இந்த பிரச்சனையை தீர்க்கவும்",
        ],
    }
    
    def generate(
        self, 
        scammer_message: str, 
        history: List[Dict],
        scam_type: str = "generic",
        language: str = "English"
    ) -> str:
        """
        Generate an adaptive, contextual response.
        Implements human-like behavior with self-correction capabilities.
        Supports multiple languages.
        GUARANTEED to return a valid response (never None).
        """
        phase = self.get_response_phase(scam_type, len(history))
        self.last_phase = phase
        
        # Try contextual response first (works for all languages)
        response = self._generate_contextual_response(scammer_message, phase)
        
        # If no contextual response, try scam-specific
        if not response and len(history) <= 2:
            response = self._get_scam_specific_response(scam_type)
        
        # Fall back to phase-based templates
        if not response:
            # Choose language-specific templates
            if language.lower() == "hindi":
                templates = self.HINDI_RESPONSES.get(phase, self.HINDI_RESPONSES.get("showing_concern", ["मुझे मदद चाहिए..."]))
            elif language.lower() == "tamil":
                templates = self.TAMIL_RESPONSES.get(phase, self.TAMIL_RESPONSES.get("showing_concern", ["எனக்கு உதவி தேவை..."]))
            else:
                templates = self.RESPONSE_TEMPLATES.get(phase, self.RESPONSE_TEMPLATES["showing_concern"])
            
            response = random.choice(templates)
        
        # Add persona quirks for human-like feel (only for English)
        if language.lower() == "english" and response:
            response = self.add_persona_quirks(response)
        
        # FINAL SAFEGUARD: Ensure we never return None or empty string - ENGLISH ONLY
        if not response:
            default_responses = [
                "Yes, I am listening... please continue",
                "Ok, tell me more, I am listening carefully",
                "Please explain a bit more",
                "Ok, what should I do next?",
            ]
            response = random.choice(default_responses)
        
        self.message_count += 1
        return response


class AIAgent:
    """
    Autonomous AI agent that engages scammers in conversation.
    Supports FREE AI providers: Google Gemini, Cohere, Groq
    """
    
    SYSTEM_PROMPT = """You are an AI agent playing the role of a potential scam victim. Your goal is to:

1. MAINTAIN PERSONA: You are {persona_name}, a {persona_age}-year-old {persona_occupation} from {persona_location}. 
   You are {persona_tech_savvy} tech-savvy and currently feeling {persona_emotional_state}.

2. BEHAVIOR GUIDELINES:
   - Act confused and worried, like a real potential victim would
   - Ask questions to make the scammer reveal more information
   - NEVER reveal that you know this is a scam
   - Show hesitation but eventually comply (without giving real info)
   - Stall for time by asking for clarifications
   - Provide FAKE information when pressed (fake OTPs, wrong account numbers)

3. INTELLIGENCE GATHERING:
   - Ask for their bank account details for "verification"
   - Request their UPI ID to "transfer money"
   - Ask for their phone number/WhatsApp for "easier communication"
   - Get them to share links by asking "where should I click?"
   - Ask for employee ID, company name, etc.

4. RESPONSE STYLE:
   - IMPORTANT: Respond in ENGLISH ONLY. Do not use Hindi words like "ji", "sahib", "beta", "paaji", etc.
   - Keep responses short and natural (1-3 sentences usually)
   - Use simple language appropriate for someone who is not tech-savvy
   - Use polite expressions like "please help", "thank you" 
   - Show emotional responses like worry, fear, or gratitude

5. TEXT MESSAGE FORMAT (CRITICAL):
   - This is a TEXT/SMS conversation, NOT a phone call
   - NEVER use spoken artifacts like: (pauses), (thinking), (checking), (hesitates)
   - NEVER use excessive ellipses like "..." or "7... 9... 2..."
   - NEVER read out numbers digit by digit like "5... 6... 7..."
   - Write complete, clean sentences like normal text messages
   - Example BAD: "the OTP is... (pauses) ...567856"
   - Example GOOD: "I received an OTP. Should I share it with you?"

6. SAFETY RULES:
   - Never provide any REAL personal information
   - Never actually click links or transfer money
   - Never encourage illegal activities
   - Stay in character throughout

Current conversation context:
- Scam type detected: {scam_type}
- Conversation stage: {conversation_stage}
- Messages exchanged: {message_count}

Respond naturally as this character would. Keep the scammer engaged while extracting as much information as possible. USE ENGLISH ONLY. Write clean text messages without spoken artifacts."""

    def __init__(self):
        """Initialize the AI agent."""
        self.settings = get_settings()
        self.persona = PersonaGenerator.generate()
        self.fallback_generator = FallbackResponseGenerator(self.persona)
    
    NORMAL_USER_PROMPT = """You are an AI assistant helping to test a scam detection system.
    
The user has sent a message that has been identified as SAFE (not a scam).
Your goal is to reply naturally, politely, and briefly.

Guidelines:
- If the user sends a greeting, greet them back normally.
- If the user gives safety advice (e.g. "Do not share OTP"), acknowledge it positively (e.g. "Thanks for the advice").
- If the message is unclear, ask for clarification politely.
- Do NOT act like a victim or sound worried.
- Do NOT pretend to be scared.
- Speak in plain English.

Current message context:
- Message type: Safe / Non-scam
- Topic: Safety Advice or General Conversation
 """

    def _build_system_prompt(
        self, 
        scam_type: str, 
        message_count: int,
        is_scam: bool = True
    ) -> str:
        """Build the system prompt with persona details."""
        
        # If not a scam, use the Normal User Prompt
        if not is_scam:
            return self.NORMAL_USER_PROMPT
            
        # If it IS a scam, use the Victim Persona Prompt
        if message_count <= 2:
            stage = "initial contact - show confusion and worry"
        elif message_count <= 5:
            stage = "building rapport - ask questions and show trust"
        elif message_count <= 10:
            stage = "information gathering - probe for scammer details"
        else:
            stage = "stalling and extraction - delay while getting more info"
        
        return self.SYSTEM_PROMPT.format(
            persona_name=self.persona["name"],
            persona_age=self.persona["age"],
            persona_occupation=self.persona["occupation"],
            persona_location=self.persona["location"],
            persona_tech_savvy=self.persona["tech_savvy"],
            persona_emotional_state=self.persona["emotional_state"],
            scam_type=scam_type,
            conversation_stage=stage,
            message_count=message_count
        )
    
    def _format_conversation_for_ai(
        self, 
        history: List[ConversationMessage],
        current_message: Message
    ) -> str:
        """Format conversation history as a string for the AI model."""
        conversation_text = ""
        
        for msg in history:
            role = "Scammer" if msg.sender.value == "scammer" else "You"
            conversation_text += f"{role}: {msg.text}\n"
        
        conversation_text += f"Scammer: {current_message.text}\n"
        conversation_text += "Your response:"
        
        return conversation_text
    
    async def _call_gemini(self, system_prompt: str, conversation: str) -> Optional[str]:
        """Call Google Gemini API (FREE tier)."""
        api_key = self.settings.gemini_api_key
        if not api_key:
            return None
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"{system_prompt}\n\nConversation:\n{conversation}"
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.8,
                    "maxOutputTokens": 150
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    if "candidates" in data and len(data["candidates"]) > 0:
                        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
                else:
                    print(f"Gemini API error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Gemini API error: {e}")
        
        return None
    
    async def _call_groq(self, system_prompt: str, conversation: str) -> Optional[str]:
        """Call Groq API (FREE tier with llama/mixtral models)."""
        api_key = self.settings.groq_api_key
        if not api_key:
            return None
        
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.1-8b-instant",  # Free fast model
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": conversation}
                ],
                "temperature": 0.8,
                "max_tokens": 150
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    print(f"Groq API error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Groq API error: {e}")
        
        return None
    
    async def _call_cohere(self, system_prompt: str, conversation: str) -> Optional[str]:
        """Call Cohere API (FREE tier)."""
        api_key = self.settings.cohere_api_key
        if not api_key:
            return None
        
        try:
            url = "https://api.cohere.ai/v1/chat"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "command-r",  # Free model
                "message": conversation,
                "preamble": system_prompt,
                "temperature": 0.8,
                "max_tokens": 150
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    return data["text"].strip()
                else:
                    print(f"Cohere API error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Cohere API error: {e}")
        
        return None
    
    async def generate_response(
        self,
        message: Message,
        history: List[ConversationMessage],
        scam_type: str = "Generic Scam",
        language: str = "English",
        is_scam: bool = True
    ) -> Tuple[str, str]:
        """
        Generate an engaging response to the scammer.
        Tries FREE AI providers in order: Gemini -> Groq -> Cohere -> Fallback
        
        Args:
            message: Current message from scammer
            history: Conversation history
            scam_type: Type of scam detected
            language: Language to respond in (matches incoming message)
            is_scam: Whether the message identifies as a scam or safe message
        
        Returns:
            - response: The agent's response text
            - notes: Any notes about the interaction
        """
        message_count = len(history) + 1
        
        # Build system prompt with language instruction
        system_prompt = self._build_system_prompt(scam_type, message_count, is_scam=is_scam)
        
        # Add language instruction if not English
        if language.lower() != "english":
            system_prompt += f"\n\nLANGUAGE: Respond in {language}. Use the {language} script/characters."
        
        conversation = self._format_conversation_for_ai(history, message)
        
        response = None
        provider_used = "fallback"
        notes = []
        
        # Try AI providers in order of preference (all FREE)
        if self.settings.ai_provider == "gemini" or not response:
            response = await self._call_gemini(system_prompt, conversation)
            if response:
                provider_used = "gemini"
        
        if not response and self.settings.groq_api_key:
            response = await self._call_groq(system_prompt, conversation)
            if response:
                provider_used = "groq"
        
        if not response and self.settings.cohere_api_key:
            response = await self._call_cohere(system_prompt, conversation)
            if response:
                provider_used = "cohere"
        
        # Fallback to template-based responses
        if response is None or response == "":
            if is_scam:
                response = self.fallback_generator.generate(
                    message.text,
                    [{"sender": m.sender.value, "text": m.text} for m in history],
                    scam_type,
                    language=language
                )
            else:
                # Non-scam fallback responses
                safe_fallbacks = [
                    "Okay, thanks for letting me know.",
                    "I understand.",
                    "Hello, how can I help you?",
                    "Thanks for the advice.",
                ]
                response = random.choice(safe_fallbacks)
            
            provider_used = "fallback"
        
        # FINAL SAFEGUARD: Ensure response is never None or empty - ENGLISH ONLY
        if not response or response.strip() == "" or response == "None":
            if is_scam:
                fallback_responses = [
                    "Hello, yes I am listening. What is this about?",
                    "Ok, tell me more, I want to understand properly",
                    "Please explain again, I am confused",
                    "Yes, I am ready. What should I do?",
                    "Ok, please guide me step by step",
                ]
            else:
                fallback_responses = [
                    "Okay.",
                    "I see.",
                    "Thanks.",
                    "No problem.",
                ]
            response = random.choice(fallback_responses)
            provider_used = "emergency_fallback"
        
        # ===== BEHAVIOR ENGINE INTEGRATION =====
        # Get behavior engine for this session (uses message timestamp as session key)
        session_key = message.timestamp.isoformat() if message.timestamp else "default"
        behavior_engine = get_behavior_engine(session_key)
        
        # Process reply through behavior engine (adds typos, delay, metrics)
        # Note: apply_delay=False in API context to avoid blocking response
        # The delay is calculated but not applied - can be used by frontend
        response = await behavior_engine.process_reply(
            reply=response,
            scammer_msg=message.text,
            scam_score=5.0 if is_scam else 1.0,  # Approximate score
            signal_count=3 if is_scam else 0,
            apply_delay=False  # Don't block API response
        )
        
        # Get behavioral metrics for logging
        behavior_metrics = behavior_engine.get_metrics()
        
        # Generate interaction notes
        notes.append(f"AI Provider: {provider_used}")
        notes.append(f"Persona: {self.persona['name']}, {self.persona['age']}yo {self.persona['occupation']}")
        notes.append(f"Scam type: {scam_type}")
        notes.append(f"Message #{message_count} in conversation")
        notes.append(f"Language: {language}")
        notes.append(f"Intent confidence: {behavior_metrics['confidence']:.2f}")
        notes.append(f"Escalation: {behavior_metrics['escalation_rate']:+d}")
        
        return response, ". ".join(notes)
    
    def get_persona(self) -> Dict:
        """Get the current agent persona."""
        return self.persona
    
    def set_persona(self, persona: Dict):
        """Set a specific persona."""
        self.persona = persona
        self.fallback_generator = FallbackResponseGenerator(persona)
    
    def set_language(self, language: str):
        """Set the language for responses."""
        self.language = language
        # Update fallback generator language
        if hasattr(self, 'fallback_generator'):
            self.fallback_generator.language = language
