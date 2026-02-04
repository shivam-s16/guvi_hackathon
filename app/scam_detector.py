"""
Scam Detection Engine.
Analyzes messages to detect fraudulent intent using pattern matching and AI.
"""

import re
from typing import Tuple, List, Dict
from app.models import Message, ConversationMessage


class ScamDetector:
    """
    Multi-layered scam detection engine.
    Uses pattern matching, keyword analysis, and behavioral indicators.
    """
    
    # High-risk keywords indicating scam intent
    SCAM_KEYWORDS = {
        # Urgency indicators
        "urgent": 2.0,
        "immediately": 2.0,
        "today": 1.5,
        "now": 1.5,
        "asap": 1.8,
        "hurry": 1.5,
        "deadline": 1.5,
        "expire": 1.8,
        "last chance": 2.0,
        
        # Threat indicators
        "blocked": 2.5,
        "suspended": 2.5,
        "deactivated": 2.0,
        "freeze": 2.0,
        "frozen": 2.0,
        "terminated": 2.0,
        "closed": 1.5,
        "legal action": 2.5,
        "police": 2.0,
        "arrest": 2.5,
        "court": 2.0,
        "lawsuit": 2.0,
        
        # Financial keywords
        "bank account": 2.0,
        "upi": 2.5,
        "otp": 3.0,
        "pin": 2.5,
        "cvv": 3.0,
        "credit card": 2.0,
        "debit card": 2.0,
        "transfer": 1.5,
        "payment": 1.5,
        "refund": 2.0,
        "cashback": 1.8,
        
        # Verification requests
        "verify": 2.0,
        "confirm": 1.5,
        "authenticate": 1.8,
        "validate": 1.5,
        "update details": 2.0,
        "kyc": 2.5,
        
        # Prize/lottery scams
        "won": 2.5,
        "winner": 2.5,
        "lottery": 3.0,
        "prize": 2.5,
        "reward": 2.0,
        "congratulations": 2.0,
        "congratulation": 2.0,
        "selected": 1.8,
        "lucky": 2.0,
        "bike": 2.0,
        "car": 2.0,
        "gift": 1.8,
        "claim": 2.0,
        "free": 1.5,
        "lakh": 2.0,
        "crore": 2.0,
        "jackpot": 3.0,
        
        # Impersonation
        "rbi": 2.0,
        "income tax": 2.0,
        "government": 1.8,
        "bank manager": 2.5,
        "customer care": 2.0,
        "support team": 1.5,
        
        # Action requests
        "click here": 2.0,
        "click link": 2.5,
        "download": 1.5,
        "install": 1.5,
        "share": 1.5,
        "send": 1.0,
    }
    
    # Scam message patterns (regex)
    SCAM_PATTERNS = [
        # Bank/UPI scams
        r"(your|ur)\s*(bank\s*)?(account|a/c)\s*(will\s*be|is)\s*(blocked|suspended|frozen)",
        r"(verify|update|confirm)\s*(your|ur)?\s*(bank|upi|account|kyc)",
        r"share\s*(your|ur)?\s*(otp|pin|cvv|password)",
        r"(upi|bank)\s*id\s*(required|needed|share)",
        
        # Prize/lottery scams
        r"(you|u)\s*(have\s*)?(won|selected|chosen)\s*(a|the)?\s*(prize|lottery|reward)",
        r"(claim|collect)\s*(your|ur)?\s*(prize|reward|money|cashback)",
        
        # Threat-based scams
        r"(legal|police)\s*action\s*(will\s*be)?\s*taken",
        r"(arrest|jail)\s*(warrant|order)",
        r"(income\s*tax|it)\s*(notice|raid|investigation)",
        
        # Urgency patterns
        r"(within|in)\s*\d+\s*(hours?|minutes?|mins?)",
        r"(last|final)\s*(warning|notice|chance)",
        
        # Link patterns
        r"https?://[^\s]+\.(xyz|tk|ml|ga|cf|top|click|link)",
        r"bit\.ly|tinyurl|short\.io",
        
        # WhatsApp/phone number requests
        r"(call|contact|whatsapp)\s*(this|at)?\s*\+?\d{10,}",
    ]
    
    def __init__(self, confidence_threshold: float = 0.4):
        """Initialize the scam detector with a lower threshold for better detection."""
        self.confidence_threshold = confidence_threshold
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.SCAM_PATTERNS
        ]
    
    def calculate_keyword_score(self, text: str) -> Tuple[float, List[str]]:
        """
        Calculate scam score based on keyword analysis.
        Returns score and list of matched keywords.
        """
        text_lower = text.lower()
        total_score = 0.0
        matched_keywords = []
        
        for keyword, weight in self.SCAM_KEYWORDS.items():
            if keyword in text_lower:
                total_score += weight
                matched_keywords.append(keyword)
        
        # Normalize score (0-1 range) - adjusted divisor for better sensitivity
        normalized_score = min(total_score / 6.0, 1.0)
        return normalized_score, matched_keywords
    
    def check_patterns(self, text: str) -> Tuple[float, int]:
        """
        Check message against scam patterns.
        Returns pattern score and number of matches.
        """
        match_count = 0
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                match_count += 1
        
        # Each pattern match adds 0.25 to score (increased from 0.15)
        pattern_score = min(match_count * 0.25, 1.0)
        return pattern_score, match_count
    
    def analyze_conversation_context(
        self, 
        history: List[ConversationMessage]
    ) -> float:
        """
        Analyze conversation history for escalating scam behavior.
        Returns context-based score adjustment.
        """
        if not history:
            return 0.0
        
        context_score = 0.0
        
        # Check for repeated threats or urgency
        threat_count = 0
        request_count = 0
        
        for msg in history:
            if msg.sender.value == "scammer":
                text_lower = msg.text.lower()
                
                # Count escalating threats
                if any(word in text_lower for word in ["blocked", "suspended", "legal", "police"]):
                    threat_count += 1
                
                # Count information requests
                if any(word in text_lower for word in ["share", "send", "provide", "give"]):
                    request_count += 1
        
        # Repeated threats indicate scam
        if threat_count >= 2:
            context_score += 0.2
        
        # Multiple requests for information
        if request_count >= 2:
            context_score += 0.15
        
        return min(context_score, 0.3)
    
    def detect(
        self, 
        message: Message, 
        history: List[ConversationMessage] = None
    ) -> Tuple[bool, float, List[str], str]:
        """
        Main detection method.
        
        Returns:
            - is_scam: Boolean indicating scam detection
            - confidence: Confidence score (0-1)
            - keywords: List of matched suspicious keywords
            - analysis: Brief analysis summary
        """
        text = message.text
        text_lower = text.lower()
        history = history or []
        
        # 1. INTELLIGENT CONTEXT CHECK: Safety Advice vs Scam
        # Using regex to ensure we match whole phrases and intent
        
        # Patterns that strictly indicate safety advice/warnings
        safety_patterns = [
            r"never share.*otp",
            r"do not share.*otp",
            r"don'?t share.*otp",
            r"never give.*otp",
            r"never tell.*otp",
            r"be careful.*fraud",
            r"beware of.*scam",
            r"stay safe",
            r"do not click.*unknown",
            r"never click.*link",
            r"don'?t click.*link",
            r"bank.*never asks",
            r"officials.*never ask",
            r"for security reasons",
            r"keep your.*safe",
            r"avoid.*scam",
            r"do not entertain",
            r"don'?t entertain",
            r"do not accept",
            r"don'?t accept",
            r"ignore.*ask",
            r"avoid.*share",
            r"refuse.*share",
        ]
        
        is_safety_advice = any(re.search(p, text_lower) for p in safety_patterns)
        
        # Patterns that indicate a request (SCAM intent)
        asking_patterns = [
            r"share.*otp",
            r"give.*otp",
            r"send.*otp",
            r"tell.*otp",
            r"provide.*otp",
            r"verify.*account",
            r"update.*kyc",
            r"click.*link",
            r"fill.*form",
        ]
        
        # Check if they are asking for something specific (but exclude "never share" context)
        is_asking = any(re.search(p, text_lower) for p in asking_patterns)
        
        # Crucial check: If they say "Never share OTP", they technically trigger "share OTP" regex.
        # So if is_safety_advice is True, we overrule is_asking.
        if is_safety_advice:
            is_asking = False
        
        # 2. Calculate component scores
        keyword_score, matched_keywords = self.calculate_keyword_score(text)
        pattern_score, pattern_matches = self.check_patterns(text)
        context_score = self.analyze_conversation_context(history)
        
        # 3. Intelligent Scoring Logic
        
        if is_safety_advice:
            # If it's safety advice, forced LOW score
            final_score = 0.05
            analysis = "Message identified as safety advice/warning (Not a scam)"
            return False, final_score, [], analysis
        
        # Weighted combination
        final_score = (
            keyword_score * 0.5 +
            pattern_score * 0.35 +
            context_score * 0.15
        )
        
        # Boost if actively asking for suspicious info
        if is_asking:
            final_score += 0.2
            
        # Also check: if we have 3+ suspicious keywords AND asking for info, it's likely a scam
        if len(matched_keywords) >= 3 and is_asking:
            final_score = max(final_score, 0.7)
        
        # Determine if scam
        is_scam = final_score >= self.confidence_threshold
        
        # Generate analysis summary
        analysis_parts = []
        if matched_keywords:
            analysis_parts.append(f"Suspicious keywords detected: {', '.join(matched_keywords[:5])}")
        if pattern_matches > 0:
            analysis_parts.append(f"Matched {pattern_matches} scam pattern(s)")
        if is_asking:
             analysis_parts.append("Message is requesting sensitive actions")
        
        analysis = ". ".join(analysis_parts) if analysis_parts else "No significant scam indicators"
        
        return is_scam, final_score, matched_keywords, analysis
    
    def get_scam_type(self, text: str, keywords: List[str]) -> str:
        """Determine the type of scam based on content."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["bank", "account", "upi", "otp", "kyc"]):
            return "Banking/UPI Fraud"
        elif any(word in text_lower for word in ["won", "prize", "lottery", "reward", "cashback"]):
            return "Prize/Lottery Scam"
        elif any(word in text_lower for word in ["police", "legal", "arrest", "court", "income tax"]):
            return "Threat/Impersonation Scam"
        elif any(word in text_lower for word in ["job", "work from home", "earning", "investment"]):
            return "Job/Investment Scam"
        elif any(word in text_lower for word in ["click", "link", "download"]):
            return "Phishing Scam"
        else:
            return "Generic Scam"
