"""
Natural Conversational Honeypot Agent.
Behaves like a real, sensible adult - NOT a confused bot.
"""

import random
import re
from typing import List, Dict, Optional, Set

class HoneyAgent:
    """
    Natural, human-like conversational agent for scammer engagement.
    
    Persona: Middle-aged adult, polite, slightly anxious, cooperative but cautious.
    Speech: Full sentences, smooth grammar, logical flow.
    """
    
    # Stages
    STAGE_INITIAL = 0
    STAGE_ENGAGED = 1
    STAGE_DETAILS = 2
    STAGE_SENSITIVE = 3
    STAGE_CRITICAL = 4
    
    def __init__(self):
        self._session_data: Dict[str, dict] = {}
        
        # Synonym pools for variation
        self._syn_check = ["check", "look at", "verify", "confirm", "see"]
        self._syn_okay = ["Okay", "Alright", "Sure", "I see", "Right"]
        self._syn_wait = ["Give me a moment", "One second", "Let me check", "Hold on"]
        self._syn_ask = ["tell me", "explain", "let me know", "clarify"]
        
    def _get_session(self, history: List[Dict]) -> dict:
        """Get or create session state."""
        if not history:
            sid = f"s_{random.randint(1000,9999)}"
        else:
            sid = f"{history[0].get('timestamp', 'x')}"[:20]
        
        if sid not in self._session_data:
            self._session_data[sid] = {
                "stage": self.STAGE_INITIAL,
                "turn": 0,
                "last_reply": "",
                "last_question_type": "",
                "used_phrases": set(),
                "stall_count": 0,
                "last_stall_turn": -10,
            }
        return self._session_data[sid]
    
    # =========================================================================
    # INTENT ANALYSIS
    # =========================================================================
    
    def _analyze_intent(self, msg: str) -> Dict[str, bool]:
        """Detect scammer's intent from message."""
        m = msg.lower()
        return {
            "otp": bool(re.search(r"\b(otp|code|pin|password|digit)\b", m)),
            "upi": bool(re.search(r"\b(upi|gpay|phonepe|paytm|@)\b", m)),
            "money": bool(re.search(r"\b(send|transfer|pay|money|amount|rs)\b", m)),
            "account": bool(re.search(r"\b(account|bank|number|ifsc)\b", m)),
            "link": bool(re.search(r"\b(link|click|url|website)\b", m)),
            "urgent": bool(re.search(r"\b(urgent|immediate|now|fast|quick)\b", m)),
            "threat": bool(re.search(r"\b(block|suspend|arrest|police|legal|freeze)\b", m)),
            "greeting": bool(re.search(r"\b(hello|hi|good morning|calling from)\b", m)),
            "confirm": bool(re.search(r"\b(yes|correct|right|confirm)\b", m)),
        }
    
    # =========================================================================
    # REPLY GENERATION
    # =========================================================================
    
    def _build_reply(self, session: dict, intent: Dict, message: str) -> str:
        """Build natural, contextual reply."""
        
        turn = session["turn"]
        stage = session["stage"]
        last_q = session["last_question_type"]
        
        # Decide if we should add mild hesitation (15% chance, not every turn)
        add_hesitation = random.random() < 0.15 and turn > 1
        
        # Decide if we can stall (max once per 4 turns)
        can_stall = (turn - session["last_stall_turn"]) >= 4
        
        reply = ""
        question_type = ""
        
        # === HANDLE DIFFERENT INTENTS ===
        
        if intent["greeting"] and stage == self.STAGE_INITIAL:
            reply = self._greeting_response()
            session["stage"] = self.STAGE_ENGAGED
            question_type = "greeting"
            
        elif intent["threat"]:
            reply = self._threat_response()
            question_type = "threat"
            
        elif intent["otp"]:
            reply = self._otp_response(stage, can_stall, session)
            session["stage"] = max(stage, self.STAGE_CRITICAL)
            question_type = "otp"
            
        elif intent["upi"]:
            reply = self._upi_response(stage, last_q)
            session["stage"] = max(stage, self.STAGE_SENSITIVE)
            question_type = "upi"
            
        elif intent["money"]:
            reply = self._money_response(stage)
            session["stage"] = max(stage, self.STAGE_CRITICAL)
            question_type = "money"
            
        elif intent["account"]:
            reply = self._account_response(stage, last_q)
            session["stage"] = max(stage, self.STAGE_DETAILS)
            question_type = "account"
            
        elif intent["link"]:
            reply = self._link_response()
            question_type = "link"
            
        elif intent["confirm"]:
            reply = self._confirmation_response(last_q)
            question_type = "confirm"
            
        elif intent["urgent"]:
            reply = self._urgency_response()
            question_type = "urgent"
            
        else:
            # Generic engaged response
            reply = self._generic_response(stage)
            question_type = "generic"
        
        # Add mild hesitation occasionally
        if add_hesitation:
            reply = self._add_mild_hesitation(reply)
        
        # Ensure no repetition
        reply = self._ensure_unique(reply, session)
        
        # Update session
        session["last_reply"] = reply
        session["last_question_type"] = question_type
        session["turn"] = turn + 1
        
        return reply
    
    # =========================================================================
    # CONTEXTUAL RESPONSES (Natural, full sentences)
    # =========================================================================
    
    def _greeting_response(self) -> str:
        options = [
            "Hello, yes? Who is this calling?",
            "Yes, hello. May I know what this is regarding?",
            "Hi, I'm listening. What happened to my account?",
            "Hello. Is there a problem with my account?",
        ]
        return random.choice(options)
    
    def _threat_response(self) -> str:
        options = [
            "Please don't say that. I haven't done anything wrong. What do I need to do?",
            "This is very concerning. Please tell me what I should do to fix this.",
            "I'm worried now. Can you explain what exactly is the issue?",
            "I don't understand why this is happening. How can I resolve it?",
        ]
        return random.choice(options)
    
    def _otp_response(self, stage: int, can_stall: bool, session: dict) -> str:
        if stage < self.STAGE_SENSITIVE:
            # Not ready to discuss OTP yet
            options = [
                "I received a message with a code. What exactly do you need me to do with it?",
                "There's a code on my phone. Should I be sharing this?",
                "I got an OTP. But the message says not to share it. Is this safe?",
            ]
        else:
            if can_stall:
                session["last_stall_turn"] = session["turn"]
                options = [
                    "Let me open the message. One moment please.",
                    "Give me a second, I'm checking the SMS.",
                    "Hold on, I need to find the message.",
                ]
            else:
                options = [
                    "I see the code. Are you sure I should share this?",
                    "The message says it's confidential. Do you really need this?",
                    "I have the OTP here. What happens after I give it to you?",
                ]
        return random.choice(options)
    
    def _upi_response(self, stage: int, last_q: str) -> str:
        if last_q == "upi":
            # Already asked about UPI, give partial info
            options = [
                "I think my UPI ID is something like raj.sharma@oksbi. Is that what you need?",
                "Let me check... I use GPay mostly. The ID should be my phone number.",
                "I'm not sure which one. I have it linked to my bank account.",
            ]
        else:
            # First time asking
            options = [
                "Do you mean the UPI ID like name@bank? Which app should I check?",
                "I have GPay and Paytm both. Which UPI ID do you need?",
                "My UPI is linked to my phone number. Is that what you're asking for?",
            ]
        return random.choice(options)
    
    def _money_response(self, stage: int) -> str:
        options = [
            "Send money? How much exactly, and to which account?",
            "I can do the transfer. But please tell me the exact amount and where to send.",
            "Okay, I'll need the account details. Where should I transfer?",
            "Alright, but why do I need to pay? Can you explain first?",
        ]
        return random.choice(options)
    
    def _account_response(self, stage: int, last_q: str) -> str:
        if last_q == "account":
            options = [
                "My account number starts with 3257. Do you need the full number?",
                "I'm looking at my passbook now. Which details specifically?",
                "I can see my account details. What exactly should I tell you?",
            ]
        else:
            options = [
                "Which account are you referring to? I have savings and current both.",
                "Do you need the account number or the IFSC code?",
                "I can check my bank details. Which bank are you asking about?",
            ]
        return random.choice(options)
    
    def _link_response(self) -> str:
        options = [
            "I clicked the link but the page is taking time to load.",
            "The website is asking for my login. Should I enter my details?",
            "I opened the link. What should I do next on this page?",
            "The link opened but it looks different from my usual bank website.",
        ]
        return random.choice(options)
    
    def _confirmation_response(self, last_q: str) -> str:
        options = [
            f"Okay, I understand. What should I do next?",
            "Alright, I'm following your instructions. What now?",
            "Yes, I've done that. What's the next step?",
            "Okay. Please guide me on what to do now.",
        ]
        return random.choice(options)
    
    def _urgency_response(self) -> str:
        options = [
            "I understand it's urgent. Just give me a moment to check.",
            "Okay, I'm trying to do this quickly. What exactly do you need?",
            "I'm doing my best. Please tell me what to do.",
            "Alright, I'm on it. What should I check first?",
        ]
        return random.choice(options)
    
    def _generic_response(self, stage: int) -> str:
        if stage <= self.STAGE_ENGAGED:
            options = [
                "I'm not sure I understand. Could you explain what you need?",
                "Can you please clarify what I should do?",
                "I'm listening. What exactly is the problem?",
            ]
        else:
            options = [
                "Okay, what should I do next?",
                "Alright, please guide me through this.",
                "I'm ready. What's the next step?",
            ]
        return random.choice(options)
    
    # =========================================================================
    # NATURAL VARIATION
    # =========================================================================
    
    def _add_mild_hesitation(self, reply: str) -> str:
        """Add subtle, natural hesitation (not broken speech)."""
        prefixes = [
            "Hmm, ",
            "Well, ",
            "Actually, ",
            "I see. ",
        ]
        return random.choice(prefixes) + reply[0].lower() + reply[1:]
    
    def _ensure_unique(self, reply: str, session: dict) -> str:
        """Ensure reply is not repeated."""
        last = session["last_reply"]
        
        if reply == last:
            # Rephrase using synonyms
            for old, new_list in [
                ("Okay", self._syn_okay),
                ("check", self._syn_check),
            ]:
                if old in reply:
                    reply = reply.replace(old, random.choice(new_list), 1)
                    break
            
            # If still same, add variation
            if reply == last:
                reply = random.choice(self._syn_okay) + ", " + reply[0].lower() + reply[1:]
        
        return reply
    
    # =========================================================================
    # MAIN ENTRY POINT
    # =========================================================================
    
    def generate_reply(
        self,
        history: List[Dict],
        current_message: str,
        known_intel: Dict
    ) -> str:
        """
        Generate natural, human-like reply.
        
        Args:
            history: Previous conversation messages
            current_message: Latest scammer message
            known_intel: Already extracted intelligence
            
        Returns:
            Natural reply string (1-2 sentences, full grammar)
        """
        session = self._get_session(history)
        intent = self._analyze_intent(current_message)
        reply = self._build_reply(session, intent, current_message)
        
        return reply
