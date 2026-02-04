import re
import math
import numpy as np
from typing import Tuple, List, Dict, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class ScamDetector:
    """
    Production-grade advanced scam detection engine.
    Implements a 5-layer hybrid system combining structural, linguistic,
    contextual, semantic, and behavioral signals.
    """
    
    # --- CONSTANTS & WEIGHTS ---
    
    # Layer 1: Structural Weights
    WEIGHTS_STRUCTURAL = {
        "url": 2.5,
        "upi": 3.0,
        "bank": 3.0,
        "otp_pattern": 4.0,
        "phone": 1.5,
    }
    
    # Layer 2: Weak Linguistic Signals
    WEIGHT_LINGUISTIC = 0.5
    MAX_LINGUISTIC_SCORE = 2.0
    
    # Layer 3: Contextual Rules
    WEIGHT_CONTEXT_RULE = 3.0
    
    # Layer 4: Semantic Similarity
    WEIGHT_SEMANTIC = 3.0
    SEMANTIC_THRESHOLD = 0.6
    
    # Layer 5: History
    WEIGHT_HISTORY_MESSAGE = 1.0
    WEIGHT_HISTORY_REPEATED = 2.0
    WEIGHT_HISTORY_LINKS = 2.0
    
    # Thresholds
    THRESHOLD_SCAM = 6.0
    THRESHOLD_SUSPICIOUS = 4.0
    
    # --- TEMPLATES ---
    
    SEMANTIC_TEMPLATES = [
        "your account will be blocked",
        "your bank account is suspended",
        "send otp to verify",
        "share otp for verification",
        "claim your prize reward now",
        "you have won a lottery",
        "update kyc immediately",
        "click this link to verify",
        "payment failed pay now",
        "electricity bill unpaid warning",
        "income tax refund pending",
    ]
    
    # --- REGEX PATTERNS ---
    
    REGEX_PATTERNS = {
        "url": r"(https?://\S+|www\.\S+)",
        "upi": r"[\w\.\-_]+@[\w]+",
        "bank": r"\b\d{9,18}\b",  # Account numbers
        "otp_pattern": r"\b\d{4,6}\b",  # 4-6 digit codes (potential OTPs)
        "phone": r"(\+91[\-\s]?)?[6-9]\d{9}",
        "otp_keyword": r"\b(otp|code|pin|password)\b",
    }
    
    # Safety checks (Negative weights)
    SAFETY_PATTERNS = [
        r"never share.*otp",
        r"do not share.*otp",
        r"don'?t share.*otp",
        r"never give.*otp",
        r"do not click.*link",
        r"bank.*never asks",
        r"officials.*never ask",
        r"stay safe",
        r"be careful",
        r"not a scam",
    ]

    def __init__(self):
        """Initialize the detector and fit vectorizers."""
        self.vectorizer = TfidfVectorizer(stop_words='english')
        # Fit vectorizer on templates once at init
        self.template_vectors = self.vectorizer.fit_transform(self.SEMANTIC_TEMPLATES)
        
    def detect(self, text: str, history: List[str]) -> Tuple[bool, float, Dict]:
        """
        Main detection entry point.
        
        Args:
            text: The current message text
            history: List of previous message strings
            
        Returns:
            Tuple containing:
            - is_scam: Boolean decision
            - risk_score: Float score (0-10)
            - debug_info: Dictionary with signal breakdown
        """
        text_lower = text.lower()
        
        # Initialize scores & signals
        scores = {
            "structural": 0.0,
            "linguistic": 0.0,
            "contextual": 0.0,
            "semantic": 0.0,
            "history": 0.0,
            "safety": 0.0
        }
        triggered_signals = []
        
        # --- Pre-check: Safety Advice (Negative Score) ---
        is_safety_advice = any(re.search(p, text_lower) for p in self.SAFETY_PATTERNS)
        if is_safety_advice:
            scores["safety"] = -10.0
            triggered_signals.append("safety_advice_detected")
            # If explicit safety advice, we can short-circuit or just let the score tank
            # Returning early to be safe and efficient
            return False, 0.0, {
                "total": 0.0,
                "signals": triggered_signals, 
                "analysis": "Message identified as safety advice."
            }

        # --- Layer 1: Structural Signals ---
        scores["structural"], signals = self._structural_score(text, text_lower)
        triggered_signals.extend(signals)
        
        # --- Layer 2: Weak Linguistic Signals ---
        scores["linguistic"], signals = self._keyword_score(text_lower)
        triggered_signals.extend(signals)
        
        # --- Layer 3: Contextual Intent Rules ---
        scores["contextual"], signals = self._context_score(text_lower)
        triggered_signals.extend(signals)
        
        # --- Layer 4: Semantic Similarity ---
        scores["semantic"], signals = self._semantic_score(text_lower)
        triggered_signals.extend(signals)
        
        # --- Layer 5: Conversation History ---
        scores["history"], signals = self._history_score(history)
        triggered_signals.extend(signals)
        
        # --- Final Scoring ---
        total_score = sum(scores.values())
        
        # Clamp score 0-10
        total_score = max(0.0, min(10.0, total_score))
        
        # Decision Logic
        is_scam = total_score >= self.THRESHOLD_SCAM
        
        debug_info = {
            "components": scores,
            "total": round(total_score, 2),
            "signals": triggered_signals,
            "is_scam": is_scam,
            "analysis": f"Risk Score: {total_score:.1f}/10 - {'SCAM DETECTED' if is_scam else 'Normal'}"
        }
        
        return is_scam, total_score, debug_info

    def _structural_score(self, text: str, text_lower: str) -> Tuple[float, List[str]]:
        """Layer 1: Detect high-risk structural regex patterns."""
        score = 0.0
        signals = []
        
        # Check URLs
        if re.search(self.REGEX_PATTERNS["url"], text):
            score += self.WEIGHTS_STRUCTURAL["url"]
            signals.append("structural:url_detected")
            
        # Check UPI
        if re.search(self.REGEX_PATTERNS["upi"], text):
            score += self.WEIGHTS_STRUCTURAL["upi"]
            signals.append("structural:upi_detected")
            
        # Check Bank Account (long digits)
        if re.search(self.REGEX_PATTERNS["bank"], text):
            # Verify context isn't just a phone number
            if not re.search(self.REGEX_PATTERNS["phone"], text):
                score += self.WEIGHTS_STRUCTURAL["bank"]
                signals.append("structural:bank_account_detected")
                
        # Check OTP (digits) AND keyword "otp"/"code"
        has_otp_digits = re.search(self.REGEX_PATTERNS["otp_pattern"], text)
        has_otp_word = re.search(self.REGEX_PATTERNS["otp_keyword"], text_lower)
        
        if has_otp_word:
             # Just the word is risky
             pass # Handled in contextual mainly, but let's add minor risk
             
        if has_otp_word or (has_otp_digits and "otp" in text_lower):
            score += self.WEIGHTS_STRUCTURAL["otp_pattern"]
            signals.append("structural:otp_request_detected")
            
        return score, signals

    def _keyword_score(self, text_lower: str) -> Tuple[float, List[str]]:
        """Layer 2: Weak linguistic urgency/pressure signals."""
        urgency_words = [
            "urgent", "immediately", "now", "verify", "blocked", 
            "suspended", "prize", "reward", "offer", "limited", 
            "expire", "lapse", "kyc"
        ]
        
        score = 0.0
        hits = 0
        signals = []
        
        for word in urgency_words:
            if word in text_lower:
                score += self.WEIGHT_LINGUISTIC
                hits += 1
                if hits <= 3: # Only list first few
                    signals.append(f"linguistic:{word}")

        # Cap the score
        score = min(score, self.MAX_LINGUISTIC_SCORE)
        
        return score, signals

    def _context_score(self, text_lower: str) -> Tuple[float, List[str]]:
        """Layer 3: Contextual Intent Rules (Combination Logic)."""
        score = 0.0
        signals = []
        
        # Rule Set: (term1, term2) - if BOTH present, it's suspicious
        rules = [
            ("verify", "link"),
            ("send", "money"),
            ("send", "payment"),
            ("share", "otp"),
            ("give", "otp"),
            ("tell", "otp"),
            ("update", "bank"),
            ("click", "link"),
            ("confirm", "account"),
            ("verify", "kyc"),
            ("block", "account"),
            # UPI-specific rules (ADDED)
            ("share", "upi"),
            ("give", "upi"),
            ("send", "upi"),
            ("verify", "upi"),
            ("share", "id"),
            ("verification", "upi"),
            ("verification", "account"),
            ("verification", "otp"),
            # Money transfer rules
            ("transfer", "account"),
            ("transfer", "money"),
            ("pay", "now"),
            ("send", "amount"),
        ]
        
        for t1, t2 in rules:
            if t1 in text_lower and t2 in text_lower:
                score += self.WEIGHT_CONTEXT_RULE
                signals.append(f"context_rule:{t1}+{t2}")
                
        return score, signals

    def _semantic_score(self, text_lower: str) -> Tuple[float, List[str]]:
        """Layer 4: Semantic Similarity using TF-IDF & Cosine Similarity."""
        if not text_lower.strip():
            return 0.0, []
            
        try:
            # Vectorize input
            input_vector = self.vectorizer.transform([text_lower])
            
            # Compute cosine similarity against all templates
            similarities = cosine_similarity(input_vector, self.template_vectors).flatten()
            
            # Get max similarity
            max_sim = np.max(similarities)
            best_idx = np.argmax(similarities)
            
            if max_sim > self.SEMANTIC_THRESHOLD:
                signals = [f"semantic:match({max_sim:.2f})_'{self.SEMANTIC_TEMPLATES[best_idx]}'"]
                return self.WEIGHT_SEMANTIC, signals
                
        except Exception as e:
            # Fallback if sklearn error (rare)
            return 0.0, [f"semantic_error:{str(e)}"]
            
        return 0.0, []
        
    def _history_score(self, history: List[str]) -> Tuple[float, List[str]]:
        """Layer 5: Conversation History Risk Boost."""
        score = 0.0
        signals = []
        
        if not history:
            return 0.0, []
        
        message_count = len(history)
        
        # Heuristic 1: Suspicious words in previous turns
        suspicious_words_hist = ["details", "bank", "otp", "link", "money"]
        suspicious_count = 0
        for msg in history:
            if any(w in msg.lower() for w in suspicious_words_hist):
                suspicious_count += 1
        
        if suspicious_count > 0:
            boost = min(3.0, suspicious_count * self.WEIGHT_HISTORY_MESSAGE)
            score += boost
            signals.append(f"history:suspicious_context_x{suspicious_count}")
            
        # Heuristic 2: Length/Persistence (Naive check for now)
        if message_count > 3:
            score += 0.5
            signals.append("history:persistence")
            
        return score, signals

    def get_scam_type(self, text: str, keywords: List[str] = None) -> str:
        """Determine the likely type of scam based on text and keywords."""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["won", "winner", "prize", "lottery", "lucky"]):
            return "Prize/Lottery Scam"
        if any(w in text_lower for w in ["kyc", "pan", "aadhar", "update", "expire"]):
            return "KYC/Bank Update Scam"
        if any(w in text_lower for w in ["otp", "code", "pin", "password"]):
            return "OTP/Phishing Scam"
        if any(w in text_lower for w in ["job", "hiring", "work from home", "salary"]):
            return "Job/Employment Scam"
        if any(w in text_lower for w in ["loan", "interest", "approve"]):
            return "Loan Scam"
        if any(w in text_lower for w in ["electricity", "bill", "power", "cut"]):
            return "Electricity/Bill Scam"
        if any(w in text_lower for w in ["customs", "parcel", "delivery", "courier"]):
            return "Courier/Customs Scam"
        if any(w in text_lower for w in ["urgent", "police", "arrest", "legal"]):
            return "Intimidation/Legal Scam"
            
        return "Generic Scam"
